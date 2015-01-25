import unittest

from sirius.coding import claiming


CC_TEST_VECTORS = [
    ("64z0-0000-0000-0000", 0x000000, 0x0000000000),
    ("kzgz-zzzz-zzzz-zzzz", 0xffffff, 0xffffffffff),
    ("c1zp-g2ec-sqqh-28t5", 0x012345, 0x6789abcdef),
    ("d2y7-dv9z-4rz9-7bk3", 0x93aa43, 0x766d3f263e),
]


class CodingCase(unittest.TestCase):

    def test_decoding(self):
        claim_code = '6xwh-441j-8115-zyrh'
        expected_encryption_key = b'F7D9bmztHV32+WJScGZR0g==\n'
        _, calculated_encryption_key = claiming.process_claim_code(claim_code)

        self.assertEqual(expected_encryption_key, calculated_encryption_key)

    def test_encoding(self):
        for cc, device, secret in CC_TEST_VECTORS:
            self.assertEqual(claiming.encode(device, secret), cc)
            dec_device, dec_secret, _, _ = claiming.unpack_claim_code(cc)
            self.assertEqual(dec_device, device)
            self.assertEqual(dec_secret, secret)

    def test_coding_from_real_world(self):
        device_address = '000d6f000273c164'
        # only the last 24 bits of the device address are used
        device_address_int = int(device_address, 16) & 0xffffff
        # secret only known to printer and claim code
        secret = 0xeb1ba696a0

        self.assertEqual(
            claiming.encode(device_address_int, secret),
            'n5ry-p6x6-kth7-7hc4',
        )
