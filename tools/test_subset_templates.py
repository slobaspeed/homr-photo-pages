import json
from pathlib import Path

import fitz

TEMPLATES = Path(__file__).parent.parent / 'templates'


def test_subset_holds_exactly_t23_to_t50():
    data = json.loads((TEMPLATES / 'templates.json').read_text(encoding='utf-8'))
    assert [t['name'] for t in data['templates']] == [f'T{n}' for n in range(23, 51)]
    assert fitz.open(TEMPLATES / 'templates.pdf').page_count == 28
    assert all(t['marks']['ids'] == list(range(8 * n, 8 * n + 8)) for n, t in zip(range(23, 51), data['templates']))


def test_every_verovio_page_has_its_answer():
    data = json.loads((TEMPLATES / 'templates.json').read_text(encoding='utf-8'))
    keys = [t['key'] for t in data['templates'] if t['kind'] == 'verovio']
    assert keys == [f'keys/T{n}.musicxml' for n in range(35, 51)]
    assert all((TEMPLATES / k).exists() for k in keys)


def test_a_lieder_song_with_a_cut_name_is_still_cc0():
    from subset_templates import source_row
    cut = {'name': 'T39', 'kind': 'verovio', 'source': '8_Lieder_und_Ges_nge_Op_57_4_Ach_wende_diesen_Blick_lc503305'}
    assert source_row(cut, None)[2] == 'CC0'


def test_every_page_has_a_licence():
    rows = [line for line in (TEMPLATES / 'sources.md').read_text(encoding='utf-8').splitlines()
            if line.startswith('| T')]
    assert [r.split('|')[1].strip() for r in rows] == [f'T{n}' for n in range(23, 51)]
    assert all(r.split('|')[3].strip() for r in rows)
