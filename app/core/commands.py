from app import db

from app.models.core import BridgeCommand, DeviceCommand, Bridge, Device
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

def add_device_encryption_key(bridge, device):
	# populate pending_claims. @TODO back onto database instead
	claim_codes = ['6xwh-441j-8115-zyrh', 'ps2f-gsjg-8wsq-7hc4']
	pending_claims = {} # hardware_xor: encryption_key
	for c in claim_codes:
		hw, key = process_claim_code(c)
		pending_claims[hw] = key
	
	if not pending_claims.has_key(device.hardware_xor):
		print "Device %r %r" % (device.device_address, device.hardware_xor)
		for hw, key in pending_claims.items():
			print "Pending claim %r %r" % (hw, key)
		raise Exception("No pending claim for device")
	
	payload = {
		'name': 'add_device_encryption_key',
		'params': {
			'device_address': device.device_address,
			'encryption_key': pending_claims[device.hardware_xor]
		}
	}
	
	command = BridgeCommand(
		bridge_address=bridge.bridge_address,
		json_payload=json.dumps(payload),
		timestamp=datetime.utcnow(),
		state=u'ready'
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
        state=u'ready',
        deliver_at=datetime.utcnow()
    )
    db.session.add(command)
    db.session.commit()
    return command