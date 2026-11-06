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


def marks_at(angles):
    """One mark per angle, its first edge pointing that way."""
    out = {}
    for n, angle in enumerate(angles):
        a = np.radians(angle)
        c0 = np.float32([100 * n, 0])
        out[8 * 43 + n] = np.stack([c0, c0 + 10 * np.float32([np.cos(a), np.sin(a)]), c0, c0])
    return out


def test_an_upside_down_page_is_turned_although_its_angles_wrap_round():
    assert quarter_turns(marks_at([174.7, -176.0])) == 2


def jpeg_with_extras():
    """A plain JPEG with an Adobe (APP14) segment after its start and a second image after its end."""
    buffer = io.BytesIO()
    Image.fromarray(np.random.default_rng(2).integers(0, 255, (32, 24, 3), np.uint8)).save(buffer, 'JPEG')
    plain = buffer.getvalue()
    adobe = b'\xff\xee\x00\x0eAdobe\x00\x64\x00\x00\x00\x00\x01'
    return plain[:2] + adobe + plain[2:], plain[:2] + adobe + plain[2:] + b'\xff\xd8\xff\xe1\x00\x08Exif\x00\x00\xff\xd9'


def test_strip_metadata_cuts_what_follows_the_image_and_keeps_adobe():
    image, with_trailer = jpeg_with_extras()
    assert strip_metadata(with_trailer) == image


def test_a_photo_with_an_orientation_tag_comes_out_upright(tmp_path):
    from prepare_photos import main
    page = np.ascontiguousarray(np.rot90(page_with_marks(number=45), 1))  # stored turned left
    exif = Image.Exif()
    exif[0x0112] = 6  # show it turned right: upright
    (tmp_path / 'in').mkdir()
    Image.fromarray(page).convert('RGB').save(tmp_path / 'in' / 'p.jpg', 'JPEG', exif=exif, quality=95)
    main([tmp_path / 'in'], tmp_path)
    out = cv2.imread(str(tmp_path / 'photos' / 'test' / 'T45__p.jpg'), cv2.IMREAD_GRAYSCALE | cv2.IMREAD_IGNORE_ORIENTATION)
    assert quarter_turns(find_marks(out)) == 0


def test_photos_of_new_pages_go_to_train(tmp_path):
    from prepare_photos import main
    (tmp_path / 'in').mkdir()
    cv2.imwrite(str(tmp_path / 'in' / 'p.jpg'), page_with_marks(number=51))
    main([tmp_path / 'in'], tmp_path)
    assert (tmp_path / 'photos' / 'train' / 'T51__p.jpg').exists()
