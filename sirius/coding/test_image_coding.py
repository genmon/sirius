from PIL import Image
import unittest
import io

from sirius.coding import image_encoding


class ImageCase(unittest.TestCase):

    def test_normal_text(self):
        data = image_encoding.html_to_png('')
        image = Image.open(io.BytesIO(data))
        self.assertEquals(image.size[0], 384)

    def test_normal_height(self):
        data = image_encoding.html_to_png(
            '<html><body style="margin: 0px; height: 100px;"></body></html>')
        image = Image.open(io.BytesIO(data))
        self.assertEquals(image.size[1], 100)

    def test_rle(self):
        data = image_encoding.html_to_png('')
        image = Image.open(io.BytesIO(data))
        n_bytes, _ = image_encoding.rle_image(data)
        self.assertEquals(n_bytes, 3072)
