"""Sorts phone photos of the printed template pages into photos/train and photos/test, ready to publish.

The marks on each photo say which page it shows (page k carries ids 8k..8k+7). Pages T01-T22 are left out: they
carry the music of homr's own photo test set. T23-T42 go to photos/train, T43-T50 to photos/test (test only, never
train on them). All metadata is dropped (phones store the position, the phone and the time); an upright photo keeps
its image data byte for byte, a turned one is turned upright and saved again at JPEG quality 95.

Run: python tools/prepare_photos.py <photo folder>... [--out <dataset folder>]
"""
import argparse
import collections
import statistics
import struct
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ARUCO = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000)
DETECTOR = cv2.aruco.ArucoDetector(ARUCO)
FIRST_PAGE, FIRST_TEST_PAGE, LAST_PAGE = 23, 43, 50
SEARCH_SIZE = 2000  # long side the marks are searched at


def strip_metadata(jpeg):
    """The JPEG without its APP1-APP15 and COM segments (EXIF, XMP, maker notes, comments); the rest byte for byte."""
    if jpeg[:2] != b'\xff\xd8':
        raise ValueError('not a JPEG')
    out, i = [jpeg[:2]], 2
    while i < len(jpeg):
        if jpeg[i] != 0xFF:
            raise ValueError(f'broken JPEG at byte {i}')
        marker = jpeg[i + 1]
        if marker == 0xDA:  # start of scan: the image data follows to the end
            out.append(jpeg[i:])
            break
        length = struct.unpack('>H', jpeg[i + 2:i + 4])[0]
        if not (0xE1 <= marker <= 0xEF or marker == 0xFE):
            out.append(jpeg[i:i + 2 + length])
        i += 2 + length
    return b''.join(out)


def find_marks(image):
    """{mark id: its 4 corners}, as cv2.aruco gives them (top left, top right, bottom right, bottom left)."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners, ids, _ = DETECTOR.detectMarkers(np.ascontiguousarray(gray))
    return {} if ids is None else {i: c[0] for i, c in zip(ids.ravel().tolist(), corners)}


def page_number(ids):
    """The page most of the marks belong to, or None without marks."""
    ids = list(ids)
    return collections.Counter(i // 8 for i in ids).most_common(1)[0][0] if ids else None


def quarter_turns(marks):
    """k for np.rot90(image, k) that sets the page upright. A mark's first edge runs along its top, left to right."""
    angle = statistics.median(float(np.degrees(np.arctan2(c[1][1] - c[0][1], c[1][0] - c[0][0])))
                              for c in marks.values())
    return round(angle / 90) % 4


def main(sources, out):
    counts = collections.Counter()
    written = []
    for path in sorted(p for folder in sources for p in Path(folder).iterdir() if p.suffix.lower() in ('.jpg', '.jpeg')):
        image = cv2.imread(str(path))
        scale = SEARCH_SIZE / max(image.shape[:2])
        marks = find_marks(cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA))
        number = page_number(marks)
        if number is None or not FIRST_PAGE <= number <= LAST_PAGE:
            counts['skipped'] += 1
            print(f'{path.name}: {"no marks" if number is None else f"page T{number:02d}"}, skipped')
            continue
        marks = {i: c for i, c in marks.items() if i // 8 == number}
        folder = out / 'photos' / ('test' if number >= FIRST_TEST_PAGE else 'train')
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f'T{number:02d}__{path.name}'
        turns = quarter_turns(marks)
        if turns == 0:
            target.write_bytes(strip_metadata(path.read_bytes()))
        else:
            cv2.imwrite(str(target), np.rot90(image, turns), [cv2.IMWRITE_JPEG_QUALITY, 95])
        counts[f'{folder.name} T{number:02d}' + (' turned' if turns else '')] += 1
        written.append(target)
    for key, n in sorted(counts.items()):
        print(f'{key}: {n}')
    left = [p.name for p in written if dict(Image.open(p).getexif())]
    print(f'metadata left in {len(left)} of {len(written)} written photos' + (f': {left}' if left else ''))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sources', nargs='+')
    parser.add_argument('--out', default=str(Path(__file__).parent.parent))
    args = parser.parse_args()
    main(args.sources, Path(args.out))
