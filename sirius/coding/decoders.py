"""This module decodes incoming the incoming dictionaries into
"messages". Each message is its own type for easier dispatching.
"""
import base64
import struct

from sirius.protocol import messages
from sirius.coding import bitshuffle


class BERGCloudConst(object):
    BC_EVENT_PRODUCT_ANNOUNCE   = 0xA000
    BC_COMMAND_SET_BERGCLOUD_ID = 0xB000

    BC_COMMAND_START_BINARY     = 0xC000
    BC_COMMAND_START_PACKED     = 0xC100
    BC_COMMAND_ID_MASK          = 0x00FF
    BC_COMMAND_FORMAT_MASK      = 0xFF00

    BC_COMMAND_DISPLAY_IMAGE    = 0xD000
    BC_COMMAND_DISPLAY_TEXT     = 0xD001

    BC_EVENT_START_BINARY       = 0xE000
    BC_EVENT_START_PACKED       = 0xE100
    BC_EVENT_ID_MASK            = 0x00FF
    BC_EVENT_FORMAT_MASK        = 0xFF00

    BC_COMMAND_FIRMWARE_ARDUINO = 0xF010
    BC_COMMAND_FIRMWARE_MBED    = 0xF020


class DeviceEventConst(object):
    EVENT_HEADER_SIZE = 10

    EVENT_HEARTBEAT = 1
    EVENT_DID_PRINT = 2
    EVENT_DID_POWER_ON = 3

    EVENT_HEARTBEAT_SIZE = 4
    EVENT_DID_PRINT_SIZE = 5
    EVENT_DID_POWER_ON_SIZE_LONG = 74  # Using fragmentation
    EVENT_DID_POWER_ON_SIZE_SHORT = 58 # No fragmentation

    RESET_DICT = {
        0x0000: "Undeterminable cause",
        0x0100: "FIB bootloader",
        0x0200: "Ember bootloader",
        0x0300: "External reset",
        0x0400: "Power on",
        0x0500: "Watchdog",
        0x0600: "Software triggered",
        0x0700: "Software crash",
        0x0800: "Flash failure",
        0x0900: "Fatal error",
        0x0a00: "Access fault",
    }


def decode_message(data):
    """Decodes a single incoming message from data.

    :param data: A python dictionary, as decoded from json.
    """
    if data['type'] == 'BridgeEvent':
        return _decode_bridge_event(data)

    elif data['type'] == 'BridgeLog':
        return _decode_bridge_log(data)

    elif data['type'] == 'BridgeCommandResponse':
        return _decode_bridge_command_response(data)

    elif data['type'] == 'DeviceCommandResponse':
        return _decode_device_command_response(data)

    elif data['type'] == 'DeviceEvent':
        return _decode_device_event(data)

    else:
        return messages.UnknownEvent(data)

    assert False, "never reached"


def _decode_bridge_event(data):
    """Decodes a single bridge event from data.

    :param data: A python dictionary, as decoded from json.
    """
    try:
        name = data['json_payload']['name']
        payload = data['json_payload']
    except KeyError as e:
        return messages.MalformedEvent(data, 'Missing field {}'.format(e))

    if name == 'power_on':
        return messages.PowerOn(
            bridge_address=data['bridge_address'],
            model=payload['model'],
            firmware_version=payload['firmware_version'],
            ncp_version=payload['ncp_version'],
            local_ip_address=payload['local_ip_address'],
            mac_address=payload['mac_address'],
            uptime=payload['uptime'],
            uboot_environment=payload['uboot_environment'],
            network_info=payload['network_info'],
        )
    elif name == 'device_connect':
        return messages.DeviceConnect(
            bridge_address=data['bridge_address'],
            device_address=payload['device_address'],
        )
    elif name == 'device_disconnect':
        return messages.DeviceDisconnect(
            bridge_address=data['bridge_address'],
            device_address=payload['device_address'],
        )
    elif name == 'encryption_key_required':
        return messages.EncryptionKeyRequired(
            bridge_address=data['bridge_address'],
            device_address=payload['device_address'],
            hardware_xor=bitshuffle.hardware_xor_from_device_address(
                payload['device_address']),
        )
    else:
        return messages.UnknownEvent(data)

    assert False, "never reached"


def _decode_bridge_log(data):
    """Decodes the bridge log from data.

    :param data: A python dictionary, as decoded from json.
    """
    return messages.BridgeLog(
        bridge_address=data['bridge_address'],
        records=data['records'],
    )


def _decode_device_event(data):
    """Decodes a device event from data.

    :param data: A python dictionary, as decoded from json.
    """
    try:
        payload = data['binary_payload']
        device_address = data['device_address']
        binary = base64.b64decode(payload)
    except KeyError as e:
        return messages.MalformedEvent(data, 'Missing field {}'.format(e))
    except TypeError as e:
        return messages.MalformedEvent(data, 'Invalid base64 {}'.format(e))

    offset = 0
    code, command_id, payload_length = \
        struct.unpack_from("<HII", binary, offset)

    expected_length = DeviceEventConst.EVENT_HEADER_SIZE + payload_length
    if len(binary) != expected_length:
        return messages.MalformedEvent(data, 'Is: {}, should be: {}'.format(
            len(binary), expected_length))

    if code & BERGCloudConst.BC_EVENT_FORMAT_MASK == BERGCloudConst.BC_EVENT_START_BINARY:
        return messages.BergCloudStartBinary(
            device_address=device_address,
            event_id=code & BERGCloudConst.BC_EVENT_ID_MASK,
            data=binary[offset:],
        )

    elif code & BERGCloudConst.BC_EVENT_FORMAT_MASK == BERGCloudConst.BC_EVENT_START_PACKED:
        return messages.BergCloudStartPacked(
            device_address=device_address,
            event_id=code & BERGCloudConst.BC_EVENT_ID_MASK,
            data=binary[offset:],
        )

    elif code == DeviceEventConst.EVENT_DID_POWER_ON:
        if payload_length == DeviceEventConst.EVENT_DID_POWER_ON_SIZE_LONG:
            power_on_fields = struct.unpack_from("<I32s32sIH", binary, offset)

        elif payload_length == DeviceEventConst.EVENT_DID_POWER_ON_SIZE_SHORT:
            power_on_fields = struct.unpack_from("<I24s24sIH", binary, offset)

        else:
            return messages.MalformedEvent(
                data, 'power_on payload wrong size. Is {}. Expected: {}'.format(
                    len(payload_length),
            ))

        deviceType, firmwareBuildVersion, loaderBuildVersion, protocolVersion, resetDescription = power_on_fields

        # High byte of resetDescription is the reset 'base type', low byte gives
        # extended information about the reset cause.
        reset_description = DeviceEventConst.RESET_DICT.get(resetDescription & 0xff00)
        if reset_description is None:
            return messages.MalformedEvent(
                data, 'Invalid reset description. {}'.format(resetDescription))

        return messages.DeviceDidPowerOn(
            device_address=device_address,
            device_type=deviceType,
            firmware_build_version=firmwareBuildVersion,
            loader_build_version=loaderBuildVersion,
            protocol_version=protocolVersion,
            reset_description=resetDescription,
        )

    elif code == BERGCloudConst.BC_EVENT_PRODUCT_ANNOUNCE:
        if payload_length != 20:
            return messages.MalformedEvent(
                data, 'Invalid BC_EVENT_PRODUCT_ANNOUNCE. Is {}. Expected 20.'.format(payload_length))

        id0, id1, id2, id3, version =  struct.unpack_from(">LLLLL", binary, offset)
        return messages.BergCloudProductAnnounce(
            device_address=device_address,
            product_id='%08x%08x%08x%08x' % (id0, id1, id2, id3),
            product_version=version,
        )

    elif code == DeviceEventConst.EVENT_HEARTBEAT:
        if payload_length != DeviceEventConst.EVENT_HEARTBEAT_SIZE:
            return messages.MalformedEvent(
                data, 'Invalid EVENT_HEARTBEAT length. Is: {}. Expected: {}'.format(
                    payload_length, DeviceEventConst.EVENT_HEARTBEAT_SIZE))

        uptime =  struct.unpack_from("<I", binary, offset)
        return messages.DeviceHeartbeat(
            bridge_address=data['bridge_address'],
            device_address=device_address,
            uptime=uptime,
        )

    elif code == DeviceEventConst.EVENT_DID_PRINT:
        if payload_length != DeviceEventConst.EVENT_DID_PRINT_SIZE:
            return messages.MalformedEvent(
                data, 'Invalid EVENT_DID_PRINT length. Is: {}. Expected: {}'.format(
                    payload_length, DeviceEventConst.EVENT_DID_PRINT_SIZE))

        print_type, print_id = struct.unpack_from("<BI", binary, offset)

        # 0x01 => :delivery,
        # 0x10 => :nothing_to_print,
        # 0x11 => :quip,

        return messages.DeviceDidPrint(
            device_address=device_address,
            type=print_type,
            id=print_id,
        )

    else:
        return messages.UnknownEvent(data)

    assert False, "never reached"

def _decode_bridge_command_response(data):
    """Decodes a BridgeCommandResponse.

    :param data: A python dictionary, as decoded from json.
    """
    return messages.BridgeCommandResponse(
        bridge_address=data['bridge_address'],
        command_id=data['command_id'],
        timestamp=data['timestamp'],
        return_code=data['return_code'],
    )

def _decode_device_command_response(data):
    """Decodes a DeviceCommandResponse.

    :param data: A python dictionary, as decoded from json.
    """
    return messages.DeviceCommandResponse(
        bridge_address=data['bridge_address'],
        command_id=data['command_id'],
        timestamp=data['timestamp'],
        return_code=data['return_code'],
    )
