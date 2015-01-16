import unittest

from sirius.coding import image_encoding


class ImageCase(unittest.TestCase):

    def test_normal_text(self):
        image = image_encoding.html_to_png('')
        self.assertEquals(image.size[0], 384)

    def test_normal_height(self):
        image = image_encoding.html_to_png(
            '<html><body style="margin: 0px; height: 100px;"></body></html>')
        self.assertEquals(image.size[1], 100)

    def test_rle(self):
        image = image_encoding.html_to_png('')
        n_bytes, _ = image_encoding.rle_image(image)
        self.assertEquals(n_bytes, 3072)
