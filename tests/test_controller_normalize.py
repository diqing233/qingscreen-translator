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
    """多段落文本：text 改用编号列表格式，para_texts 包含各段纯文本。"""
    ctrl = _make_ctrl()
    payload = {
        'text': 'L1 L2 L3',
        'rows': [
            {'text': 'L1', 'box': [[0,  0], [20,  0], [20, 14], [0, 14]]},
            {'text': 'L2', 'box': [[0, 18], [20, 18], [20, 32], [0, 32]]},
            {'text': 'L3', 'box': [[0, 70], [20, 70], [20, 84], [0, 84]]},
        ],
    }
    result = ctrl._normalize_ocr_payload(payload)
    assert result['text'] == '1. L1 L2\n2. L3'
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


def test_parse_numbered_list_exact_match():
    """编号列表格式，数量匹配时提取段落文本。"""
    from core.controller import _parse_paragraph_translations
    text = "1. First para\n2. Second para\n3. Third para"
    assert _parse_paragraph_translations(text, 3) == ["First para", "Second para", "Third para"]


def test_parse_numbered_list_with_parenthesis():
    """支持 '1)' 格式的编号。"""
    from core.controller import _parse_paragraph_translations
    text = "1) Para one\n2) Para two"
    assert _parse_paragraph_translations(text, 2) == ["Para one", "Para two"]


def test_parse_fallback_double_newline():
    """编号列表数量不符时，回退到双换行分割。"""
    from core.controller import _parse_paragraph_translations
    text = "First para\n\nSecond para"
    assert _parse_paragraph_translations(text, 2) == ["First para", "Second para"]


def test_parse_fallback_single_newline():
    """双换行也不符时，回退到单换行分割。"""
    from core.controller import _parse_paragraph_translations
    text = "First para\nSecond para"
    assert _parse_paragraph_translations(text, 2) == ["First para", "Second para"]


def test_parse_fallback_returns_empty():
    """三级均无法匹配时返回空列表。"""
    from core.controller import _parse_paragraph_translations
    assert _parse_paragraph_translations("just one line", 3) == []


def test_parse_count_mismatch_tries_next_level():
    """编号列表条数与期望不符时，不使用该级结果，继续回退。"""
    from core.controller import _parse_paragraph_translations
    # 编号找到3项，期望2项 → 跳过；\n\n 得到3项 → 跳过；\n 得到3项 → 跳过 → []
    text = "1. a\n2. b\n3. c"
    assert _parse_paragraph_translations(text, 2) == []


def test_parse_single_paragraph():
    """count=1 时直接返回整体文本。"""
    from core.controller import _parse_paragraph_translations
    assert _parse_paragraph_translations("whole text", 1) == ["whole text"]


def test_parse_count_zero_returns_empty():
    """count=0 时返回空列表。"""
    from core.controller import _parse_paragraph_translations
    assert _parse_paragraph_translations("any text", 0) == []


def test_parse_single_empty_text_returns_empty():
    """count=1 但文本为空时返回空列表。"""
    from core.controller import _parse_paragraph_translations
    assert _parse_paragraph_translations("", 1) == []
