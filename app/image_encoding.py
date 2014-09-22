from PIL import Image
from itertools import groupby
import array
import struct

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
 
def rle_image(image_fn):
    # get image pixels
    im = Image.open(image_fn)
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
    output = struct.pack("<%ds" % len(x), str(x))

    # return (number of pixels, output)
    return len(pixels), output
