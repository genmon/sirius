"""Encoders for various commands. All encoders return python
dictionaries that can be encoded directly as json.
"""
import struct
import base64

from sirius.coding import image_encoding
from sirius.coding import claiming
from sirius.protocol import messages

__all__ = [
    'encode_bridge_command',
]


def _encode_pixels(pixel_count, rle_image):
    """
    :param pixel_count: total number of pixels
    :param rle_image: Run-length encoded black and white image.
    :returns: The binary payload
    """
    printer_control = struct.pack("<13B",
        0x1d, 0x73, 0x03, 0xe8, # max printer speed
        0x1d, 0x61, 0xd0, # printer acceleration
        0x1d, 0x2f, 0x0f, # peak current
        0x1d, 0x44, 0x80, # max intensity
    )
    printer_byte_count = pixel_count // 8
    n3, n3_remainder = divmod(printer_byte_count, 65536)
    n2, n1 = divmod(n3_remainder, 256)
    printer_data = struct.pack("<8B", 0x1b, 0x2a, n1, n2, n3, 0, 0, 48)
    header_region = struct.pack("<BI", 0, len(printer_control) + len(printer_data))
    header_region += printer_control + printer_data

    # payload including the header
    payload = struct.pack("<IB", len(header_region) + len(rle_image) + 1, 0)
    payload += header_region + rle_image

    return payload


def _encode_printer_message(command, payload, print_id):
    """
    :param command: See LittlePrinterCommand in protocol.proto.
    :param pixel_count: total number of pixels
    :param rle_image: Run-length encoded black and white image.
    :print_id: unique 32-bit number for ack-ing the print (sent back in didprint event)
    :returns: The binary payload
    """
    LITTLE_PRINTER_DEVICE_ID = 1

    # device type c, reserved byte c,
    # command_name <H (short), file_id <L (long),
    # unimplemented CRC (long is zero)
    command_header = struct.pack(
        "<BBHII",
        LITTLE_PRINTER_DEVICE_ID, 0,
        command,
        print_id, 0,
    )
    entire_payload = command_header + struct.pack("<I", len(payload)) + payload

    return entire_payload


def _payload_from_pixels(pixels):
    """
    :returns: binary payload to be embedded in full message.
    """
    pixel_count, rle_pixels = image_encoding.rle_from_bw(pixels)
    return _encode_pixels(pixel_count, rle_pixels)


def encode_bridge_command(bridge_address, command, command_id, timestamp):
    """Encodes a BridgeCommand into a dict that can be serialized as json.

    :param bridge_address: The hex bridge address.
    :param command: A command from messages.py
    :param command_id: A unique id that is used to ack the command.
    :param timestamp: unix timestamp. Unclear why this is necessary.
    """
    def make(extra):
        base = {
            'type': 'BridgeCommand',
            'bridge_address': bridge_address,
            'command_id': command_id,
            # Apparently in ISO format?
            'timestamp': timestamp,
        }
        base.update(extra)
        return base

    if type(command) == messages.AddDeviceEncryptionKey:
        return make({
            'json_payload': {
                'name': 'add_device_encryption_key',
                'params': {
                    'device_address': command.device_address,
                    'encryption_key': claiming.key_from_claim_code(command.claim_code),
                },
            },
        })

    elif type(command) == messages.SetDeliveryAndPrint:
        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x1, _payload_from_pixels(command.pixels), command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetDelivery:
        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x2, _payload_from_pixels(command.pixels), command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetDeliveryAndPrintNoFace:
        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x11, _payload_from_pixels(command.pixels), command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetDeliveryNoFace:
        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x12, _payload_from_pixels(command.pixels), command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetPersonality:
        payload = (
            _payload_from_pixels(command.face_pixels)
            + _payload_from_pixels(command.nothing_to_print_pixels)
            + _payload_from_pixels(command.cannot_see_bridge_pixels)
            + _payload_from_pixels(command.cannot_see_internet_pixels))

        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x0102, payload, command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetPersonalityWithMessage:
        payload = (
            _payload_from_pixels(command.face_pixels)
            + _payload_from_pixels(command.nothing_to_print_pixels)
            + _payload_from_pixels(command.cannot_see_bridge_pixels)
            + _payload_from_pixels(command.cannot_see_internet_pixels)
            + _payload_from_pixels(command.message_pixels))

        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x0101, payload, command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    elif type(command) == messages.SetQuip:
        payload = (
            _payload_from_pixels(command.quip_pixels_1)
            + _payload_from_pixels(command.quip_pixels_2)
            + _payload_from_pixels(command.quip_pixels_3))

        return make({
            'binary_payload': base64.b64encode(_encode_printer_message(
                0x202, payload, command_id)),
            'device_address': command.device_address,
            'type': 'DeviceCommand',
        })

    assert False, "unknown command type: {}".format(command)
