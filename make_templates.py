"""New template pages to print and photograph, from your own music (MusicXML or .mxl).

Every page is A4 with the music shrunk a little (SCALE) and eight ArUco marks around it (corners and edge middles).
Page k carries the mark ids 8k..8k+7, in the order of MARK_SPOTS, so a photo says which page it shows and where each
part of the flat page landed, even when the page is cut off by the frame. New pages are numbered after the highest
page in templates/templates.json, from T51 up to T124 (the last page whose ids fit the mark dictionary).

Use music free of conditions (CC0 or public domain), so the photos stay simple to share.

Run: python make_templates.py <music.musicxml|.mxl>...
  appends the pages to templates/new.pdf, their entries to templates/templates.json and their answers to
  templates/keys/.
"""
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import cairosvg
import cv2
import fitz
import numpy as np
import verovio

HERE = Path(__file__).parent
OUT = HERE / 'templates'
W, H = 2480, 3508  # A4 at 300 dpi
MM = 300 / 25.4
SCALE = 0.86  # the music's share of the page width, leaving room for the marks
MARK = round(10 * MM)  # mark side
MARK_CENTER = 10 * MM  # from the page edge (printers leave about 4 mm blank)
MARK_SPOTS = ['top left', 'top middle', 'top right', 'right middle', 'bottom right', 'bottom middle', 'bottom left',
              'left middle']
ARUCO = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000)
FONTS = ['Leipzig', 'Bravura', 'Gootville', 'Leland', 'Petaluma']
SIZES = [30, 40, 55]  # Verovio scale: small, normal, large staves
FIRST_NEW, LAST = 51, 124  # 8 * 124 + 7 = 999, the last id of DICT_4X4_1000


def next_number(existing):
    """The number for the next new page: after the highest existing one, at least FIRST_NEW."""
    number = max([FIRST_NEW - 1] + [int(name[1:]) for name in existing]) + 1
    if number > LAST:
        raise ValueError(f'no more pages: the marks run out after T{LAST}')
    return number


def read_music(path):
    path = Path(path)
    if path.suffix == '.mxl':
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith(('.xml', '.musicxml')) and not n.startswith('META-INF'))
            return z.read(name).decode('utf-8')
    return path.read_text(encoding='utf-8')


def first_measures(xml, count):
    """The score with only its first `count` measures in every part."""
    root = ET.fromstring(xml.encode('utf-8'))
    for part in root.findall('part'):
        for measure in part.findall('measure')[count:]:
            part.remove(measure)
    return ET.tostring(root, encoding='unicode')


def engrave(xml, font, size):
    """The most measures from the start that fit on one page, engraved (grey image) and as MusicXML."""
    options = {'pageWidth': 2100, 'pageHeight': 2970, 'scale': size, 'adjustPageHeight': False, 'footer': 'none',
               'font': font, 'pageMarginLeft': 150, 'pageMarginRight': 150,  # staves clear of the side marks
               'header': 'none'}  # Verovio's titles ran off the page or lost letters

    def toolkit(count):
        tk = verovio.toolkit()
        tk.setOptions(options)
        tk.loadData(first_measures(xml, count))
        return tk

    low, high = 1, len(ET.fromstring(xml.encode('utf-8')).find('part').findall('measure'))
    while low < high:
        mid = (low + high + 1) // 2
        if toolkit(mid).getPageCount() == 1:
            low = mid
        else:
            high = mid - 1
    if low < 4:
        raise ValueError('fewer than 4 bars fit on a page')
    png = cairosvg.svg2png(bytestring=toolkit(low).renderToSVG(1).encode('utf-8'), background_color='white', scale=1.5)
    return cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_GRAYSCALE), first_measures(xml, low)


def mark_centers():
    lo_x, hi_x, mid_x = MARK_CENTER, W - MARK_CENTER, W / 2
    lo_y, hi_y, mid_y = MARK_CENTER, H - MARK_CENTER, H / 2
    return [(lo_x, lo_y), (mid_x, lo_y), (hi_x, lo_y), (hi_x, mid_y), (hi_x, hi_y), (mid_x, hi_y), (lo_x, hi_y),
            (lo_x, mid_y)]


def on_template(music, number, label):
    """The music centred on an A4 page at SCALE, with the marks and a small label."""
    f = min(SCALE * W / music.shape[1], (H - 2 * (MARK_CENTER + MARK)) / music.shape[0])
    small = cv2.resize(music, (round(music.shape[1] * f), round(music.shape[0] * f)), interpolation=cv2.INTER_AREA)
    page = np.full((H, W), 255, np.uint8)
    y, x = (H - small.shape[0]) // 2, (W - small.shape[1]) // 2
    page[y:y + small.shape[0], x:x + small.shape[1]] = small
    corners = []
    for spot, (cx, cy) in enumerate(mark_centers()):
        x0, y0 = round(cx - MARK / 2), round(cy - MARK / 2)
        page[y0:y0 + MARK, x0:x0 + MARK] = cv2.aruco.generateImageMarker(ARUCO, 8 * number + spot, MARK)
        corners.append([[x0, y0], [x0 + MARK, y0], [x0 + MARK, y0 + MARK], [x0, y0 + MARK]])
    cv2.putText(page, f'T{number:02d} {label}', (round(W / 2 + 12 * MM), round(H - 7 * MM)), cv2.FONT_HERSHEY_SIMPLEX,
                1.1, 0, 2, cv2.LINE_AA)
    return page, corners, [x, y, small.shape[1], small.shape[0]]


def make_page(xml, number, font, size):
    """The printable page for template `number` and its templates.json entry (with the answer under 'musicxml')."""
    music, key = engrave(xml, font, size)
    page, corners, box = on_template(music, number, f'verovio {font}')
    entry = {'name': f'T{number:02d}', 'kind': 'verovio', 'font': font, 'size': size,
             'marks': {'ids': list(range(8 * number, 8 * number + 8)), 'corners': corners}, 'music_box': box,
             'musicxml': key}
    return page, entry


def main(paths):
    data = json.loads((OUT / 'templates.json').read_text(encoding='utf-8'))
    new_pdf = OUT / 'new.pdf'
    pdf = fitz.open(new_pdf) if new_pdf.exists() else fitz.open()
    for path in paths:
        number = next_number([t['name'] for t in data['templates']])
        font, size = FONTS[number % len(FONTS)], SIZES[number % len(SIZES)]
        try:
            page, entry = make_page(read_music(path), number, font, size)
        except ValueError as e:
            print(f'{path}: {e}, skipped')
            continue
        name = entry['name']
        (OUT / 'keys').mkdir(exist_ok=True)
        (OUT / 'keys' / f'{name}.musicxml').write_text(entry.pop('musicxml'), encoding='utf-8')
        data['templates'].append({**entry, 'source': Path(path).stem, 'key': f'keys/{name}.musicxml'})
        png = cv2.imencode('.png', page)[1].tobytes()
        pdf.new_page(width=595.28, height=841.89).insert_image(fitz.Rect(0, 0, 595.28, 841.89), stream=png)
        print(f'{name}: {font} {size} {path}')
    pdf.save(new_pdf.with_suffix('.tmp'), garbage=3, deflate=True)  # PyMuPDF can't rewrite the file it read
    pdf.close()
    new_pdf.with_suffix('.tmp').replace(new_pdf)
    (OUT / 'templates.json').write_text(json.dumps(data, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
