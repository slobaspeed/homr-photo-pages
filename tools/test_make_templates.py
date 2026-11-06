import sys
from pathlib import Path

import cv2
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from make_templates import make_page, next_number  # noqa: E402

DETECTOR = cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000))
NOTE = '<note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><type>whole</type></note>'
SMALL_SCORE = (
    '<?xml version="1.0" encoding="UTF-8"?><score-partwise version="3.1"><part-list><score-part id="P1">'
    '<part-name>Piano</part-name></score-part></part-list><part id="P1">'
    '<measure number="1"><attributes><divisions>1</divisions><key><fifths>0</fifths></key>'
    '<time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>'
    + NOTE + '</measure>'
    + ''.join(f'<measure number="{n}">{NOTE}</measure>' for n in range(2, 9))
    + '</part></score-partwise>')


def test_new_page_carries_its_own_eight_marks():
    page, entry = make_page(SMALL_SCORE, 51, 'Leipzig', 40)
    assert page.shape == (3508, 2480)
    _, ids, _ = DETECTOR.detectMarkers(page)
    assert sorted(ids.ravel().tolist()) == list(range(408, 416))
    assert entry['name'] == 'T51' and entry['marks']['ids'] == list(range(408, 416))


def test_numbers_stop_at_page_124():
    assert next_number(['T23', 'T50']) == 51
    assert next_number(['T23', 'T60']) == 61
    with pytest.raises(ValueError):
        next_number(['T124'])
