from PIL import Image
import unittest

from sirius.coding import image_encoding


class ImageCase(unittest.TestCase):

    def _test_normal_text(self):
        data = image_encoding.html_to_png('')
        image = Image.open(data)
        self.assertEquals(image.size[0], 384)

    def _test_normal_height(self):
        data = image_encoding.html_to_png(
            '<html><body style="margin: 0px; height: 100px;"></body></html>')
        image = Image.open(data)
        self.assertEquals(image.size[1], 100)

    def _test_rle(self):
        data = image_encoding.html_to_png('')
        image = Image.open(data)
        n_bytes, _ = image_encoding.rle_image(data)
        self.assertEquals(n_bytes, 3072)


class PipeTestCase(unittest.TestCase):

    def test_full(self):
        data = image_encoding.html_to_png('')

        image = Image.open(data)
        image = image_encoding.crop_384(image)
        image = image_encoding.threshold(image)

        n_bytes, _ = image_encoding.rle_from_bw(image)
        self.assertEquals(n_bytes, 3072)

    def test_default_pipeline(self):
        n_bytes, _ = image_encoding.rle_from_bw(
            image_encoding.default_pipeline('')
        )
        self.assertEquals(n_bytes, 3072)
