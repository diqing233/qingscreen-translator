import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_group_rows_into_paragraphs_merges_close_rows_and_splits_large_gaps():
    from core.overlay_layout import group_rows_into_paragraphs

    rows = [
        {'text': 'Line 1', 'box': [[10, 10], [90, 10], [90, 24], [10, 24]]},
        {'text': 'Line 2', 'box': [[12, 28], [92, 28], [92, 42], [12, 42]]},
        {'text': 'Line 3', 'box': [[10, 70], [90, 70], [90, 84], [10, 84]]},
    ]

    paragraphs = group_rows_into_paragraphs(rows)

    assert [p['text'] for p in paragraphs] == ['Line 1\nLine 2', 'Line 3']
    assert paragraphs[0]['rect'] == {'x': 10, 'y': 10, 'width': 82, 'height': 32}
    assert paragraphs[1]['rect'] == {'x': 10, 'y': 70, 'width': 80, 'height': 14}


def test_group_rows_into_paragraphs_merges_same_line_fragments_and_loose_line_spacing():
    from core.overlay_layout import group_rows_into_paragraphs

    rows = [
        {'text': 'This is', 'box': [[10, 10], [60, 10], [60, 24], [10, 24]]},
        {'text': 'one paragraph.', 'box': [[68, 10], [170, 10], [170, 24], [68, 24]]},
        {'text': 'Still the same paragraph.', 'box': [[18, 40], [178, 40], [178, 54], [18, 54]]},
        {'text': 'Next paragraph', 'box': [[10, 92], [120, 92], [120, 106], [10, 106]]},
    ]

    paragraphs = group_rows_into_paragraphs(rows)

    assert [p['text'] for p in paragraphs] == [
        'This is one paragraph.\nStill the same paragraph.',
        'Next paragraph',
    ]
    assert paragraphs[0]['rect'] == {'x': 10, 'y': 10, 'width': 168, 'height': 44}
