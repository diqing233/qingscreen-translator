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
        {'text': 'Line 3', 'box': [[10, 70], [90, 70], [90, 84], [10, 84]]},
    ]
    paras = group_rows_into_paragraphs(rows, gap_ratio=3.0)
    assert len(paras) == 1


def test_small_font_detects_three_paragraphs():
    """旧算法对14px字体全部合并为1段；新算法应正确拆出3段。"""
    from core.overlay_layout import group_rows_into_paragraphs
    # 3段：段内行间距4px，段落间距10px
    rows = [
        {'text': 'P1L1', 'box': [[0,   0], [100,   0], [100,  14], [0,  14]]},
        {'text': 'P1L2', 'box': [[0,  18], [100,  18], [100,  32], [0,  32]]},
        {'text': 'P1L3', 'box': [[0,  36], [100,  36], [100,  50], [0,  50]]},
        {'text': 'P2L1', 'box': [[0,  60], [100,  60], [100,  74], [0,  74]]},
        {'text': 'P2L2', 'box': [[0,  78], [100,  78], [100,  92], [0,  92]]},
        {'text': 'P3L1', 'box': [[0, 102], [100, 102], [100, 116], [0, 116]]},
        {'text': 'P3L2', 'box': [[0, 120], [100, 120], [100, 134], [0, 134]]},
    ]
    paragraphs = group_rows_into_paragraphs(rows)
    assert len(paragraphs) == 3
    assert paragraphs[0]['text'] == 'P1L1\nP1L2\nP1L3'
    assert paragraphs[1]['text'] == 'P2L1\nP2L2'
    assert paragraphs[2]['text'] == 'P3L1\nP3L2'


def test_single_line_returns_one_paragraph():
    """只有1行时不崩溃，返回单段。"""
    from core.overlay_layout import group_rows_into_paragraphs
    rows = [{'text': 'Only line', 'box': [[0, 0], [100, 0], [100, 14], [0, 14]]}]
    paragraphs = group_rows_into_paragraphs(rows)
    assert len(paragraphs) == 1
    assert paragraphs[0]['text'] == 'Only line'
