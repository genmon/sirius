from app import db

from ..models.core import BridgeCommand
from ..models.core import DeviceCommand
from ..image_encoding import rle_image

from .claiming import process_claim_code

import struct
from datetime import datetime
import base64
import json

# device commands are
# set_delivery_and_print
# set_delivery
# set_delivery_and_print_no_face
# set_delivery_no_face
# set_personality
# set_quip
# firmware_update

TEST_FILE_ID = 1
#TEST_PNG_FN = '/Users/matt/Documents/dev-unversioned/sirius2/iconrethink.png'
#TEST_PNG_FN = '/Users/matt/Documents/dev/sirius/tests/iconrethink.png'
TEST_PNG_FN = '/Users/matt/Documents/dev/sirius/tests/riley.png'

# some constants
DEVICE_TYPE = '\x01' # rBergCloud::Barringer::DEVICE_TYPE in weminuche-server
COMMAND_ID = {
    'set_delivery_and_print': 0x0001
}

def add_device_encryption_key():
    bridge_address = "000d6f00026c6edd"
    device_address = "000d6f000273ce0b"
    #claim_code = "6xwh-441j-8115-zyrh"
    claim_code = "ps2f-gsjg-8wsq-7hc4"
    _, encryption_key = process_claim_code(claim_code)
    
    payload = {
        'name': 'add_device_encryption_key',
        'params': {
            'device_address': device_address,
            'encryption_key': encryption_key
        }
    }

    command = BridgeCommand(
        bridge_address='000d6f0001b397c3',
        json_payload=json.dumps(payload),
        timestamp=datetime.utcnow(),
        state='ready'
    )
    
    db.session.add(command)
    db.session.commit()
    
    return command   

def set_delivery_and_print_payload(file_id, png_fn):
    # file ID is a 32 bit ID which is returned as a did_print event
    # three parts:
    # - command header
    #   - >cxHLL
    # - payload header
    #   - length >L
    # - payload
    #   - len(header plus image) + 1 >L
    #   - pad x
    #   - encode_header_region
    #       - pad x
    #       - length of following >L
    #       - append_printer_control_header (a bunch o bytes)
    #       - UC05 controls <cccccccc
    #   - encode_image_region
    
    # device type c, reserved byte c,
    # command_name <H (short), file_id <L (long),
    # unimplemented CRC (long is zero)
    command_header = struct.pack("<BBHII", 1, 0, 1, 123, 0)

    # get the encoded image now, because we'll need the data later
    pixel_count, encoded_image = rle_image(png_fn)

    # payload header region
    printer_control = struct.pack("<13B",
        0x1d, 0x73, 0x03, 0xe8, # max printer speed
        0x1d, 0x61, 0xd0, # printer acceleration
        0x1d, 0x2f, 0x0f, # peak current
        0x1d, 0x44, 0x80  # max intensity
        )
    printer_byte_count = pixel_count / 8
    n3 = printer_byte_count / 65536
    n3_remainder = printer_byte_count % 65536
    n2 = n3_remainder / 256
    n1 = n3_remainder % 256
    printer_data = struct.pack("<8B", 0x1b, 0x2a, n1, n2, n3, 0, 0, 48)
    header_region = struct.pack("<BI", 0, len(printer_control) + len(printer_data))
    header_region += printer_control + printer_data
    
    # payload including the header
    payload = struct.pack("<IB", len(header_region) + len(encoded_image) + 1, 0)
    payload += header_region + encoded_image
    
    entire_payload = command_header + struct.pack("<I", len(payload)) + payload
    
    return entire_payload
    
def set_delivery_and_print(device_address):
    command = DeviceCommand(
        device_address=device_address,
        binary_payload=base64.b64encode(set_delivery_and_print_payload(TEST_FILE_ID, TEST_PNG_FN)),
        state='ready',
        deliver_at=datetime.utcnow()
    )
    db.session.add(command)
    db.session.commit()
    return command