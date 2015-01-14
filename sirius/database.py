"""Fake database to be connected to a real database at some point.

"""
import collections


ClaimedDevice = collections.namedtuple('ClaimedDevice', 'address hardware_xor claim_code')
claimed_devices = {
    0x73c164: ClaimedDevice(
        '000d6f000273c164',
        0x73c164,
        'n5ry-p6x6-kth7-7hc4',
    ),
    0xaacafe: ClaimedDevice(
        '000d6f000273ce0b',
        0xaacafe,
        'n5ry-p6x6-kth7-7hc4',
    ),
}

def get_claim_code(hardware_xor):
    return claimed_devices.get(hardware_xor)
