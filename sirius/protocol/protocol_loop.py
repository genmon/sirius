"""This file contains the core logic (state machine) for a
websocket-connected bridge.

The official API is two functions:

accept(websocket)
send_message(device_address, message)
"""
import messages
import json
import logging
import time
import gevent

from sirius.coding import encoders
from sirius.coding import decoders
from sirius import stats

from sirius.models import user
from sirius.models import hardware
from sirius.models import messages as model_messages

logger = logging.getLogger(__name__)


# Global ephemeral state. If we move to more than one process then
# either 1) this state needs to move to a central server or 2) we need
# a pubsub message distribution for send_message so the correct
# process can reply.
bridge_by_address = dict()


class BridgeState(object):
    "Ephemeral state of a bridge. Lives as long as the websocket."

    def __init__(self, websocket, address):
        # key -> command_id, value -> unix timestamp sent
        self.address = address
        self.websocket = websocket
        self.pending_commands = dict()
        self.connected_devices = set()
        self.last_seen_timestamp = dict()

    def mark_alive(self, device_address):
        self.connected_devices.add(device_address)
        self.last_seen_timestamp[device_address] = time.time()

    def mark_dead(self, device_address):
        self.connected_devices.discard(device_address)
        self.last_seen_timestamp.pop(device_address, None)

    def mark_dead_by_timeout(self):
        now = time.time()
        for device_address, ts in self.last_seen_timestamp.items():
            if now - ts > 60:
                logger.debug('Marking as dead: %s', device_address)
                self.mark_dead(device_address)


def _get_next_command_id(local_data={}):
    """Return the next usable command id. Initialized lazily from the
    database.

    :returns: An int that can be used as the next command id.
    """
    # Lazy-initialize global next_command_id
    if 'next_command_id' not in local_data:
        # NB 0 is an invalid command id (AKA file-id) so we start at
        # whatever the latest message id is to avoid collisions.
        next_command_id = model_messages.Message.get_next_command_id()
        logger.info("Initialized next_command_id as %s", next_command_id)
        local_data['next_command_id'] = next_command_id
    local_data['next_command_id'] += 1
    return local_data['next_command_id']


def send_message(device_address, message):
    """Sends a single message to a connected device.

    :param device_address: The hex-address of the device.
    :param message: A message from sirius.protocol.messages.

    :returns: 2-tuple of (success, command id used - even if the sending failed)
    """
    command_id = _get_next_command_id()

    # Search for bridge.
    for bridge_state in bridge_by_address.values():
        if device_address in bridge_state.connected_devices:
            break
    else:
        return (False, command_id)

    # Send data through the websocket.
    command = encoders.encode_bridge_command(
        bridge_state.address,
        message,
        command_id,
        '0',
    )
    bridge_state.websocket.send(json.dumps(command))

    # Remember the command we just sent and increment the command id.
    # TODO - implement timeout logic.
    bridge_state.pending_commands[command_id] = message

    return (True, command_id)


def accept(ws):
    """Receiving loop for a single websocket. We're storing the websocket
    in a BridgeState class keyed on the bridge address. This is
    necessary to later find connected devices in `send_message`.

    :param ws: A gevent websocket object.
    """
    loop = _decoder_loop(ws)
    power_on = loop.next()

    # stats & logging
    stats.inc('accepted.count')
    stats.inc('by_type.{}.count'.format(type(power_on).__name__))
    logger.info("New connection from %r.", power_on)

    # Note that there is a potential race condition. If the bridge
    # responds to command_id 0 over a restart we may receive that
    # response just after we have sent out a command with id 0, but
    # it's the wrong response from an earlier command.
    bridge_state = BridgeState(websocket=ws, address=power_on.bridge_address)
    bridge_by_address[power_on.bridge_address] = bridge_state

    try:
        for message in loop:
            # stats & logging
            stats.inc('received.count')
            stats.inc('by_type.{}.count'.format(type(message).__name__))
            logger.debug("Received %r.", message)

            _accept_step(message, bridge_state)

        # If the iterator closes normally then the client closed the
        # socket and we clean up normally.
        stats.inc('client_closed.count')

    except:
        stats.inc('protocol_loop_exception.count')
        logger.exception("Unexpected bridge error.")
        raise

    finally:
        logger.debug("Bridge disonnected: %r.", bridge_state)
        del bridge_by_address[power_on.bridge_address]


def _decoder_loop(ws):
    """We run one decoder loop for every connected web socket. The first
    message is always PowerOn which contains a bridge_address.

    :param ws: A gevent websocket object.
    """
    while True:
        raw_data = ws.receive()
        if raw_data is None:
            break  # websocket closed by client

        try:
            data = json.loads(raw_data)
        except ValueError:
            stats.inc('json_decode_error.count')
            yield messages.MalformedEvent(raw_data, 'Could not decode json.')

        yield decoders.decode_message(data)


def _accept_step(x, bridge_state):
    """Handle a single decoded message. This is in its own function to
    simplify testing and to keep the if/elif indentation low.

    :param x: A type from sirius.protocol.message
    :param bridge_state: The BridgeState for this connection
    """
    if type(x) == messages.DeviceConnect:
        hardware.Printer.phone_home(x.device_address)
        bridge_state.mark_alive(x.device_address)

    elif type(x) == messages.DeviceDisconnect:
        bridge_state.mark_dead(x.device_address)

    elif type(x) == messages.BridgeLog:
        pass  # TODO - write log to a place

    elif type(x) == messages.EncryptionKeyRequired:
        hardware.Printer.phone_home(x.device_address)
        bridge_state.mark_alive(x.device_address)

        claim_code = hardware.Printer.get_claim_code(x.device_address)
        if claim_code is None:
            # It's OK to have an unclaimed device, we just ignore it
            # for now.
            stats.inc('unclaimed.encryption_key_required.count')
            return

        add_key = messages.AddDeviceEncryptionKey(
            bridge_address=x.bridge_address,
            device_address=x.device_address,
            claim_code=claim_code,
        )

        send_message(x.device_address, add_key)

    elif type(x) == messages.DeviceHeartbeat:
        hardware.Printer.phone_home(x.device_address)
        bridge_state.mark_alive(x.device_address)

    elif type(x) == messages.PowerOn:
        logging.info('Received superfluous PowerOn message. '
                     'Probably backlog from previous socket error.')

    elif type(x) == messages.DeviceDidPowerOn:
        # We don't really care about this one other than for debugging
        # maybe.
        bridge_state.mark_alive(x.device_address)

    elif type(x) == messages.DeviceDidPrint:
        # TODO - This message is sent for two reasons:
        # 1) The user pressed the button and nothing was in the queue
        #    "hello, I don't have anything to print [...]"
        # 2) We printed a queued job.
        # In case 2 we want to ack the print in the database.
        pass

    elif type(x) == messages.BridgeCommandResponse:
        if x.command_id not in bridge_state.pending_commands:
            logger.error('Unexpected response (command_id not known) %r', x)
            return

        logger.debug('Got BridgeCommandResponse, ignoring.')

    elif type(x) == messages.DeviceCommandResponse:
        if x.command_id not in bridge_state.pending_commands:
            logger.error('Unexpected response (command_id not known) %r', x)
            return

        logger.debug('Ack-ing message with print_id %s', x.command_id)
        model_messages.Message.ack(x.return_code, x.command_id)
    else:
        assert False, "Unexpected message {}".format(x)


def mark_dead_loop():
    """Loop forever and mark devices that haven't been online for 60
    seconds as dead.

    There is a disconnect message but that's unreliable: If the bridge
    disconnects without a clean TCP shutdown (almost always the case)
    then the websocket won't close and we will never receive any
    disconnect message. Timing out is really the only reliable way to
    do this.
    """
    while True:
        try:
            for bridge in bridge_by_address.values():
                bridge.mark_dead_by_timeout()

            gevent.sleep(5)

        except Exception:
            logger.exception('Unexpected exception in mark_offline_loop. Ignoring.')
            gevent.sleep(5)
