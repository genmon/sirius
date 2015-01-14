from .crc16 import crc16
from Crypto.Cipher import AES, XOR

import struct
import base64

ZBEE_SEC_CONST_BLOCKSIZE = 16

CLAIM_CODE_SALT = [ 0x38, 0x96, 0x10, 0xd9,
                    0xb6, 0xb1, 0x0d, 0x16,
                    0x9e, 0xe9, 0xbf, 0x87,
                    0x95, 0x32, 0x62, 0x5b ]

# This dictionary maps base32 digits to five-bit values.
#
# Letter 'A' is omitted and not valid in a claim code.
# Letter 'I' is mapped to number '1' (i.e. claim code is '1', user enters 'I' by mistake).
# Letter 'L' is mapped to number '1' (i.e. claim code is '1', user enters 'L' by mistake).
# Letter 'U' is mapped to letter 'v' (i.e. claim code is 'V', user enters 'U' by mistake).
CLAIMCODE_BASE32_DICT = {
  '0': 0x00,
  '1': 0x01,
  '2': 0x02,
  '3': 0x03,
  '4': 0x04,
  '5': 0x05,
  '6': 0x06,
  '7': 0x07,
  '8': 0x08,
  '9': 0x09,
# 'A': omitted
  'B': 0x0A,
  'C': 0x0B,
  'D': 0x0C,
  'E': 0x0D,
  'F': 0x0E,
  'G': 0x0F,
  'H': 0x10,
  'I': 0x01,   # mapped to '1'
  'J': 0x11,
  'K': 0x12,
  'L': 0x01,   # mapped to '1'
  'M': 0x13,
  'N': 0x14,
  'O': 0x15,
  'P': 0x16,
  'Q': 0x17,
  'R': 0x18,
  'S': 0x19,
  'T': 0x1A,
  'U': 0x1B,   # mapped to 'V'
  'V': 0x1B,
  'W': 0x1C,
  'X': 0x1D,
  'Y': 0x1E,
  'Z': 0x1F
}

CC_ENCODE_LIST = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                  'j', 'k', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z']

class InvalidClaimCode(Exception):
    pass

def unpack_claim_code(claim_code):
    clean = claim_code.replace("-", "").upper()

    if len(clean) != 16:
        raise InvalidClaimCode("claim codes should be 16 characters")

    value = 0

    for i, c in enumerate(clean):
        if c in CLAIMCODE_BASE32_DICT.keys():
            value += CLAIMCODE_BASE32_DICT[c] * (32 ** (15 - i))
        else:
            raise InvalidClaimCode("%s is not a valid character" % c)

    device = value & 0xffffff             # 24 bit hardware address xor
    secret = (value >> 24) & 0xffffffffff # 40 bit secret
    crc = value >> 64                     # 16 bit crc

    # Return the components, and the raw 80 bit value
    return (device, secret, crc, value)

# This method is inspired by dissectors/packet-zbee-security.c from Wireshark
# input should be a binary string of 5 bytes in length
def generate_link_key(input):
    input_length = len(input) + len(CLAIM_CODE_SALT)

    if len(input) <= 5:
        # Padding begins with 1000000
        # Then pad with zeroes until we're at 14 bytes
        input = input + b'\x80' + b'\x00' * (ZBEE_SEC_CONST_BLOCKSIZE - 2 - len(input) - 1)

        # Pad with the original length encoded as a 16bit int
        # Python3
        #input = input + bytes( [((input_length * 8) >> 8 & 0xff)] )
        #input = input + bytes( [((input_length * 8) >> 0 & 0xff)] )
        # Python2
        input = input + chr((input_length * 8) >> 8 & 0xff)
        input = input + chr((input_length * 8) >> 0 & 0xff)

    elif input_length != ZBEE_SEC_CONST_BLOCKSIZE:
        raise InvalidClaimCode("cannot handle input size %d" % input_length)

    # We encrypt the salt and the input bytes
    # blocks = [bytes(CLAIM_CODE_SALT), input] # Python3
    blocks = [str(bytearray(CLAIM_CODE_SALT)), input] # Python2

    #output = bytes(16) # Works in Python3
    output = bytearray(16) # Works in Python2

    for block in blocks:
        # aes_encoder = AES.new(output, AES.MODE_ECB) # Python3
        aes_encoder = AES.new(str(output), AES.MODE_ECB) # Python2
        h = aes_encoder.encrypt(block)
        output = bytearray(16)
        for i in range(len(output)):
            # output[i] = h[i] ^ block[i] # Python3
            output[i] = ord(h[i]) ^ ord(block[i]) # Python2
        output = bytes(output)

    return output


# Codes go through the following process:
#
# 1. Cleaning
# 2. Convert from 5-bit to 8-bit (16 chars down to 10 chars)
# 3. Checksum is checked
# 4. XOR EUI64 + Base64 security hash + CRC are returned
#
# Return the link key in Base64, and the XORed hardware_address
def process_claim_code(claim_code):
    hardware_xor, secret, crc, raw_value = unpack_claim_code(claim_code)

    # Generate our own CRC from the raw_value, and confirm it matches the extracted crc
    data_for_crc = struct.pack("<Q", raw_value & 0xffffffffffffffff)
    #server_crc = crc16(data_for_crc) # this works in Python3
    server_crc = crc16( bytearray(data_for_crc) ) # this works in Python2

    if server_crc != crc:
        raise InvalidClaimCode("CRC problem")

    # Pack the 40-bit number as a LE long long, and then truncate back to 5 bytes
    packed_secret = struct.pack("<Q", secret)[0:5]
    link_key = generate_link_key(packed_secret)
    link_key_b64 = base64.encodestring(link_key)

    return (hardware_xor, link_key_b64)


def key_from_claim_code(claim_code):
    _, key = process_claim_code(claim_code)
    return key


def encode(device, secret):
    device = device & 0xffffff
    secret = secret & 0xffffffffff

    value = device | (secret << 24)
    data = bytearray(struct.pack("<Q", value))
    crc = crc16(data, 0xffff)
    cc = value | (crc << 64)

    text = ''

    i = 16
    while i> 0:
        text = CC_ENCODE_LIST[cc & 0x1f] + text
        cc = cc >> 5
        if (i==5) or (i==9) or (i==13):
            text = '-' + text
        i -= 1

    return text
