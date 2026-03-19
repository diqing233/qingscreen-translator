# 临时模式隐藏翻译条 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 切换到临时模式时弹出一次性提示，用户确认后最小化 result_bar，之后翻译结果自动以覆盖字幕形式显示在选区框下方。

**Architecture:** 在 `result_bar.py` 新增 `_TempModeHintDialog`，在 `_on_mode_btn_click` 切换到 temp 时触发提示；在 `controller.py` 的翻译完成回调中加条件判断，临时模式 + `temp_mode_hide_bar=true` 时绕过 result_bar 直接调用 `box.show_subtitle()`；在 `settings_window.py` 通用标签页新增复选框和重置提示按钮。

**Tech Stack:** Python 3.14, PyQt5 5.15.11, SettingsStore (JSON)

---

### Task 1: 新增设置项默认值 + 测试

**Files:**
- Modify: `tests/test_settings.py`
- Modify: `src/core/settings.py`

- [ ] **Step 1: 写失败测试**

```python
def test_temp_mode_defaults():
    store = make_store()
    assert store.get('temp_mode_hide_bar') is True
    assert store.get('temp_mode_hint_dismissed') is False
```

在 `tests/test_settings.py` 末尾追加此函数。

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest tests/test_settings.py::test_temp_mode_defaults -v
```

预期：FAIL（KeyError 或返回 None）

- [ ] **Step 3: 在 settings.py 加默认值**

找到 `SettingsStore` 的 `DEFAULTS` 字典（或等效位置），加入：

```python
'temp_mode_hide_bar': True,
'temp_mode_hint_dismissed': False,
```

- [ ] **Step 4: 运行确认通过**

```bash
python -m pytest tests/test_settings.py::test_temp_mode_defaults -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_settings.py src/core/settings.py
git commit -m "feat: add temp_mode_hide_bar and temp_mode_hint_dismissed settings"
```

---

### Task 2: 新增 `_TempModeHintDialog` + 测试

**Files:**
- Modify: `src/ui/result_bar.py`（在文件顶部附近的辅助类区域新增）
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_result_bar_toolbar.py` 末尾追加：

```python
def test_temp_mode_hint_dialog_ok(qtbot):
    from unittest.mock import MagicMock
    from ui.result_bar import _TempModeHintDialog
    settings = MagicMock()
    settings.get.side_effect = lambda k, d=None: {'temp_mode_hint_dismissed': False}.get(k, d)
    skin = {}
    dlg = _TempModeHintDialog(settings, skin)
    qtbot.addWidget(dlg)
    # 点"好的"后对话框关闭，hint_dismissed 不变
    dlg._btn_ok.click()
    assert not dlg.isVisible()
    settings.set.assert_not_called()

def test_temp_mode_hint_dialog_dismiss(qtbot):
    from unittest.mock import MagicMock
    from ui.result_bar import _TempModeHintDialog
    settings = MagicMock()
    settings.get.side_effect = lambda k, d=None: {'temp_mode_hint_dismissed': False}.get(k, d)
    skin = {}
    dlg = _TempModeHintDialog(settings, skin)
    qtbot.addWidget(dlg)
    # 点"不再提示"后写入 dismissed=True
    dlg._btn_dismiss.click()
    assert not dlg.isVisible()
    settings.set.assert_called_once_with('temp_mode_hint_dismissed', True)
```

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest tests/test_result_bar_toolbar.py::test_temp_mode_hint_dialog_ok tests/test_result_bar_toolbar.py::test_temp_mode_hint_dialog_dismiss -v
```

预期：FAIL（ImportError: cannot import _TempModeHintDialog）

- [ ] **Step 3: 实现 `_TempModeHintDialog`**

在 `src/ui/result_bar.py` 中，在 `_MinimizeProxy` 类之后插入：

```python
class _TempModeHintDialog(QWidget):
    """切换到临时模式时弹出的一次性提示。"""

    def __init__(self, settings, skin, parent=None):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._settings = settings
        self.setAttribute(Qt.WA_TranslucentBackground)

        bg   = skin.get('surface', '#1a1f2e')
        fg   = skin.get('text',    '#e8eaf0')
        acc  = skin.get('accent',  '#4a90e2')
        rad  = skin.get('radius',  8)

        container = QWidget(self)
        container.setObjectName('hint_container')
        container.setStyleSheet(
            f"#hint_container {{ background: {bg}; border-radius: {rad}px; }}"
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel('临时模式提示')
        title.setStyleSheet(f"color: {fg}; font-weight: bold; font-size: 13px; background: transparent;")
        layout.addWidget(title)

        body = QLabel(
            '翻译条将自动最小化，翻译结果会直接\n'
            '显示在选区框下方。\n\n'
            '按 Alt+Q 框选并翻译。'
        )
        body.setStyleSheet(f"color: {fg}; font-size: 12px; background: transparent;")
        layout.addWidget(body)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_dismiss = QPushButton('不再提示')
        self._btn_ok      = QPushButton('好的')
        for btn in (self._btn_dismiss, self._btn_ok):
            btn.setFixedHeight(26)
            btn.setStyleSheet(
                f"QPushButton {{ background: transparent; color: {fg}; border: 1px solid {acc}; "
                f"border-radius: 4px; padding: 0 12px; }}"
                f"QPushButton:hover {{ background: {acc}; color: #fff; }}"
            )
        btn_row.addStretch()
        btn_row.addWidget(self._btn_dismiss)
        btn_row.addWidget(self._btn_ok)
        layout.addLayout(btn_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(container)

        self._btn_ok.clicked.connect(self.close)
        self._btn_dismiss.clicked.connect(self._on_dismiss)

    def _on_dismiss(self):
        self._settings.set('temp_mode_hint_dismissed', True)
        self.close()
```

- [ ] **Step 4: 运行确认通过**

```bash
python -m pytest tests/test_result_bar_toolbar.py::test_temp_mode_hint_dialog_ok tests/test_result_bar_toolbar.py::test_temp_mode_hint_dialog_dismiss -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/ui/result_bar.py tests/test_result_bar_toolbar.py
git commit -m "feat: add _TempModeHintDialog"
```

---

### Task 3: 切换到临时模式时触发提示 + 最小化

**Files:**
- Modify: `src/ui/result_bar.py`（`_on_mode_btn_click` 方法，约第 1219 行）
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: 写失败测试**

```python
def test_switching_to_temp_shows_hint_when_not_dismissed(qtbot, monkeypatch):
    """切换到 temp 且 hint 未 dismissed 时，应弹出提示对话框。"""
    from unittest.mock import MagicMock, patch
    bar = make_bar()
    qtbot.addWidget(bar)
    bar._settings.set('temp_mode_hint_dismissed', False)
    bar._settings.set('temp_mode_hide_bar', True)

    shown = []
    with patch('ui.result_bar._TempModeHintDialog') as MockDlg:
        instance = MagicMock()
        MockDlg.return_value = instance
        bar._on_mode_btn_click('temp')
        assert MockDlg.called, "应创建 _TempModeHintDialog"

def test_switching_to_temp_no_hint_when_dismissed(qtbot, monkeypatch):
    """hint 已 dismissed 时，切换到 temp 不弹提示。"""
    from unittest.mock import patch
    bar = make_bar()
    qtbot.addWidget(bar)
    bar._settings.set('temp_mode_hint_dismissed', True)
    bar._settings.set('temp_mode_hide_bar', True)

    with patch('ui.result_bar._TempModeHintDialog') as MockDlg:
        bar._on_mode_btn_click('temp')
        assert not MockDlg.called
```

注意：`make_bar()` 是该测试文件中已有的辅助函数，请确认其存在；若不存在，参考文件中其他测试的初始化方式。

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest tests/test_result_bar_toolbar.py::test_switching_to_temp_shows_hint_when_not_dismissed tests/test_result_bar_toolbar.py::test_switching_to_temp_no_hint_when_dismissed -v
```

预期：FAIL

- [ ] **Step 3: 修改 `_on_mode_btn_click`**

在 `src/ui/result_bar.py` 的 `_on_mode_btn_click` 方法（约第 1219 行）中，在 `self.box_mode_changed.emit(key)` 之后追加：

```python
        if key == 'temp' and self._settings.get('temp_mode_hide_bar', True):
            if not self._settings.get('temp_mode_hint_dismissed', False):
                self._show_temp_mode_hint()
            elif not self._minimized:
                self._toggle_minimize()
```

然后在 `ResultBar` 类中新增方法：

```python
    def _show_temp_mode_hint(self):
        skin = get_skin(self._settings.get('skin', 'deep_space'),
                        self._settings.get('button_style_variant', 'calm'))
        dlg = _TempModeHintDialog(self._settings, skin, parent=self)
        dlg.setAttribute(Qt.WA_DeleteOnClose)
        # 对话框关闭后最小化
        dlg.destroyed.connect(lambda: self._toggle_minimize() if not self._minimized else None)
        # 居中显示在 result_bar 附近
        dlg.adjustSize()
        pos = self.geometry().center() - dlg.rect().center()
        dlg.move(pos)
        dlg.show()
```

- [ ] **Step 4: 运行确认通过**

```bash
python -m pytest tests/test_result_bar_toolbar.py::test_switching_to_temp_shows_hint_when_not_dismissed tests/test_result_bar_toolbar.py::test_switching_to_temp_no_hint_when_dismissed -v
```

预期：PASS

- [ ] **Step 5: 提交**

```bash
git add src/ui/result_bar.py tests/test_result_bar_toolbar.py
git commit -m "feat: show hint and minimize on switch to temp mode"
```

---

### Task 4: controller 翻译完成时绕过 result_bar

**Files:**
- Modify: `src/core/controller.py`（翻译完成回调，约第 695-708 行）
- Modify: `tests/test_controller_normalize.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_controller_normalize.py` 末尾追加：

```python
def test_temp_hide_bar_routes_to_subtitle(qtbot):
    """临时模式 + temp_mode_hide_bar=True 时，翻译结果走 box.show_subtitle，不调用 result_bar.show_result。"""
    from unittest.mock import MagicMock, patch
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from core.controller import Controller

    ctrl = Controller.__new__(Controller)
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}

    mock_settings = MagicMock()
    mock_settings.get.side_effect = lambda k, d=None: {
        'temp_mode_hide_bar': True,
    }.get(k, d)
    ctrl.settings = mock_settings

    mock_bar = MagicMock()
    ctrl.result_bar = mock_bar

    mock_box = MagicMock()
    mock_box.mode = 'temp'
    mock_box._subtitle_mode = 'off'
    mock_box._last_ocr_paragraphs = []
    mock_box._last_paragraph_translations = []
    mock_box._pending_auto = False
    mock_box._pending_para_texts = []

    result = {'translated': '你好', 'original': 'hello', 'paragraphs': []}

    # 调用翻译完成的核心逻辑（_dispatch_translation_result）
    ctrl._dispatch_translation_result(result, mock_box)

    mock_box.show_subtitle.assert_called_once_with('你好')
    mock_bar.show_result.assert_not_called()

def test_temp_hide_bar_no_box_silent(qtbot):
    """临时模式 + temp_mode_hide_bar=True + box=None 时，静默跳过。"""
    from unittest.mock import MagicMock
    from core.controller import Controller

    ctrl = Controller.__new__(Controller)
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}

    mock_settings = MagicMock()
    mock_settings.get.side_effect = lambda k, d=None: {
        'temp_mode_hide_bar': True,
    }.get(k, d)
    ctrl.settings = mock_settings

    mock_bar = MagicMock()
    ctrl.result_bar = mock_bar

    result = {'translated': '你好', 'original': 'hello', 'paragraphs': []}
    ctrl._dispatch_translation_result(result, None)

    mock_bar.show_result.assert_not_called()
```

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest tests/test_controller_normalize.py::test_temp_hide_bar_routes_to_subtitle tests/test_controller_normalize.py::test_temp_hide_bar_no_box_silent -v
```

预期：FAIL（AttributeError: _dispatch_translation_result）

- [ ] **Step 3: 重构 controller.py 翻译完成逻辑**

在 `src/core/controller.py` 中，将约第 695-714 行的翻译完成分发逻辑提取为独立方法 `_dispatch_translation_result`，并加入条件判断：

```python
    def _dispatch_translation_result(self, result: dict, box):
        """翻译完成后分发结果到 result_bar 或 translation_box。"""
        hide_bar = (
            self._box_mode == 'temp'
            and self.settings.get('temp_mode_hide_bar', True)
        )

        if hide_bar:
            if box is not None:
                box.set_overlay_mode('below')
                translated = result.get('translated', '')
                if translated:
                    box.show_subtitle(translated)
            # box 为 None 时静默跳过
        else:
            if box is not None and self._box_mode == 'multi':
                self._multi_results[box.box_id] = result
                self.result_bar.show_multi_results(list(self._multi_results.values()))
            else:
                self.result_bar.show_result(result)

            translated = result.get('translated', '')
            if box is not None:
                setattr(box, '_last_translation', translated)
                overlay_mode = getattr(box, '_subtitle_mode', 'off')
                if overlay_mode == 'over_para' and getattr(box, '_last_ocr_paragraphs', []) and not getattr(box, '_last_paragraph_translations', []):
                    self._run_paragraph_translate(box)
                if translated and (getattr(box, '_subtitle_active', False) or overlay_mode != 'off'):
                    box.show_subtitle(translated)

        if box is not None:
            if box.mode == 'temp':
                box.start_dismiss_timer()
            elif getattr(box, '_pending_auto', False):
                box._pending_auto = False
                box.start_auto_translate()
```

然后将原来第 695-714 行替换为：

```python
        self._dispatch_translation_result(result, box)
```

- [ ] **Step 4: 运行确认通过**

```bash
python -m pytest tests/test_controller_normalize.py::test_temp_hide_bar_routes_to_subtitle tests/test_controller_normalize.py::test_temp_hide_bar_no_box_silent -v
```

预期：PASS

- [ ] **Step 5: 运行全量测试确认无回归**

```bash
python -m pytest -q
```

预期：全部通过（或与改动前相同数量通过）

- [ ] **Step 6: 提交**

```bash
git add src/core/controller.py tests/test_controller_normalize.py
git commit -m "feat: route temp mode translation to subtitle overlay"
```

---

### Task 5: 设置界面新增复选框 + 重置提示按钮

**Files:**
- Modify: `src/ui/settings_window.py`（通用标签页，约第 182-196 行的 checkbox 区域之后）
- Modify: `tests/test_settings.py`

- [ ] **Step 1: 写失败测试**

在 `tests/test_settings.py` 末尾追加：

```python
def test_settings_window_has_temp_hide_bar_checkbox():
    """设置窗口通用标签页应包含 temp_mode_hide_bar 复选框。"""
    from PyQt5.QtWidgets import QCheckBox
    from ui.settings_window import SettingsWindow
    store = make_store()
    win = SettingsWindow(store)
    assert hasattr(win, '_chk_temp_hide_bar'), "应有 _chk_temp_hide_bar 属性"
    assert isinstance(win._chk_temp_hide_bar, QCheckBox)
    win.close()
```

- [ ] **Step 2: 运行确认失败**

```bash
python -m pytest tests/test_settings.py::test_settings_window_has_temp_hide_bar_checkbox -v
```

预期：FAIL（AttributeError）

- [ ] **Step 3: 在 settings_window.py 通用标签页加控件**

在 `src/ui/settings_window.py` 中，找到 `self._para_check.stateChanged.connect(...)` 之后（约第 193 行），在 `gen_layout.addWidget(form_widget)` 之前插入：

```python
        # 临时模式行为分组
        temp_group = QGroupBox('临时模式')
        temp_layout = QVBoxLayout(temp_group)
        temp_layout.setSpacing(6)

        self._chk_temp_hide_bar = QCheckBox('临时模式下隐藏翻译条（翻译结果显示在选区框下方）')
        temp_layout.addWidget(self._chk_temp_hide_bar)

        hint_row = QHBoxLayout()
        hint_row.setContentsMargins(20, 0, 0, 0)
        self._btn_reset_hint = QPushButton('重置提示')
        self._btn_reset_hint.setFlat(True)
        self._btn_reset_hint.setStyleSheet(
            'QPushButton { color: #888; font-size: 11px; text-decoration: underline; border: none; }'
            'QPushButton:hover { color: #aaa; }'
            'QPushButton:disabled { color: #555; text-decoration: none; }'
        )
        self._btn_reset_hint.setFixedHeight(18)
        hint_row.addWidget(self._btn_reset_hint)
        hint_row.addStretch()
        temp_layout.addLayout(hint_row)

        self._btn_reset_hint.clicked.connect(self._on_reset_hint)
        gen_layout.addWidget(temp_group)
```

然后在 `SettingsWindow` 类中新增方法（放在 `_load_values` 附近）：

```python
    def _on_reset_hint(self):
        self._settings.set('temp_mode_hint_dismissed', False)
        self._btn_reset_hint.setEnabled(False)
```

在 `_load_values` 方法中追加：

```python
        self._chk_temp_hide_bar.setChecked(self._settings.get('temp_mode_hide_bar', True))
        dismissed = self._settings.get('temp_mode_hint_dismissed', False)
        self._btn_reset_hint.setEnabled(dismissed)
        self._chk_temp_hide_bar.stateChanged.connect(
            lambda state: self._settings.set('temp_mode_hide_bar', bool(state))
        )
```

- [ ] **Step 4: 运行确认通过**

```bash
python -m pytest tests/test_settings.py::test_settings_window_has_temp_hide_bar_checkbox -v
```

预期：PASS

- [ ] **Step 5: 运行全量测试**

```bash
python -m pytest -q
```

预期：全部通过

- [ ] **Step 6: 提交**

```bash
git add src/ui/settings_window.py tests/test_settings.py
git commit -m "feat: add temp mode hide bar checkbox and reset hint button in settings"
```

---

### Task 6: 启动时检查初始模式

**Files:**
- Modify: `src/ui/result_bar.py`（`__init__` 或 `showEvent`）

- [ ] **Step 1: 在 ResultBar 初始化时检查初始模式**

在 `src/ui/result_bar.py` 的 `ResultBar.showEvent` 方法中（或 `__init__` 末尾），追加一次性检查：

```python
    def showEvent(self, event):
        super().showEvent(event)
        if not self._startup_hint_checked:
            self._startup_hint_checked = True
            if (self._box_mode == 'temp'
                    and self._settings.get('temp_mode_hide_bar', True)
                    and not self._settings.get('temp_mode_hint_dismissed', False)):
                QTimer.singleShot(300, self._show_temp_mode_hint)
```

在 `ResultBar.__init__` 中初始化标志：

```python
        self._startup_hint_checked = False
```

- [ ] **Step 2: 运行全量测试**

```bash
python -m pytest -q
```

预期：全部通过

- [ ] **Step 3: 提交**

```bash
git add src/ui/result_bar.py
git commit -m "feat: show temp mode hint on startup if initial mode is temp"
```
