# 关闭按钮行为与托盘恢复 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让主结果条的 `✕` 支持“首次询问并可记住选择、可在设置中修改、支持托盘恢复主窗口”的完整关闭行为。

**Architecture:** 由 `ResultBar` 发出关闭请求，`CoreController` 统一决定询问、托盘或退出，`SystemTray` 负责恢复入口，`SettingsStore / SettingsWindow` 负责持久化。测试先覆盖设置和控制器分支，再补托盘入口，最后做最小实现通过全部测试。

**Tech Stack:** Python 3.x, PyQt5 5.15.x, pytest, unittest.mock

---

## Chunk 1: 设置模型

### Task 1: 为关闭行为增加默认值和持久化测试

**Files:**
- Modify: `src/core/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: 写失败测试，覆盖默认值**

在 `tests/test_settings.py` 追加：

```python
def test_default_close_button_behavior_is_ask():
    store = make_store()
    assert store.get('close_button_behavior') == 'ask'
```

- [ ] **Step 2: 运行单测，确认它先失败**

Run: `python -m pytest tests/test_settings.py::test_default_close_button_behavior_is_ask -v`

Expected: FAIL，提示默认值不存在或不等于 `ask`

- [ ] **Step 3: 最小实现默认值**

在 `src/core/settings.py` 的 `DEFAULTS` 中新增：

```python
'close_button_behavior': 'ask',
```

- [ ] **Step 4: 重跑单测，确认转绿**

Run: `python -m pytest tests/test_settings.py::test_default_close_button_behavior_is_ask -v`

Expected: PASS

- [ ] **Step 5: 写失败测试，覆盖持久化**

在 `tests/test_settings.py` 追加：

```python
def test_close_button_behavior_persists():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('close_button_behavior', 'tray')
    store2 = SettingsStore(f.name)
    assert store2.get('close_button_behavior') == 'tray'
```

- [ ] **Step 6: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_settings.py::test_close_button_behavior_persists -v`

Expected: FAIL，如果默认值或保存逻辑未覆盖该字段

- [ ] **Step 7: 不改代码，直接重跑确认现有持久化已足够**

Run: `python -m pytest tests/test_settings.py::test_close_button_behavior_persists -v`

Expected: PASS，说明 `SettingsStore.set()` 已支持该字段

- [ ] **Step 8: 运行设置相关测试，确认没有回归**

Run: `python -m pytest tests/test_settings.py -v`

Expected: 全部 PASS

- [ ] **Step 9: 提交这一小步**

```bash
git add tests/test_settings.py src/core/settings.py
git commit -m "test: cover close button behavior settings"
```

---

## Chunk 2: 关闭请求与托盘入口

### Task 2: 先写控制器测试，定义关闭策略分支

**Files:**
- Create: `tests/test_close_behavior.py`
- Modify: `src/core/controller.py`
- Modify: `src/ui/result_bar.py`
- Modify: `src/ui/tray.py`

- [ ] **Step 1: 写失败测试，定义 `tray` 模式**

创建 `tests/test_close_behavior.py`：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock

def make_controller():
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl.app = MagicMock()
    ctrl.settings = MagicMock()
    ctrl.result_bar = MagicMock()
    ctrl.tray = MagicMock()
    return ctrl

def test_close_request_hides_to_tray_when_behavior_is_tray():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'tray'

    CoreController._handle_result_bar_close(ctrl)

    ctrl.result_bar.hide.assert_called_once()
    ctrl.app.quit.assert_not_called()
```

- [ ] **Step 2: 运行单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_hides_to_tray_when_behavior_is_tray -v`

Expected: FAIL，提示 `_handle_result_bar_close` 尚不存在

- [ ] **Step 3: 写失败测试，定义 `quit` 模式**

在同文件追加：

```python
def test_close_request_quits_when_behavior_is_quit():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'quit'

    CoreController._handle_result_bar_close(ctrl)

    ctrl.app.quit.assert_called_once()
```

- [ ] **Step 4: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_quits_when_behavior_is_quit -v`

Expected: FAIL

- [ ] **Step 5: 写失败测试，定义“询问并记住为 tray”**

继续追加：

```python
def test_close_request_asks_and_remembers_tray_choice():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior = MagicMock(return_value=('tray', True))

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_called_once_with('close_button_behavior', 'tray')
    ctrl.result_bar.hide.assert_called_once()
```

- [ ] **Step 6: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_asks_and_remembers_tray_choice -v`

Expected: FAIL

- [ ] **Step 7: 写失败测试，定义“询问但不记住”**

继续追加：

```python
def test_close_request_asks_without_remembering_keeps_ask_setting():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior = MagicMock(return_value=('tray', False))

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_not_called()
    ctrl.result_bar.hide.assert_called_once()
```

- [ ] **Step 8: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_asks_without_remembering_keeps_ask_setting -v`

Expected: FAIL

- [ ] **Step 9: 最小实现控制器分支**

在 `src/core/controller.py`：

- 连接 `self.result_bar.close_requested.connect(self._handle_result_bar_close)`
- 新增 `_handle_result_bar_close()`
- 新增 `_send_main_window_to_tray()`
- 新增 `_restore_main_window()`
- 新增 `_ask_close_behavior()`

实现原则：

- `ask` 时调用 `_ask_close_behavior()`，返回 `(action, remember)`
- `action == 'tray'` 时隐藏结果条
- `action == 'quit'` 时调用 `self.app.quit()`
- `remember` 为真时写回 `close_button_behavior`
- `action is None` 时直接返回

- [ ] **Step 10: 在 `ResultBar` 暴露关闭请求**

在 `src/ui/result_bar.py`：

- 增加 `close_requested = pyqtSignal()`
- 将 `self._btn_close` 的回调从 `self.hide` 改为 `self.close_requested.emit`

- [ ] **Step 11: 运行 4 个控制器单测，确认转绿**

Run: `python -m pytest tests/test_close_behavior.py -v`

Expected: 至少上述 4 个测试 PASS

- [ ] **Step 12: 写失败测试，定义托盘恢复入口**

在 `tests/test_close_behavior.py` 追加：

```python
def test_restore_main_window_shows_and_activates_result_bar():
    from core.controller import CoreController
    ctrl = make_controller()

    CoreController._restore_main_window(ctrl)

    ctrl.result_bar.show.assert_called_once()
    ctrl.result_bar.raise_.assert_called_once()
    ctrl.result_bar.activateWindow.assert_called_once()
```

- [ ] **Step 13: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_restore_main_window_shows_and_activates_result_bar -v`

Expected: FAIL

- [ ] **Step 14: 最小实现恢复逻辑**

在 `src/core/controller.py` 的 `_restore_main_window()` 中实现：

```python
self.result_bar.show()
self.result_bar.raise_()
self.result_bar.activateWindow()
```

- [ ] **Step 15: 为托盘增加显示主窗口信号**

在 `src/ui/tray.py`：

- 增加 `show_main_requested = pyqtSignal()`
- 菜单新增 `显示主窗口`
- `_on_activated()` 改为在单击或双击时发出 `show_main_requested`

- [ ] **Step 16: 在控制器中接上托盘恢复信号**

在 `src/core/controller.py`：

```python
self.tray.show_main_requested.connect(self._restore_main_window)
```

- [ ] **Step 17: 写失败测试，校验托盘菜单项存在**

在 `tests/test_close_behavior.py` 追加一个 `QApplication` 级测试：

```python
from PyQt5.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

def test_tray_menu_contains_show_main_action():
    from ui.tray import SystemTray
    tray = SystemTray()
    labels = [action.text() for action in tray.contextMenu().actions()]
    assert '显示主窗口' in labels
```

- [ ] **Step 18: 运行该单测，确认它先失败，再随代码转绿**

Run: `python -m pytest tests/test_close_behavior.py::test_tray_menu_contains_show_main_action -v`

Expected: 先 FAIL，完成 Step 15 后 PASS

- [ ] **Step 19: 运行本文件全部测试**

Run: `python -m pytest tests/test_close_behavior.py -v`

Expected: 全部 PASS

- [ ] **Step 20: 提交这一小步**

```bash
git add tests/test_close_behavior.py src/core/controller.py src/ui/result_bar.py src/ui/tray.py
git commit -m "feat: add close button tray behavior flow"
```

---

## Chunk 3: 询问对话框与设置界面

### Task 3: 把交互补全到用户可配置

**Files:**
- Modify: `src/core/controller.py`
- Modify: `src/ui/settings_window.py`

- [ ] **Step 1: 写失败测试，定义“记住为 quit”**

在 `tests/test_close_behavior.py` 追加：

```python
def test_close_request_asks_and_remembers_quit_choice():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior = MagicMock(return_value=('quit', True))

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_called_once_with('close_button_behavior', 'quit')
    ctrl.app.quit.assert_called_once()
```

- [ ] **Step 2: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_asks_and_remembers_quit_choice -v`

Expected: FAIL

- [ ] **Step 3: 写失败测试，定义取消行为**

继续追加：

```python
def test_close_request_cancel_does_nothing():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior = MagicMock(return_value=(None, False))

    CoreController._handle_result_bar_close(ctrl)

    ctrl.result_bar.hide.assert_not_called()
    ctrl.app.quit.assert_not_called()
    ctrl.settings.set.assert_not_called()
```

- [ ] **Step 4: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_close_request_cancel_does_nothing -v`

Expected: FAIL

- [ ] **Step 5: 最小补全 `CoreController._handle_result_bar_close()`**

补全：

- `quit + remember` 保存 `quit`
- `None` 直接返回

- [ ] **Step 6: 实现真正的关闭确认框**

在 `src/core/controller.py` 的 `_ask_close_behavior()` 使用 `QMessageBox` 实现：

- 标题：`关闭程序`
- 文案：`关闭后要做什么？`
- informative text：`之后可以在“设置 -> 通用 -> 关闭按钮行为”里修改`
- 自定义按钮：`放到托盘`、`退出程序`、`取消`
- 勾选框：`记住我的选择，下次不再询问`
- 勾选框默认选中

返回值约定：

- `('tray', checked)`
- `('quit', checked)`
- `(None, False)`

- [ ] **Step 7: 在设置页增加关闭按钮行为下拉框**

在 `src/ui/settings_window.py` 的“通用”页增加：

```python
self._combo_close_behavior = QComboBox()
self._combo_close_behavior.addItem('每次询问', 'ask')
self._combo_close_behavior.addItem('最小化到托盘', 'tray')
self._combo_close_behavior.addItem('直接退出程序', 'quit')
```

并新增表单项：

```python
form.addRow('关闭按钮行为', self._combo_close_behavior)
```

- [ ] **Step 8: 让设置页正确加载和保存该字段**

在 `_load_values()` 中读取：

```python
behavior = self.settings.get('close_button_behavior', 'ask')
idx = self._combo_close_behavior.findData(behavior)
if idx >= 0:
    self._combo_close_behavior.setCurrentIndex(idx)
```

在 `_save()` 中保存：

```python
self.settings.set('close_button_behavior', self._combo_close_behavior.currentData())
```

在 `_reset_defaults()` 中重置为 `DEFAULTS['close_button_behavior']`

- [ ] **Step 9: 运行设置测试和关闭行为测试**

Run: `python -m pytest tests/test_settings.py tests/test_close_behavior.py -v`

Expected: 全部 PASS

- [ ] **Step 10: 提交这一小步**

```bash
git add src/core/controller.py src/ui/settings_window.py tests/test_settings.py tests/test_close_behavior.py
git commit -m "feat: make close button behavior configurable"
```

---

## Chunk 4: 托盘不可用降级与回归

### Task 4: 补全系统托盘不可用时的降级

**Files:**
- Modify: `src/core/controller.py`
- Modify: `tests/test_close_behavior.py`

- [ ] **Step 1: 写失败测试，覆盖托盘不可用降级**

在 `tests/test_close_behavior.py` 追加：

```python
def test_tray_behavior_falls_back_to_quit_when_system_tray_unavailable():
    from core.controller import CoreController
    ctrl = make_controller()
    ctrl.settings.get.return_value = 'tray'
    ctrl._is_tray_available = MagicMock(return_value=False)
    ctrl._warn_tray_unavailable = MagicMock()

    CoreController._handle_result_bar_close(ctrl)

    ctrl._warn_tray_unavailable.assert_called_once()
    ctrl.app.quit.assert_called_once()
```

- [ ] **Step 2: 运行该单测，确认它先失败**

Run: `python -m pytest tests/test_close_behavior.py::test_tray_behavior_falls_back_to_quit_when_system_tray_unavailable -v`

Expected: FAIL

- [ ] **Step 3: 最小实现托盘可用性检查**

在 `src/core/controller.py` 新增：

- `_is_tray_available()`，内部调用 `QSystemTrayIcon.isSystemTrayAvailable()`
- `_warn_tray_unavailable()`，使用 `QMessageBox.warning(...)`

在 `_send_main_window_to_tray()` 中：

- 若托盘不可用，先提示，再 `self.app.quit()`

- [ ] **Step 4: 重跑该单测，确认转绿**

Run: `python -m pytest tests/test_close_behavior.py::test_tray_behavior_falls_back_to_quit_when_system_tray_unavailable -v`

Expected: PASS

- [ ] **Step 5: 运行本次相关全部测试**

Run: `python -m pytest tests/test_settings.py tests/test_close_behavior.py -v`

Expected: 全部 PASS

- [ ] **Step 6: 运行回归测试**

Run: `python -m pytest tests/test_fixed_mode.py tests/test_subtitle.py tests/test_history.py -v`

Expected: 全部 PASS

- [ ] **Step 7: 手动验证**

Run: `python src/main.py`

Manual check:

- 首次点击 `✕` 会弹窗
- 勾选“记住我的选择”后，再次点击不再询问
- 设置中可以改回“每次询问”
- 选择“最小化到托盘”后，点击托盘图标能恢复主结果条
- 选择“直接退出程序”后，点击 `✕` 直接退出

- [ ] **Step 8: 最终提交**

```bash
git add src/core/settings.py src/core/controller.py src/ui/result_bar.py src/ui/tray.py src/ui/settings_window.py tests/test_settings.py tests/test_close_behavior.py
git commit -m "feat: add configurable close-to-tray behavior"
```
