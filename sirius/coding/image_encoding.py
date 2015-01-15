from PIL import Image
from itertools import groupby
import struct
import io
import time
import tempfile

WHITE = 0
BLACK = 1
THRESHOLD = 127
TRANSLATE = [ (1536, 255), (1152, 254), (768, 253), (384, 252), (251, 251) ]

def pixel_to_bw(p):
    if p == (0, 0, 0, 0):
        return WHITE
    elif p[0] > THRESHOLD or p[1] > THRESHOLD or p[2] > THRESHOLD:
        return WHITE
    else:
        return BLACK

def ilen(i): return sum(1 for _ in i)

# so what we have is a list of runs, alternating white and black,
# starting with white.
# the scheme for our little printer RLE is:
# - runs of 0..251 inclusive are stored as a byte
# - if larger, pull off chunks of 1536, 1152, 768, 384, 251 (encoded as
# 255, 254, 253, 252, 251) until small enough
# when a large number is broken into chunks, each chunk needs
# to be suffixed by a zero so it snaps back to swap it back to the
# correct colour
def rle(lengths):
    for length in lengths:
        if length == 0:
            yield length
        elif length <= 251:
            yield length
        elif length > 251:
            remainder = length
            done_first = False
            while remainder > 251:
                chunk, code = [t for t in TRANSLATE if remainder >= t[0]][0]
                remainder -= chunk
                if done_first:
                    yield 0
                else:
                    done_first = True
                yield code
            else:
                if remainder > 0:
                    yield 0
                    yield remainder


def rle_image(im):
    """
    :param im: A python PIL image.
    :returns: A 2-tuple of (number of pixels, RLE-encoded pixel data)
    """
    im = im.convert('RGBA')
    pixels = im.getdata()

    # convert to B&W and group each run length into lists
    # each list is (result of identity function, [actual pixels])
    grouped = groupby(pixels, pixel_to_bw)

    # create list of tuples (WHITE|BLACK, run_length)
    groups = []
    for k, g in grouped:
        groups.append( (k, ilen(g)) )

    # the decoder assumes that the first run is white, so if the
    # first pixel is black, add a zero run of white
    if groups[k][0] == BLACK:
        groups.insert(0, (WHITE, 0))

    # encode using our custom encoding
    lengths = [g[1] for g in groups]
    x = bytearray(rle(lengths))
    compressed_data = struct.pack("<%dB" % len(x), *x)

    # package up with length as header
    # first byte is compressed type, always 1
    output = struct.pack("<BL", 0x01, len(compressed_data)) + compressed_data

    # return (number of pixels, output)
    return len(pixels), output


def html_to_png(html):
	""" This works:
	<html><body style="width: 384px; margin: 0;">
	<img src="https://dl.dropboxusercontent.com/u/165957/Escher.gif">
	</body></html>
	"""
	from selenium import webdriver
        try:
            driver = webdriver.PhantomJS('phantomjs')
            driver.set_window_size(384, 5)

            # note that the .html suffix is required to make phantomjs
            # pick up the mime-type and render correctly.
            with tempfile.NamedTemporaryFile(suffix='.html') as f:
                f.write(html)
                f.flush()
                driver.get('file://' + f.name)
                p = driver.get_screenshot_as_png()

            return Image.open(io.BytesIO(p))
        finally:
            driver.quit()
