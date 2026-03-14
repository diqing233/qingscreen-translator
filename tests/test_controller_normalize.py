import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class _FakeSettings:
    def __init__(self, data):
        self._data = data
    def get(self, key, default=None):
        return self._data.get(key, default)


def _make_ctrl(para_enabled=True, gap_ratio=0.5):
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl.settings = _FakeSettings({
        'para_split_enabled': para_enabled,
        'para_gap_ratio': gap_ratio,
    })
    return ctrl


def test_normalize_single_paragraph_returns_no_para_texts():
    """单段文本不触发分段，返回空 para_texts 和空 paragraphs。"""
    ctrl = _make_ctrl()
    payload = {
        'text': 'hello world',
        'rows': [
            {'text': 'hello', 'box': [[0, 0], [40, 0], [40, 14], [0, 14]]},
            {'text': 'world', 'box': [[50, 0], [90, 0], [90, 14], [50, 14]]},
        ],
    }
    result = ctrl._normalize_ocr_payload(payload)
    assert result['text'] == 'hello world'
    assert result['paragraphs'] == []
    assert result['para_texts'] == []


def test_normalize_multi_paragraph_splits_text_with_double_newline():
    """多段落文本：text 用 \\n\\n 连接，para_texts 包含各段纯文本。"""
    ctrl = _make_ctrl()
    # Line 3 距 Line 2 有大间距（gap=38 > threshold≈33） → 被切分为两个段落
    payload = {
        'text': 'L1 L2 L3',
        'rows': [
            {'text': 'L1', 'box': [[0,  0], [20,  0], [20, 14], [0, 14]]},
            {'text': 'L2', 'box': [[0, 18], [20, 18], [20, 32], [0, 32]]},
            {'text': 'L3', 'box': [[0, 70], [20, 70], [20, 84], [0, 84]]},
        ],
    }
    result = ctrl._normalize_ocr_payload(payload)
    assert '\n\n' in result['text']
    assert len(result['paragraphs']) >= 2
    assert len(result['para_texts']) == len(result['paragraphs'])


def test_normalize_disabled_returns_original_text():
    """para_split_enabled=False 时直接返回原始文本，不做分段。"""
    ctrl = _make_ctrl(para_enabled=False)
    payload = {
        'text': 'original text',
        'rows': [
            {'text': 'original', 'box': [[0,  0], [60,  0], [60, 14], [0, 14]]},
            {'text': 'text',     'box': [[0, 60], [40, 60], [40, 74], [0, 74]]},
        ],
    }
    result = ctrl._normalize_ocr_payload(payload)
    assert result['text'] == 'original text'
    assert result['paragraphs'] == []
    assert result['para_texts'] == []
