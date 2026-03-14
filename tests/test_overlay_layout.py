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


def test_gap_ratio_default_preserves_behavior():
    """gap_ratio=0.0 时行为与修改前一致（向后兼容）。"""
    from core.overlay_layout import group_rows_into_paragraphs
    rows = [
        {'text': 'Line 1', 'box': [[10, 10], [90, 10], [90, 24], [10, 24]]},
        {'text': 'Line 2', 'box': [[12, 28], [92, 28], [92, 42], [12, 42]]},
        {'text': 'Line 3', 'box': [[10, 70], [90, 70], [90, 84], [10, 84]]},
    ]
    # 不传 gap_ratio → 使用默认 0.0 → 结果与之前相同
    paras_default = group_rows_into_paragraphs(rows)
    paras_explicit = group_rows_into_paragraphs(rows, gap_ratio=0.0)
    assert [p['text'] for p in paras_default] == ['Line 1\nLine 2', 'Line 3']
    assert [p['text'] for p in paras_explicit] == ['Line 1\nLine 2', 'Line 3']


def test_gap_ratio_larger_merges_more_paragraphs():
    """gap_ratio>0 使阈值更宽松，本来切分的段落被合并。"""
    from core.overlay_layout import group_rows_into_paragraphs
    # Line 3 gap = 70-24 = 46px，行高 14px，原始阈值 ≈ 22px → 被切分
    # gap_ratio=3.0 → 阈值 ≈ 14*1.6*4=89px > 46px → 合并为一段
    rows = [
        {'text': 'Line 1', 'box': [[10, 10], [90, 10], [90, 24], [10, 24]]},
        {'text': 'Line 2', 'box': [[12, 28], [92, 28], [92, 42], [12, 42]]},
        {'text': 'Line 3', 'box': [[10, 70], [90, 70], [90, 84], [10, 74]]},
    ]
    paras = group_rows_into_paragraphs(rows, gap_ratio=3.0)
    assert len(paras) == 1
