from app.models.core import BridgeCommand, DeviceCommand, Device, Bridge
from .. import db

from . import commands
from .payload import DeviceEventPayload
from . import claiming

from datetime import datetime
from pprint import pprint

# process_event should...
# - break apart the event
# - handle internally by saving/modifying state to current_app
# - deal with claiming
# - create DeviceEvent models and propagate out if necessary
# all of this is happening within a try:except: in the event loop,
# so don't be afraid to crash out

class PendingClaims(object):
    
    def __init__(self):
        self.encryption_keys = {} # hardware_xor: encryption_key
    
    def add_claim_code(self, claim_code):
        hardware_xor, encryption_key = claiming.process_claim_code(claim_code)
        #@TODO handle exception
        
        self.encryption_keys[hardware_xor] = encryption_key
    
    def key_for_address(self, device_address):
        hardware_xor = claiming.make_hardware_xor(device_address)
        return self.encryption_keys.get(hardware_xor, None)

pending_claims = PendingClaims()


class EventProcessingException(Exception): pass

# @TODO command_sender shouldn't be passed in here, and of course it
# shouldn't be horribly synchronous like it is

def process_event(ws, event, sender):
    print "Received event type %r" % event['type']
    if event['type'] == 'DeviceEvent':
        # unwrap here, even though it breaks abstraction... three event
        # types: heartbeat, did_print, did_power_on
        # see device_event.py in hubcode
        payload = DeviceEventPayload.from_base64(event['binary_payload'])
        timestamp = datetime.fromtimestamp(event['timestamp'])
        print "DeviceEvent: %r at %s" % (payload['name'], timestamp.isoformat())
        if payload['name'] == 'heartbeat':
            if sender.did_send_image is False:
                print "Sending set_delivery_and_print"
                device = Device.query.get(event['device_address'])
                if device is not None:
                    q = sender.for_device(device)
                    if q is not None:
                        dc = commands.set_delivery_and_print(event['device_address'])
                        q.queue_device_command(dc)
                        sender.did_send_image = True
    elif event['type'] == 'BridgeEvent':
        # unwrap here. use device_connect and device_disconnect to
        # change the command delivery map. there is also power_on,
        # encryption_key_required [4 events are all I can find]
        bridge = Bridge.get_or_create(event['bridge_address'])
        event_name = event['json_payload']['name']
        timestamp = datetime.fromtimestamp(event['timestamp'])
        print "BridgeEvent: %r at %s" % (event_name, timestamp.isoformat())
        if event_name == 'device_connect':
            device = Device.get_or_create(event['json_payload']['device_address'])
            sender.device_connect(bridge, device)
        elif event_name == 'device_disconnect':
            device = Device.get_or_create(event['json_payload']['device_address'])
            sender.device_disconnect(bridge, device)
        elif event_name == 'power_on':
            sender.register(ws, bridge)
        elif event_name == 'encryption_key_required':
            print "Sending add_device_encryption_key"
            bc = commands.add_device_encryption_key()
            sender.for_bridge(bridge).queue_bridge_command(bc)
        else:
            raise EventProcessingException("Unknown BridgeEvent command name: %r" % command_name)
        pass
    elif event['type'] == 'BridgeLog':
        pprint(event)
    elif event['type'] == 'BridgeCommandResponse':
        # if the return_code is 0 or not set, set state as delivered
        # else mark it as failed
        # (what happens if there is never any update? is there a timeout?)
        # (30 minute time-out in the command gate)
        r = event['return_code']
        # update the database,
        c = BridgeCommand.query.get(event['command_id'])
        if c is None:
            raise EventProcessingException("BridgeCommandResponse for unknown command_id %r" % event['command_id'])
        c.return_code = r
        if r == 0:
            c.state = 'delivered'
        else:
            c.state = 'failed'
        db.session.add(c)
        db.session.commit()
        # let the command_sender know to remove the command from
        # the queue, or to resend it
        bridge = Bridge.query.get(event['bridge_address'])
        if bridge is not None:
            sender.for_bridge(bridge).handle_bridge_response(c)       
    elif event['type'] == 'DeviceCommandResponse':
        # if the return_code is 0, set state as delivered
        # else mark it as failed
        # (what happens if there is never any update? is there a timeout?)
        r = event['return_code']
        # update the database,
        c = DeviceCommand.query.get(event['command_id'])
        if c is None:
            raise EventProcessingException("DeviceCommandResponse for unknown command_id %r" % event['command_id'])
        c.return_code = r
        if r == 0:
            c.state = 'delivered'
        else:
            c.state = 'failed'
        db.session.add(c)
        db.session.commit()
        # let the command_sender know to remove the command from
        # the queue, or to resend it
        device = Device.query.get(event['device_address'])
        if device is not None:
            sender.for_device(device).handle_device_response(c)   
    else:
        raise EventProcessingException("Unknown event type: %r" % event['type'])
