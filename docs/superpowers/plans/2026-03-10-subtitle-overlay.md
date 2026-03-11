# 字幕覆盖翻译 + 固定模式修复 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在每个翻译框上加"字幕覆盖"按钮，点击后在框正下方显示译文字幕条（双语字幕效果）；同时修复"固定"模式按钮对已存在框不生效的 bug。

**Architecture:** 采用独立浮动子窗口方案——TranslationBox 懒创建一个 `_subtitle_win`（Qt.Tool 窗口），定位在 box 下方。box 移动/缩放/隐藏/关闭时同步字幕窗口。固定按钮修复在 controller 的 `_on_box_mode_changed` 中补充对现有框的 set_mode 调用。

**Tech Stack:** Python 3.x, PyQt5 5.15.x

---

## Chunk 1: 固定按钮 Bug 修复

### Task 1: 修复 _on_box_mode_changed

**Files:**
- Modify: `src/core/controller.py:156-159`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_fixed_mode.py`：

```python
# tests/test_fixed_mode.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

def _make_box(mode='temp'):
    box = MagicMock()
    box.mode = mode
    return box

def test_switching_to_fixed_stops_existing_temp_boxes():
    """切换到固定模式时，已存在的临时框应该被改为 fixed（停止 dismiss timer）"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}

    box1 = _make_box('temp')
    box2 = _make_box('temp')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_box_mode_changed('fixed')

    box1.set_mode.assert_called_once_with('fixed')
    box2.set_mode.assert_called_once_with('fixed')

def test_switching_to_temp_does_not_change_existing_boxes():
    """切换回临时模式时，不强制改变已有框的模式"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'fixed'
    ctrl._multi_results = {}

    box1 = _make_box('fixed')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1}

    ctrl._on_box_mode_changed('temp')

    box1.set_mode.assert_not_called()
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd c:/Users/Administrator/my-todo
python -m pytest tests/test_fixed_mode.py -v
```

Expected: `FAILED test_switching_to_fixed_stops_existing_temp_boxes` — `set_mode` not called.

- [ ] **Step 3: 修改 controller.py**

打开 `src/core/controller.py`，找到 `_on_box_mode_changed`（约第 156 行），改为：

```python
def _on_box_mode_changed(self, mode: str):
    self._box_mode = mode
    if mode != 'multi':
        self._multi_results.clear()
    if mode == 'fixed':
        for box in self.box_manager._boxes.values():
            box.set_mode('fixed')
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python -m pytest tests/test_fixed_mode.py -v
```

Expected: 2 tests PASSED.

- [ ] **Step 5: 运行全量测试，确认无回归**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED（共 10 个测试：原有 8 个 + 本 chunk 新增 2 个）。

- [ ] **Step 6: 提交**

```bash
git add src/core/controller.py tests/test_fixed_mode.py
git commit -m "fix: switching to fixed mode now applies to existing temp boxes"
```

---

## Chunk 2: TranslationBox 字幕窗口

### Task 2: 新增 SubtitleWindow 及 TranslationBox 按钮

**Files:**
- Modify: `src/ui/translation_box.py`

- [ ] **Step 1: 写失败测试**

新建 `tests/test_subtitle.py`：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

_app = QApplication.instance() or QApplication(sys.argv)

def _make_box():
    from core.settings import SettingsStore
    settings = MagicMock()
    settings.get.side_effect = lambda k, d=None: d
    from ui.translation_box import TranslationBox
    box = TranslationBox(QRect(100, 100, 200, 80), box_id=1, settings=settings)
    return box

def test_subtitle_win_initially_none():
    box = _make_box()
    assert box._subtitle_win is None
    assert box._subtitle_active is False

def test_show_subtitle_creates_win_and_shows():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    assert box._subtitle_win is not None
    assert box._subtitle_win.isVisible()
    assert box._subtitle_active is True

def test_hide_subtitle_hides_win():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    box.hide_subtitle()
    assert not box._subtitle_win.isVisible()
    assert box._subtitle_active is False

def test_subtitle_position_below_box():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    sw = box._subtitle_win
    # 字幕窗口 x 应与 box 相同，y 应为 box.y() + box.height()
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()
    assert sw.width() == box.width()

def test_subtitle_follows_box_on_move():
    box = _make_box()
    box.show()
    box.show_subtitle("移动测试")
    box.move(300, 200)
    # moveEvent 触发后字幕窗口应更新位置
    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()

def test_toggle_subtitle():
    box = _make_box()
    box.show()
    box._last_translation = "测试译文"
    box._on_toggle_subtitle()
    assert box._subtitle_active is True
    box._on_toggle_subtitle()
    assert box._subtitle_active is False
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
python -m pytest tests/test_subtitle.py -v
```

Expected: AttributeError / ImportError — `_subtitle_win` 不存在。

- [ ] **Step 3: 修改 translation_box.py — 初始化新状态**

在 `__init__` 中，`self._overlay_label = None` 后追加：

```python
self._subtitle_win = None
self._subtitle_active = False
self._last_translation = ''
```

- [ ] **Step 4: 修改 _setup_ui — 加入 ⊞ 按钮**

在 `_setup_ui` 中，`self._btn_close` 定义之前加入：

```python
self._btn_subtitle = self._make_btn('⊞', '在框下方显示译文字幕', self._on_toggle_subtitle)
```

然后在 `for btn in [...]` 列表中加入 `self._btn_subtitle`：

```python
for btn in [self._btn_translate, self._btn_pin, self._btn_subtitle,
            self._btn_hide, self._btn_close]:
    btn_layout.addWidget(btn)
```

- [ ] **Step 5: 新增字幕相关方法**

在 `hide_translation_overlay` 方法之后、`_on_dismiss_timeout` 之前追加：

```python
def _create_subtitle_win(self):
    from PyQt5.QtWidgets import QLabel
    win = QLabel()
    win.setWindowFlags(
        Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
    )
    win.setAttribute(Qt.WA_TranslucentBackground)
    win.setWordWrap(True)
    win.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    win.setStyleSheet('''
        QLabel {
            background: rgba(15, 15, 24, 210);
            color: #f0f0f0;
            font-size: 13px;
            padding: 6px 12px;
            border-top: 1px solid rgba(80, 140, 255, 100);
            border-radius: 0px 0px 6px 6px;
        }
    ''')
    return win

def _subtitle_geometry(self):
    """计算字幕窗口应在的位置（box 正下方，同宽）"""
    return (self.x(), self.y() + self.height(), self.width())

def show_subtitle(self, text: str):
    """在框正下方显示译文字幕条。"""
    self._last_translation = text
    if self._subtitle_win is None:
        self._subtitle_win = self._create_subtitle_win()
    self._subtitle_win.setText(text)
    x, y, w = self._subtitle_geometry()
    self._subtitle_win.setFixedWidth(w)
    self._subtitle_win.adjustSize()
    self._subtitle_win.move(x, y)
    self._subtitle_win.show()
    self._subtitle_win.raise_()
    self._subtitle_active = True
    self._btn_subtitle.setStyleSheet('''
        QPushButton {
            background: rgba(80,140,255,180); color: white;
            border: none; border-radius: 3px; font-size: 11px;
        }
        QPushButton:hover { background: rgba(100,160,255,200); }
    ''')

def hide_subtitle(self):
    """隐藏译文字幕条。"""
    if self._subtitle_win is not None:
        self._subtitle_win.hide()
    self._subtitle_active = False
    self._btn_subtitle.setStyleSheet('''
        QPushButton {
            background: rgba(30,30,40,180); color: white;
            border: none; border-radius: 3px; font-size: 11px;
        }
        QPushButton:hover { background: rgba(70,70,100,220); }
    ''')

def _on_toggle_subtitle(self):
    if self._subtitle_active:
        self.hide_subtitle()
    else:
        self.show_subtitle(self._last_translation)
```

- [ ] **Step 6: 重写 moveEvent，字幕窗口跟随**

在 `mouseMoveEvent` 之后追加：

```python
def moveEvent(self, event):
    super().moveEvent(event)
    if self._subtitle_win is not None and self._subtitle_win.isVisible():
        x, y, w = self._subtitle_geometry()
        self._subtitle_win.move(x, y)
```

- [ ] **Step 7: 更新已有 resizeEvent，字幕窗口同步宽度和位置**

找到现有 `resizeEvent`（最后几行），改为以下内容（不再包含 `_overlay_label` 逻辑，因为它将在 Step 10 被删除）：

```python
def resizeEvent(self, event):
    super().resizeEvent(event)
    if self._subtitle_win is not None and self._subtitle_win.isVisible():
        x, y, w = self._subtitle_geometry()
        self._subtitle_win.setFixedWidth(w)
        self._subtitle_win.adjustSize()
        self._subtitle_win.move(x, y)
```

- [ ] **Step 8: 重写 hideEvent，隐藏字幕窗口**

在 `resizeEvent` 之后追加：

```python
def hideEvent(self, event):
    super().hideEvent(event)
    if self._subtitle_win is not None:
        self._subtitle_win.hide()

def showEvent(self, event):
    super().showEvent(event)
    if self._subtitle_active and self._subtitle_win is not None:
        self._subtitle_win.show()
```

- [ ] **Step 9: 字幕窗口在 box 被删除时销毁**

在 `translation_box.py` 中重写 `closeEvent`（`deleteLater` 前触发，保证字幕窗口被回收）：

```python
def closeEvent(self, event):
    if self._subtitle_win is not None:
        self._subtitle_win.close()
        self._subtitle_win = None
    super().closeEvent(event)
```

同时在 `test_subtitle.py` 末尾追加测试，确保 closeEvent 清理字幕：

```python
def test_close_event_destroys_subtitle_win():
    box = _make_box()
    box.show()
    box.show_subtitle("关闭测试")
    assert box._subtitle_win is not None
    box.close()
    assert box._subtitle_win is None
```

- [ ] **Step 10: 删除已被替代的旧 overlay 方法**

在 `translation_box.py` 中找到并删除以下内容（已被字幕方案替代，保留会成为死代码）：
- `show_translation_overlay(self, text: str)` 方法（约第 114-133 行）
- `hide_translation_overlay(self)` 方法（约第 135-138 行）
- `__init__` 中的 `self._overlay_label = None`（约第 22 行）

注意：Step 7 已经写出了不含 `_overlay_label` 的 `resizeEvent`，无需再修改 `resizeEvent`。

- [ ] **Step 11: 运行字幕测试验证删除后无断裂**

```bash
python -m pytest tests/test_subtitle.py -v
```

Expected: 7 tests PASSED（含新增的 closeEvent 测试）。

- [ ] **Step 12: 运行全量测试**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED（共 17 个：原有 8 + Chunk1 新增 2 + Chunk2 新增 7）。

- [ ] **Step 13: 提交**

```bash
git add src/ui/translation_box.py tests/test_subtitle.py
git commit -m "feat: add subtitle overlay button to TranslationBox (bilingual subtitle mode)"
```

---

## Chunk 3: Controller 联动 + 全局覆盖按钮统一

### Task 3: 翻译完成后刷新字幕 + 全局覆盖按钮改用字幕

**Files:**
- Modify: `src/core/controller.py:279-301`, `src/core/controller.py:324-342`

- [ ] **Step 1: 修改 _on_translate_done — 翻译完成时刷新字幕**

在 `controller.py` 的 `_on_translate_done` 中（约第 279 行），`self.result_bar.show_result(result)` 之后追加：

```python
# 若该框字幕已激活，刷新字幕内容
translated = result.get('translated', '')
if getattr(box, '_subtitle_active', False):
    box.show_subtitle(translated)
```

完整方法如下：

```python
def _on_translate_done(self, result: dict, box):
    try:
        self.history.add(
            result.get('original', ''),
            result.get('translated', ''),
            result.get('source_lang', ''),
            result.get('target_lang', ''),
            result.get('backend', ''),
        )
    except Exception as e:
        logger.warning(f'History save failed: {e}')

    if self._box_mode == 'multi':
        self._multi_results[box.box_id] = result
        self.result_bar.show_multi_results(list(self._multi_results.values()))
    else:
        self.result_bar.show_result(result)

    # 若该框字幕已激活，刷新字幕内容
    translated = result.get('translated', '')
    if getattr(box, '_subtitle_active', False):
        box.show_subtitle(translated)

    if box.mode == 'temp':
        box.start_dismiss_timer()
    elif getattr(box, '_pending_auto', False):
        # 以下两行保留自原有实现，不作修改
        box._pending_auto = False
        box.start_auto_translate()
```

- [ ] **Step 2: 修改 _on_overlay_requested — 改用字幕方法**

将 `_on_overlay_requested`（约第 324 行）改为：

```python
def _on_overlay_requested(self, text: str):
    """切换所有翻译框的字幕条显示。"""
    boxes = list(self.box_manager._boxes.values())
    if not boxes:
        return
    any_subtitle = any(getattr(b, '_subtitle_active', False) for b in boxes)
    for box in boxes:
        if any_subtitle:
            box.hide_subtitle()
        else:
            # 多框模式：各框显示各自的译文
            result = self._multi_results.get(box.box_id)
            t = result.get('translated', '') if result else text
            box.show_subtitle(t)
```

- [ ] **Step 3: 写联动测试**

- [ ] 首先确认 `tests/test_fixed_mode.py` 存在且包含 Chunk 1 的两个测试：

```bash
python -m pytest tests/test_fixed_mode.py -v
```

Expected: 2 tests PASSED（Chunk 1 的测试）。

然后追加以下测试到 `tests/test_fixed_mode.py`：

```python
def test_translate_done_refreshes_active_subtitle():
    """翻译完成时，若字幕已激活，应刷新字幕内容"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_active = True
    box._pending_auto = False

    result = {'original': 'hello', 'translated': '你好', 'source_lang': 'en',
              'target_lang': 'zh-CN', 'backend': 'google'}
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('你好')

def test_translate_done_no_subtitle_refresh_when_inactive():
    """字幕未激活时，翻译完成不调用 show_subtitle"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_active = False
    box._pending_auto = False

    result = {'original': 'hello', 'translated': '你好', 'source_lang': 'en',
              'target_lang': 'zh-CN', 'backend': 'google'}
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_not_called()

def test_overlay_requested_shows_all_when_none_active():
    """无字幕激活时，全局切换应对所有框调用 show_subtitle，传入 text 参数（无 _multi_results 时）"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {}

    box1 = MagicMock()
    box1._subtitle_active = False
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('译文')

    box1.show_subtitle.assert_called_once_with('译文')
    box2.show_subtitle.assert_called_once_with('译文')

def test_overlay_requested_uses_multi_results_when_available():
    """多框模式下，show_subtitle 应使用各框自己的 _multi_results 译文"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {1: {'translated': '框一译文'}, 2: {'translated': '框二译文'}}

    box1 = MagicMock()
    box1._subtitle_active = False
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('fallback')

    box1.show_subtitle.assert_called_once_with('框一译文')
    box2.show_subtitle.assert_called_once_with('框二译文')

def test_overlay_requested_hides_all_when_any_active():
    """有字幕激活时，全局切换应对所有框调用 hide_subtitle"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {}

    box1 = MagicMock()
    box1._subtitle_active = True
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('译文')

    box1.hide_subtitle.assert_called_once()
    box2.hide_subtitle.assert_called_once()
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
python -m pytest tests/test_fixed_mode.py tests/test_subtitle.py -v
```

Expected: 共 14 个 PASSED（Chunk1 2 个 + Chunk3 新增 5 个 + Chunk2 7 个）。

- [ ] **Step 5: 全量测试**

```bash
python -m pytest tests/ -v
```

Expected: 全部 PASSED（共 22 个：原有 8 + Chunk1 2 + Chunk2 7 + Chunk3 5）。

- [ ] **Step 6: 提交**

```bash
git add src/core/controller.py tests/test_fixed_mode.py
git commit -m "feat: refresh subtitle on translate done; unify global overlay to subtitle"
```

---

## 最终验证

- [ ] 手动运行应用

```bash
cd c:/Users/Administrator/my-todo
python src/main.py
```

- [ ] 验证字幕功能
  1. Alt+Q 框选一段文字 → 等待翻译
  2. 悬停在框上 → 看到 ⊞ 按钮
  3. 点击 ⊞ → 框正下方出现字幕条，原文区域完全可见
  4. 拖动框 → 字幕条跟随
  5. 调整框大小 → 字幕宽度同步
  6. 再次点 ⊞ → 字幕消失
  7. 关闭框 → 字幕窗口也消失
  8. result bar 的 ⊞ → 所有框字幕同步切换

- [ ] 验证固定模式修复
  1. 框选一段文字（此时处于临时模式） → 框出现
  2. 点击结果条"固定"按钮 → 框应立即不再自动消失
  3. 直接选"固定"模式再框选 → 新框也不自动消失
