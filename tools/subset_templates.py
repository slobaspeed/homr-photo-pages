"""Copies template pages T23-T50 from the research templates (PDF, templates.json, answer keys) into templates/, and
writes templates/sources.md with where every page's music comes from and its licence. T01-T22 stay out: they carry
the music of homr's photo test set (liebharc/sheet-music-photos).

Mutopia licences are read from each piece's own PDF footer.

Run: python tools/subset_templates.py <research templates folder> <Mutopia pdf folder>
"""
import json
import re
import shutil
import sys
from pathlib import Path

import fitz

OUT = Path(__file__).parent.parent / 'templates'
FIRST, LAST = 23, 50
LICENCES = {  # how each licence is written on Mutopia footers
    'Creative Commons Attribution-ShareAlike 4.0': 'CC BY-SA 4.0',
    'Creative Commons Attribution-ShareAlike 3.0': 'CC BY-SA 3.0',
    'Creative Commons Attribution-ShareAlike 2.5': 'CC BY-SA 2.5',
    'Creative Commons Attribution 4.0': 'CC BY 4.0',
    'Creative Commons Attribution 3.0': 'CC BY 3.0',
    'Creative Commons Attribution 2.5': 'CC BY 2.5',
    'Public Domain': 'public domain',
}


def mutopia_licence(pdf):
    """The licence a Mutopia PDF states in its footer."""
    text = ' '.join(' '.join(page.get_text().split()) for page in fitz.open(pdf)).lower()
    for written, short in LICENCES.items():
        if written.lower() in text:
            return short
    raise ValueError(f'no known licence in {pdf}')


def source_row(template, mutopia):
    name, kind, source = template['name'], template['kind'], template['source']
    if kind == 'lilypond':
        piece = re.match(r'Mutopia (.+) page \d+$', source).group(1)
        return name, f'Mutopia: {piece}', mutopia_licence(mutopia / f'{piece}.pdf')
    if re.search(r'_lc\d+', source):  # Lieder files carry a Library of Congress number; long names were cut short
        return name, f'OpenScore Lieder: {source.removesuffix("_mxl")}', 'CC0'
    return name, f'ASAP: {source}', 'CC BY-NC-SA 4.0'


def main(research, mutopia):
    data = json.loads((research / 'templates.json').read_text(encoding='utf-8'))
    keep = [t for t in data['templates'] if FIRST <= int(t['name'][1:]) <= LAST]
    (OUT / 'keys').mkdir(parents=True, exist_ok=True)
    (OUT / 'templates.json').write_text(json.dumps({**data, 'templates': keep}, indent=1), encoding='utf-8')
    pdf = fitz.open()
    pdf.insert_pdf(fitz.open(research / 'templates.pdf'), from_page=FIRST - 1, to_page=LAST - 1)
    pdf.save(OUT / 'templates.pdf', garbage=4, deflate=True)
    for t in keep:
        if 'key' in t:
            shutil.copyfile(research / t['key'], OUT / t['key'])
    rows = [source_row(t, mutopia) for t in keep]
    lines = ['# Where the music on each page comes from', '',
             'A photo of a page is a copy of the music printed on it, so each photo keeps the licence of its page.', '',
             '| Page | Music | Licence |', '|---|---|---|'] + [f'| {n} | {s} | {lic} |' for n, s, lic in rows]
    (OUT / 'sources.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for n, s, lic in rows:
        print(f'{n}  {lic:16} {s}')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
