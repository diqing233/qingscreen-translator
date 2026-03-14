# 分段翻译功能 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 ScreenTranslator 添加自然段检测和分段翻译功能，原文和译文均以 `[1] [2]` 编号格式分段显示，支持一键切换分段/整体视图。

**Architecture:** OCR 识别后通过现有 `group_rows_into_paragraphs()` 检测段落，各段文本以 `\n\n` 分隔后整体发送给翻译后端；译文按 `\n\n` 拆分还原，段落对象写入 `result['paragraphs']` 字段；result_bar 按字段决定是否分段渲染。段落数不匹配时静默降级为整体显示。

**Tech Stack:** Python 3.14, PyQt5 5.15.11, pytest

---

## Chunk 1: Foundation — settings + overlay_layout

### Task 1: 新增 settings.py 默认值

**Files:**
- Modify: `src/core/settings.py`
- Test: `tests/test_settings.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_settings.py` 末尾追加：

```python
def test_para_split_defaults():
    import tempfile, os
    from core.settings import SettingsStore
    with tempfile.TemporaryDirectory() as d:
        s = SettingsStore(os.path.join(d, 'settings.json'))
        assert s.get('para_split_enabled') is True
        assert s.get('para_gap_ratio') == 0.5
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_settings.py::test_para_split_defaults -v
```

预期输出：`FAILED`（KeyError 或断言失败）

- [ ] **Step 3: 在 `src/core/settings.py` DEFAULTS 中追加两个键**

在 `src/core/settings.py` 第 36 行（`}` 前）找到 DEFAULTS 末尾，在 `'api_keys': {...}` 之前（任意位置均可）添加：

```python
    'para_split_enabled': True,
    'para_gap_ratio':     0.5,
```

确保 DEFAULTS 结构保持正确（逗号、缩进）。

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_settings.py -v
```

预期：全部 PASSED

- [ ] **Step 5: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/settings.py tests/test_settings.py && git commit -m "feat: add para_split_enabled and para_gap_ratio defaults to settings"
```

---

### Task 2: 为 overlay_layout.py 的 _can_merge_lines / group_rows_into_paragraphs 添加 gap_ratio 参数

**Files:**
- Modify: `src/core/overlay_layout.py`
- Test: `tests/test_overlay_layout.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_overlay_layout.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_overlay_layout.py::test_gap_ratio_default_preserves_behavior tests/test_overlay_layout.py::test_gap_ratio_larger_merges_more_paragraphs -v
```

预期：`FAILED`（TypeError: unexpected keyword argument 'gap_ratio'）

- [ ] **Step 3: 修改 `src/core/overlay_layout.py`**

**修改 `_can_merge_lines`**（当前第 66 行）：

将：
```python
def _can_merge_lines(previous_rect, current_rect):
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0

    height_threshold = max(12, int(max(previous_rect['height'], current_rect['height']) * 1.6))
    if vertical_gap > height_threshold:
        return False
```

改为：
```python
def _can_merge_lines(previous_rect, current_rect, gap_ratio: float = 0.0):
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0

    height_threshold = max(12, int(max(previous_rect['height'], current_rect['height']) * 1.6 * (1 + gap_ratio)))
    if vertical_gap > height_threshold:
        return False
```

**修改 `group_rows_into_paragraphs`**（当前第 104 行）：

将：
```python
def group_rows_into_paragraphs(rows):
```

改为：
```python
def group_rows_into_paragraphs(rows, gap_ratio: float = 0.0):
```

并将函数体内对 `_can_merge_lines` 的调用（第 126 行）：

将：
```python
        if current is None or not _can_merge_lines(previous_line['rect'], line['rect']):
```

改为：
```python
        if current is None or not _can_merge_lines(previous_line['rect'], line['rect'], gap_ratio):
```

- [ ] **Step 4: 运行所有 overlay_layout 测试，确认通过**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_overlay_layout.py -v
```

预期：全部 PASSED（原有测试不受影响，新测试也通过）

- [ ] **Step 5: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/overlay_layout.py tests/test_overlay_layout.py && git commit -m "feat: add gap_ratio param to group_rows_into_paragraphs and _can_merge_lines"
```

---

## Chunk 2: Controller 重构

### Task 3: 清理 controller.py 中的重复方法

**Files:**
- Modify: `src/core/controller.py`

> **注意**：在删除任何方法前，先阅读两个版本进行对比，确认保留版本包含所有有效逻辑。

**当前重复情况**（已分析确认）：

| 方法 | 死代码（删除） | 保留版本 |
|------|--------------|---------|
| `_on_translate_done` | 第 468 行（无 `box is not None` 守护，`box=None` 时会崩溃） | 第 643 行（有 `if box is not None` 守护）|
| `_on_overlay_requested` | 第 562 行（旧签名，无 mode 参数） | 第 605 行（含 mode 参数）|
| `_trigger_explain` | 第 205 行（旧版，功能较弱） | 第 626 行（读取 `current_source_text()`）|

- [ ] **Step 1: 确认两个 _on_translate_done 版本的差异**

阅读第 468-501 行（死代码版本）和第 643-676 行（保留版本），确认：
- 第 643 行版本有 `if box is not None and self._box_mode == 'multi':` 守护 ✓
- 第 643 行版本有 `if box is not None:` 块保护 box 属性访问 ✓

- [ ] **Step 2: 删除死代码 `_on_translate_done`（第 468 行版本）**

删除 `src/core/controller.py` 中从第一个 `def _on_translate_done` 开始到第二个 `def _on_translate_done` 之前的整个方法体（约第 468-501 行）。

删除范围：从 `    def _on_translate_done(self, result: dict, box, worker=None):` 到（不含）下一个方法定义（即 `    def _on_translate_error`，约第 503 行）。

- [ ] **Step 3: 删除旧版 `_on_overlay_requested`（第 562 行版本）**

删除从第一个 `def _on_overlay_requested` 到第二个 `def _on_overlay_requested` 之前的整个方法体（约第 562-577 行）。

- [ ] **Step 4: 删除旧版 `_trigger_explain`（第 205 行版本）**

在 `controller.py` 中搜索 `def _trigger_explain`，找到第一个版本（约第 205 行），确认第二个版本（约第 626 行）有完整逻辑（读取 `self.result_bar.current_source_text()`），然后删除第一个版本的完整方法体。

- [ ] **Step 5: 验证应用仍可编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from core.controller import CoreController; print('OK')"
```

预期：`OK`（无 SyntaxError / ImportError）

- [ ] **Step 6: 运行现有测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py -x
```

预期：全部 PASSED

- [ ] **Step 7: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/controller.py && git commit -m "refactor: remove duplicate _on_translate_done, _on_overlay_requested, _trigger_explain dead code"
```

---

### Task 4: 将 _normalize_ocr_payload 从模块级函数改为实例方法并新增段落检测

**Files:**
- Modify: `src/core/controller.py`
- Test: `tests/test_ocr_worker.py`（或新建 `tests/test_controller_normalize.py`）

- [ ] **Step 1: 写失败测试**

新建 `tests/test_controller_normalize.py`：

```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class _FakeSettings:
    def __init__(self, data):
        self._data = data
    def get(self, key, default=None):
        return self._data.get(key, default)


def _make_ctrl(para_enabled=True, gap_ratio=0.5):
    from core.controller import CoreController
    import unittest.mock as mock
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
    # Line 3 距 Line 2 有大间距 → 被切分为两个段落（gap_ratio=0.5，阈值≈21px，实际间距≈28px）
    payload = {
        'text': 'L1 L2 L3',
        'rows': [
            {'text': 'L1', 'box': [[0,  0], [20,  0], [20, 14], [0, 14]]},
            {'text': 'L2', 'box': [[0, 18], [20, 18], [20, 32], [0, 32]]},
            {'text': 'L3', 'box': [[0, 60], [20, 60], [20, 74], [0, 74]]},
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_controller_normalize.py -v
```

预期：`FAILED`（`_normalize_ocr_payload` 不在 CoreController 上，或 signature 不匹配）

- [ ] **Step 3: 修改 `src/core/controller.py`**

**3a. 删除模块级函数**（第 18-27 行）：

删除：
```python
def _normalize_ocr_payload(payload):
    if isinstance(payload, dict):
        return {
            'text': str(payload.get('text', '')),
            'rows': list(payload.get('rows', []) or []),
        }
    return {
        'text': str(payload or ''),
        'rows': [],
    }
```

**3b. 在 `CoreController` 类内添加实例方法**（在 `_on_ocr_done_for_rect` 方法之前，或放在 `__init__` 之后的合适位置）：

```python
def _normalize_ocr_payload(self, payload: dict) -> dict:
    from core.overlay_layout import group_rows_into_paragraphs
    if not isinstance(payload, dict):
        return {'text': str(payload or ''), 'rows': [], 'paragraphs': [], 'para_texts': []}
    rows = list(payload.get('rows', []) or [])
    para_enabled = self.settings.get('para_split_enabled', True)
    gap_ratio = float(self.settings.get('para_gap_ratio', 0.5))

    paras = []
    para_texts = []
    if para_enabled and rows:
        paras = group_rows_into_paragraphs(rows, gap_ratio=gap_ratio)

    if para_enabled and len(paras) >= 2:
        para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
        text = '\n\n'.join(para_texts)
    else:
        text = str(payload.get('text', ''))
        paras = []
        para_texts = []

    return {
        'text':       text,
        'rows':       rows,
        'paragraphs': paras,
        'para_texts': para_texts,
    }
```

**3c. 更新两处调用点**：

第 324 行（`_on_ocr_done_for_rect` 内）：
```python
# 旧：
text = _normalize_ocr_payload(payload)['text']
# 改为：
text = self._normalize_ocr_payload(payload)['text']
```

第 355 行（`_on_ocr_done` 内）：
```python
# 旧：
payload = _normalize_ocr_payload(payload)
# 改为：
payload = self._normalize_ocr_payload(payload)
```

同时移除 `_on_ocr_done` 内已有的那行 import（如果有单独的 import，改为在方法内或顶部导入）：
```python
# _on_ocr_done 第 358 行已有：
from core.overlay_layout import group_rows_into_paragraphs
# 保持不变（这行用于 overlay 段落检测，不受影响）
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/test_controller_normalize.py -v
```

预期：全部 PASSED

- [ ] **Step 5: 运行全量测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py -x
```

预期：全部 PASSED

- [ ] **Step 6: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/controller.py tests/test_controller_normalize.py && git commit -m "feat: convert _normalize_ocr_payload to instance method with paragraph detection"
```

---

### Task 5: _on_ocr_done 中暂存 para_texts，_on_translate_done 中配对段落

**Files:**
- Modify: `src/core/controller.py`

- [ ] **Step 1: 修改 `_on_ocr_done`**

在 `src/core/controller.py` 的 `_on_ocr_done` 方法中，找到现有的 overlay 段落写入代码段（约第 358-361 行）：

```python
        setattr(box, '_last_ocr_rows', payload['rows'])
        from core.overlay_layout import group_rows_into_paragraphs
        setattr(box, '_last_ocr_paragraphs', group_rows_into_paragraphs(payload['rows']))
        setattr(box, '_last_paragraph_translations', [])
        setattr(box, '_paragraph_translation_pending', False)
        setattr(box, '_pending_paragraph_translations', [])
```

在这段代码之后（在 `if text == '\x00LOW_CONTRAST':` 之前）追加：

```python
        # 分段翻译：暂存段落文本列表，供 _on_translate_done 配对译文
        box._pending_para_texts = payload.get('para_texts', [])
```

- [ ] **Step 2: 修改 `_on_translate_done`（第 643 行版本）**

在 `_on_translate_done` 中，找到 `if box is not None:` 块（约第 664-676 行）。在该块内，找到 `setattr(box, '_last_translation', translated)` 这一行之前，追加段落配对逻辑：

```python
        if box is not None:
            # 段落配对
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
        result.setdefault('paragraphs', [])  # box=None 路径也需要此字段
```

> **精确定位**：追加位置在 `if box is not None and self._box_mode == 'multi':` 块之前，即 `_on_translate_done` 方法体的最前面（`if self._is_translation_cancelled(worker): return` 之后，history.add 代码之后，`if box is not None and self._box_mode == 'multi':` 之前）。

最终 `_on_translate_done` 结构（第 643 行版本）应如下：

```python
def _on_translate_done(self, result: dict, box, worker=None):
    if self._is_translation_cancelled(worker):
        return
    try:
        self.history.add(...)
    except Exception as e:
        logger.warning(...)

    # ── 新增：段落配对 ──────────────────────────────────
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
    # ────────────────────────────────────────────────────

    if box is not None and self._box_mode == 'multi':
        ...
    else:
        self.result_bar.show_result(result)
    ...
```

- [ ] **Step 3: 验证编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from core.controller import CoreController; print('OK')"
```

- [ ] **Step 4: 运行全量测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py -x
```

预期：全部 PASSED

- [ ] **Step 5: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/controller.py && git commit -m "feat: store para_texts in _on_ocr_done and pair paragraphs in _on_translate_done"
```

---

## Chunk 3: Settings UI

### Task 6: settings_window.py 新增分段翻译控件

**Files:**
- Modify: `src/ui/settings_window.py`

- [ ] **Step 1: 在 imports 中添加 `QCheckBox` 和 `QDoubleSpinBox`**

在 `src/ui/settings_window.py` 第 1 行的 from 语句中添加 `QCheckBox` 和 `QDoubleSpinBox`：

```python
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
                              QListWidget, QListWidgetItem, QTabWidget,
                              QWidget, QFormLayout, QMessageBox,
                              QProgressBar, QGroupBox, QCheckBox)
```

- [ ] **Step 2: 在 `_setup_ui` 的通用 tab 末尾添加控件**

在 `_setup_ui` 方法中，找到：

```python
        tabs.addTab(gen, '通用')
```

在其之前添加（即在通用 tab 的 QFormLayout 末尾追加）：

```python
        self._para_check = QCheckBox('自动识别段落，分段翻译')
        form.addRow('', self._para_check)

        self._para_ratio_spin = QDoubleSpinBox()
        self._para_ratio_spin.setRange(0.1, 3.0)
        self._para_ratio_spin.setSingleStep(0.1)
        self._para_ratio_spin.setDecimals(1)
        self._para_ratio_spin.setToolTip('间距阈值越大，段落之间需要更大的垂直间距才会被切分')
        form.addRow('段落间距阈值（×行高）', self._para_ratio_spin)

        # checkbox 控制 spin 的可用性
        self._para_check.stateChanged.connect(
            lambda state: self._para_ratio_spin.setEnabled(bool(state))
        )
```

- [ ] **Step 3: 在 `_load_values` 末尾追加加载逻辑**

在 `_load_values` 方法末尾（`self._refresh_dict_status()` 之前）追加：

```python
        self._para_check.setChecked(bool(self.settings.get('para_split_enabled', True)))
        self._para_ratio_spin.setValue(float(self.settings.get('para_gap_ratio', 0.5)))
        self._para_ratio_spin.setEnabled(self._para_check.isChecked())
```

- [ ] **Step 4: 在 `_save` 方法中追加保存逻辑**

在 `_save` 方法的 `self.settings_saved.emit()` 之前追加：

```python
        self.settings.set('para_split_enabled', self._para_check.isChecked())
        self.settings.set('para_gap_ratio', self._para_ratio_spin.value())
```

- [ ] **Step 5: 验证编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from ui.settings_window import SettingsWindow; print('OK')"
```

预期：`OK`

- [ ] **Step 6: 运行全量测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py -x
```

- [ ] **Step 7: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/ui/settings_window.py && git commit -m "feat: add para_split_enabled and para_gap_ratio controls to settings window"
```

---

## Chunk 4: Result Bar

### Task 7: result_bar.py — 新增分段按钮、状态和核心逻辑

**Files:**
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: 在 `__init__` 中添加 `_para_mode` 状态变量**

在 `src/ui/result_bar.py` 的 `__init__` 方法中，找到现有的状态变量初始化区（约第 179-210 行），在 `self._overlay_mode = ...` 附近添加：

```python
        self._para_mode: bool = bool(self.settings.get('para_split_enabled', True))
```

- [ ] **Step 2: 在 `_details_actions_widget` 中添加 `_btn_para` 按钮**

在 `src/ui/result_bar.py` 中，找到（约第 484-494 行）：

```python
        self._btn_source   = self._action_btn('原文 ▼', '展开/收起原始识别文字', self._toggle_source)
        ...
        ar.addWidget(self._btn_source)
```

在 `ar.addWidget(self._btn_source)` 之前插入：

```python
        self._btn_para = self._action_btn('分段 ▼', '切换分段/整体显示模式', self._toggle_para_mode)
        self._btn_para.setEnabled(False)  # 初始无段落数据时置灰
        ar.addWidget(self._btn_para)
```

- [ ] **Step 3: 添加新方法**

在 `result_bar.py` 中任意适合位置（例如 `_toggle_source` 方法之前）添加以下四个方法：

```python
    def _format_para_text(self, paragraphs: list, key: str) -> str:
        return "\n".join(f"[{i+1}] {p[key]}" for i, p in enumerate(paragraphs))

    def _update_para_button(self):
        has_paras = bool(
            self._current_result and self._current_result.get('paragraphs')
        )
        self._btn_para.setText('分段 ▲' if self._para_mode else '分段 ▼')
        self._btn_para.setEnabled(has_paras)

    def _toggle_para_mode(self):
        self._para_mode = not self._para_mode
        self._source_dirty = False  # 用户主动切换格式，清除编辑保护
        self._update_para_button()
        if self._current_result:
            self.show_result(self._current_result)

    def sync_para_mode_from_settings(self):
        self._para_mode = bool(self.settings.get('para_split_enabled', True))
        self._update_para_button()
        if self._current_result:
            self.show_result(self._current_result)
```

- [ ] **Step 4: 修改 `show_result` 方法**

在 `show_result`（第 1252 行）中，找到现有的：

```python
        self._set_translation_text(result.get('translated', ''))
        self._update_translation_height()
        if not self._source_dirty or not self.current_source_text():
            self._set_source_text(result.get('original', ''), mark_clean=True)
```

替换为：

```python
        paras = result.get('paragraphs', [])
        if self._para_mode and paras:
            self._set_translation_text(self._format_para_text(paras, 'translation'))
            if not self._source_dirty or not self.current_source_text():
                self._set_source_text(self._format_para_text(paras, 'text'), mark_clean=True)
        else:
            self._set_translation_text(result.get('translated', ''))
            if not self._source_dirty or not self.current_source_text():
                self._set_source_text(result.get('original', ''), mark_clean=True)
        self._update_translation_height()
        self._update_para_button()
```

- [ ] **Step 5: 验证编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from ui.result_bar import ResultBar; print('OK')"
```

- [ ] **Step 6: 运行全量测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py -x
```

预期：全部 PASSED

- [ ] **Step 7: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/ui/result_bar.py && git commit -m "feat: add para mode button and paragraph display logic to result_bar"
```

---

## Chunk 5: 信号连接与收尾

### Task 8: controller.py 中连接 settings_saved 信号

**Files:**
- Modify: `src/core/controller.py`

- [ ] **Step 1: 在 `_show_settings` 中追加信号连接**

在 `src/core/controller.py` 的 `_show_settings` 方法中，找到（约第 595-599 行）已有的 `settings_saved` 连接列表：

```python
            self._settings_win.settings_saved.connect(self.router.reload)
            self._settings_win.settings_saved.connect(self.result_bar.refresh_opacity)
            self._settings_win.settings_saved.connect(self.result_bar.apply_settings)
            self._settings_win.settings_saved.connect(self._reload_hotkeys)
            self._settings_win.settings_saved.connect(self._refresh_overlay_font_styles)
```

在末尾追加：

```python
            self._settings_win.settings_saved.connect(self.result_bar.sync_para_mode_from_settings)
```

- [ ] **Step 2: 验证编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from core.controller import CoreController; print('OK')"
```

- [ ] **Step 3: 运行全量测试**

```bash
cd C:/Users/Administrator/my-todo && python -m pytest tests/ -v --ignore=tests/test_startup_compile.py --ignore=tests/test_startup_logging.py
```

预期：全部 PASSED

- [ ] **Step 4: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/core/controller.py && git commit -m "feat: connect settings_saved to result_bar.sync_para_mode_from_settings"
```

---

### Task 9: translation_box.py 新增 ¶ 分段按钮（低优先级）

**Files:**
- Modify: `src/ui/translation_box.py`

- [ ] **Step 1: 阅读 translation_box.py 的按钮区代码**

找到 `_btn_translate` 按钮的创建位置和 `_make_btn` 方法定义。

- [ ] **Step 2: 在 `_btn_translate` 之后添加 `_btn_para`**

```python
self._btn_para = self._make_btn("¶", "切换分段显示", self._on_toggle_para)
```

- [ ] **Step 3: 添加 `_on_toggle_para` 方法**

```python
def _on_toggle_para(self):
    # 暂无分段数据，仅切换 _para_mode 状态和按钮高亮
    self._para_mode = not getattr(self, '_para_mode', False)
    style_on  = self._btn_subtitle.property('active_style') or ''
    style_off = ''
    self._btn_para.setStyleSheet(style_on if self._para_mode else style_off)
```

- [ ] **Step 4: 验证编译**

```bash
cd C:/Users/Administrator/my-todo && python -c "from ui.translation_box import TranslationBox; print('OK')"
```

- [ ] **Step 5: 提交**

```bash
cd C:/Users/Administrator/my-todo && git add src/ui/translation_box.py && git commit -m "feat: add paragraph toggle button to translation box (low priority)"
```

---

## 人工验证清单

完成所有任务后，启动应用进行功能验证：

```bash
cd C:/Users/Administrator/my-todo && python src/main.py
```

1. **多段落翻译**：截取包含多个自然段的英文/中文文章图片，点击翻译后确认结果条出现 `[1] ... [2] ...` 分段编号，原文和译文均分段显示
2. **单段降级**：截取单行短文，确认不出现 `[1]` 编号，"分段 ▼" 按钮置灰
3. **切换按钮**：有多段结果时，点击"分段 ▲/▼"，实时在编号格式和整体格式之间切换
4. **设置同步**：打开设置 → 通用，取消勾选"自动识别段落"并保存，确认按钮置灰
5. **重新翻译不崩溃**：在原文框中手动修改文字，点击"重新翻译"，确认无异常
6. **覆盖翻译不受影响**：开启"覆盖翻译"模式，段落覆盖字幕仍正常工作

---

## 参考：关键文件与行号速查

| 文件 | 关键位置 |
|------|---------|
| `src/core/settings.py` | DEFAULTS 第 5-36 行 |
| `src/core/overlay_layout.py` | `_can_merge_lines` 第 66 行；`group_rows_into_paragraphs` 第 104 行 |
| `src/core/controller.py` | 模块级 `_normalize_ocr_payload` 第 18 行；`_on_ocr_done_for_rect` 第 306 行；`_on_ocr_done` 第 354 行；`_show_settings` 第 591 行；`_on_translate_done`（保留）第 643 行 |
| `src/ui/settings_window.py` | `_setup_ui` 通用 tab 第 43 行；`tabs.addTab(gen, '通用')` 第 120 行；`_load_values` 第 239 行；`_save` 第 301 行 |
| `src/ui/result_bar.py` | `__init__` 第 176 行；`_details_actions_widget` 第 480 行；`show_result` 第 1252 行 |
| `src/ui/translation_box.py` | 按钮创建区（需阅读后定位） |
