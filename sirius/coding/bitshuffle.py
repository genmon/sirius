"""This module contains encoder/decoder functions that are needed but
don't fit neatly into any category.
"""

def hardware_xor_from_device_address(device_address):
    """The "hardware xor" is a 3-byte representation of the device_address.

    :param device_address: A str containing the hex-encoded device address.
    """
    b = bytearray.fromhex(device_address)

    # little endian
    b.reverse()

    claim_address = bytearray(3)
    claim_address[0] = b[0] ^ b[5]
    claim_address[1] = b[1] ^ b[3] ^ b[6]
    claim_address[2] = b[2] ^ b[4] ^ b[7]

    result = claim_address[2] << 16 | claim_address[1] << 8 | claim_address[0]

    return result
