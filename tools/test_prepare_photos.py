import io

import cv2
import numpy as np
import pytest
from PIL import Image

from prepare_photos import ARUCO, find_marks, page_number, quarter_turns, strip_metadata


def page_with_marks(number, size=(1000, 700), mark=80):
    """A white page with the eight marks of template `number` at its corners and edge middles."""
    h, w = size
    page = np.full((h, w), 255, np.uint8)
    spots = [(20, 20), (w // 2 - mark // 2, 20), (w - 20 - mark, 20), (w - 20 - mark, h // 2 - mark // 2),
             (w - 20 - mark, h - 20 - mark), (w // 2 - mark // 2, h - 20 - mark), (20, h - 20 - mark),
             (20, h // 2 - mark // 2)]
    for spot, (x, y) in enumerate(spots):
        page[y:y + mark, x:x + mark] = cv2.aruco.generateImageMarker(ARUCO, 8 * number + spot, mark)
    return page


def jpeg_with_gps():
    exif = Image.Exif()
    exif[0x010F] = 'HONOR'
    gps = exif.get_ifd(0x8825)
    gps[1] = 'N'
    gps[2] = (45.0, 30.0, 0.0)
    buffer = io.BytesIO()
    Image.fromarray(np.random.default_rng(0).integers(0, 255, (64, 48, 3), np.uint8)).save(buffer, 'JPEG', exif=exif)
    return buffer.getvalue()


def test_strip_metadata_drops_gps_and_keeps_the_image():
    original = jpeg_with_gps()
    assert Image.open(io.BytesIO(original)).getexif().get_ifd(0x8825)  # the test photo really carries a position
    out = strip_metadata(original)
    assert dict(Image.open(io.BytesIO(out)).getexif()) == {}
    assert np.array_equal(np.array(Image.open(io.BytesIO(out))), np.array(Image.open(io.BytesIO(original))))


def test_page_number_is_the_most_common_page():
    assert page_number([8 * 43 + i for i in range(5)] + [8 * 12]) == 43
    assert page_number([]) is None


@pytest.mark.parametrize('k', [0, 1, 2, 3])
def test_quarter_turns_bring_a_turned_page_back(k):
    page = page_with_marks(number=43)
    turned = np.rot90(page, k)
    assert np.array_equal(np.rot90(turned, quarter_turns(find_marks(turned))), page)
