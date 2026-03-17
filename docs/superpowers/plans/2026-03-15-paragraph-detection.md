# 段落翻译优化 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复小字体内容段落检测失效、及翻译后端不保留换行导致分段显示失败两个问题。

**Architecture:** 修改 `overlay_layout.py` 中的分段阈值从固定系数改为自适应中位数；修改 `controller.py` 发送编号列表格式并用回退链解析译文。整体流程不变，不增加额外 API 调用。

**Tech Stack:** Python，PyQt5，RapidOCR，deep-translator，`re` 标准库

---

## Chunk 1: 自适应段落检测

### Task 1: 自适应间距检测（overlay_layout.py）

**Files:**
- Modify: `src/core/overlay_layout.py:66-82, 104-139`
- Test: `tests/test_overlay_layout.py`

- [ ] **Step 1: 写小字体场景的失败测试**

在 `tests/test_overlay_layout.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/test_overlay_layout.py::test_small_font_detects_three_paragraphs tests/test_overlay_layout.py::test_single_line_returns_one_paragraph -v
```

预期：`test_small_font_detects_three_paragraphs` FAIL（旧算法返回1段），`test_single_line_returns_one_paragraph` PASS（已有的边界处理）。

- [ ] **Step 3: 实现自适应检测**

将 `src/core/overlay_layout.py` 的 `_can_merge_lines`（第66-81行）改为接收预算好的 `break_threshold`，并重写 `group_rows_into_paragraphs`（第104-139行）改为自适应阈值：

```python
def _can_merge_lines(previous_rect, current_rect, break_threshold: float) -> bool:
    """Return True if two lines belong to the same paragraph."""
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0
    if vertical_gap > break_threshold:
        return False
    overlap = _horizontal_overlap(previous_rect, current_rect)
    min_width = max(1, min(previous_rect['width'], current_rect['width']))
    if overlap >= int(min_width * 0.15):
        return True
    indent_threshold = max(18, int(max(previous_rect['height'], current_rect['height']) * 2.5))
    return abs(previous_rect['x'] - current_rect['x']) <= indent_threshold


def group_rows_into_paragraphs(rows, gap_ratio: float = 0.0):
    normalized = []
    for row in rows or []:
        text = str(row.get('text', '')).strip()
        box = row.get('box') or []
        if not text or len(box) < 4:
            continue
        normalized.append({
            'text': text,
            'box': box,
            'rect': _rect_from_box(box),
        })

    normalized.sort(key=lambda row: (row['rect']['y'], row['rect']['x']))
    if not normalized:
        return []

    lines = _group_rows_into_lines(normalized)

    # 边界：0或1行时直接返回单段，无需计算阈值
    if len(lines) <= 1:
        if not lines:
            return []
        return [{'text': lines[0]['text'], 'rows': list(lines[0]['rows']), 'rect': dict(lines[0]['rect'])}]

    # 自适应阈值：收集所有行间距，取下中位数
    gaps = [
        max(0, lines[i]['rect']['y'] - _rect_bottom(lines[i - 1]['rect']))
        for i in range(1, len(lines))
    ]
    lower_median = sorted(gaps)[(len(gaps) - 1) // 2]
    break_threshold = max(lower_median * 1.8, 6) * (1 + gap_ratio)

    paragraphs = []
    current = None
    previous_line = None
    for line in lines:
        if current is None or not _can_merge_lines(previous_line['rect'], line['rect'], break_threshold):
            current = {
                'text': line['text'],
                'rows': list(line['rows']),
                'rect': dict(line['rect']),
            }
            paragraphs.append(current)
        else:
            current['text'] = f"{current['text']}\n{line['text']}"
            current['rows'].extend(line['rows'])
            _expand_rect(current['rect'], line['rect'])
        previous_line = line

    return paragraphs
```

- [ ] **Step 4: 运行所有 overlay_layout 测试，确认全部通过**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/test_overlay_layout.py -v
```

预期：全部 PASS（包括新测试和原有4个测试）。

- [ ] **Step 5: 提交**

```bash
cd c:/Users/Administrator/my-todo && git add src/core/overlay_layout.py tests/test_overlay_layout.py && git commit -m "fix: adaptive paragraph gap detection based on inter-line median"
```

---

## Chunk 2: 编号列表格式 + 解析回退链

### Task 2: 解析辅助函数（controller.py）

**Files:**
- Modify: `src/core/controller.py:1-5`（添加 `import re` 和模块级函数）
- Test: `tests/test_controller_normalize.py`

- [ ] **Step 1: 写 `_parse_paragraph_translations` 的失败测试**

在 `tests/test_controller_normalize.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认全部失败（函数不存在）**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/test_controller_normalize.py -k "parse" -v
```

预期：全部 FAIL，错误 `ImportError: cannot import name '_parse_paragraph_translations'`。

- [ ] **Step 3: 添加 `import re` 和 `_parse_paragraph_translations` 函数**

在 `src/core/controller.py` 第1行添加 `import re`，并在 `logger = logging.getLogger(__name__)` 这一行**之后**（即 `_fmt_hotkey` 函数之前）插入函数：

```python
import re
```

```python
def _parse_paragraph_translations(text: str, count: int) -> list:
    """将译文拆分为 count 个段落字符串，四级回退。

    Level 1: 编号列表正则（1. / 1)）
    Level 2: 双换行分割
    Level 3: 单换行分割
    Level 4: 失败 → 返回 []
    每级仅当结果数量恰好等于 count 时才采用。
    """
    if count <= 0:
        return []
    if count == 1:
        return [text.strip()] if text.strip() else []

    # Level 1: 编号列表
    parts = re.findall(r'^\d+[.)]\s*(.+)', text, re.MULTILINE)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) == count:
        return parts

    # Level 2: 双换行
    parts = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(parts) == count:
        return parts

    # Level 3: 单换行
    parts = [p.strip() for p in text.split('\n') if p.strip()]
    if len(parts) == count:
        return parts

    return []
```

- [ ] **Step 4: 运行新测试，确认通过**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/test_controller_normalize.py -k "parse" -v
```

预期：全部 PASS。

- [ ] **Step 5: 更新发送格式测试**

`test_normalize_multi_paragraph_splits_text_with_double_newline` 的旧断言 `assert '\n\n' in result['text']` 在新格式下会失败。将该断言替换为：

```python
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
```

- [ ] **Step 6: 运行所有 controller_normalize 测试，确认全部通过**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/test_controller_normalize.py -v
```

预期：全部 PASS（3个原有测试 + 7个新测试）。

- [ ] **Step 7: 提交**

```bash
cd c:/Users/Administrator/my-todo && git add src/core/controller.py tests/test_controller_normalize.py && git commit -m "feat: add _parse_paragraph_translations with 3-level fallback chain"
```

---

### Task 3: 接入编号列表格式和回退解析（controller.py）

**Files:**
- Modify: `src/core/controller.py:109-115`（`_normalize_ocr_payload`）
- Modify: `src/core/controller.py:622-635`（`_on_translate_done`）

- [ ] **Step 1: 修改 `_normalize_ocr_payload` 的发送格式**

将 `src/core/controller.py` 第111行：

```python
        if para_enabled and len(paras) >= 2:
            para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
            text = '\n\n'.join(para_texts)
```

改为：

```python
        if para_enabled and len(paras) >= 2:
            para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
            text = '\n'.join(f'{i + 1}. {t}' for i, t in enumerate(para_texts))
```

- [ ] **Step 2: 修改 `_on_translate_done` 的段落匹配逻辑**

将 `src/core/controller.py` 第622-635行：

```python
        if box is not None:
            pending = getattr(box, '_pending_para_texts', [])
            if pending:
                parts = result.get('translated', '').split('\n\n')
                if len(parts) == len(pending):
                    result['paragraphs'] = [
                        {'text': orig, 'translation': trans}
                        for orig, trans in zip(pending, parts)
                    ]
                else:
                    result['paragraphs'] = []
                box._pending_para_texts = []
        result.setdefault('paragraphs', [])
```

改为：

```python
        if box is not None:
            pending = getattr(box, '_pending_para_texts', [])
            if pending:
                parts = _parse_paragraph_translations(
                    result.get('translated', ''), len(pending)
                )
                if len(parts) == len(pending):
                    result['paragraphs'] = [
                        {'text': orig, 'translation': trans}
                        for orig, trans in zip(pending, parts)
                    ]
                else:
                    result['paragraphs'] = []
                box._pending_para_texts = []
        result.setdefault('paragraphs', [])
```

- [ ] **Step 3: 运行全量测试，确认无回归**

```bash
cd c:/Users/Administrator/my-todo && python -m pytest tests/ -v --tb=short
```

预期：全部 PASS，无新增失败。

- [ ] **Step 4: 提交**

```bash
cd c:/Users/Administrator/my-todo && git add src/core/controller.py && git commit -m "fix: use numbered list format and fallback parser for paragraph translation matching"
```
