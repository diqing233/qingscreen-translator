# Result Bar Toolbar Layout Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复结果条顶部工具栏在窄宽度下的重叠问题，并让语言按钮文本完整显示。

**Architecture:** 保留单行横向滚动工具栏，只调整滚动区内部顺序和尺寸刷新逻辑。核心改动集中在 `ResultBar`：新增工具栏刷新方法、重排覆盖按钮与切换控件位置、按文本测量语言按钮最小宽度。

**Tech Stack:** Python 3.x, PyQt5, pytest

---

## Chunk 1: 工具栏布局回归测试

### Task 1: 为工具栏顺序和宽度刷新补失败测试

**Files:**
- Create: `tests/test_result_bar_toolbar.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: 写失败测试，定义切换控件应在覆盖按钮右侧**

```python
def test_toggle_is_placed_after_overlay_button():
    ...
```

- [ ] **Step 2: 运行该测试，确认先失败**

Run: `python -m pytest tests/test_result_bar_toolbar.py::test_toggle_is_placed_after_overlay_button -v`

Expected: FAIL

- [ ] **Step 3: 写失败测试，定义切换控件显示后工具栏内容宽度会增长**

```python
def test_toolbar_width_refreshes_when_toggle_becomes_visible():
    ...
```

- [ ] **Step 4: 运行该测试，确认先失败**

Run: `python -m pytest tests/test_result_bar_toolbar.py::test_toolbar_width_refreshes_when_toggle_becomes_visible -v`

Expected: FAIL

- [ ] **Step 5: 写失败测试，定义语言按钮最小宽度能容纳文本**

```python
def test_language_buttons_reserve_enough_width_for_labels():
    ...
```

- [ ] **Step 6: 运行该测试，确认先失败**

Run: `python -m pytest tests/test_result_bar_toolbar.py::test_language_buttons_reserve_enough_width_for_labels -v`

Expected: FAIL

## Chunk 2: 最小实现

### Task 2: 调整滚动工具栏布局并补刷新逻辑

**Files:**
- Modify: `src/ui/result_bar.py`
- Test: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: 将覆盖按钮移动到切换控件左侧**
- [ ] **Step 2: 保存滚动容器和布局实例属性**
- [ ] **Step 3: 新增工具栏刷新方法**
- [ ] **Step 4: 在模式切换和语言文本更新时调用刷新**
- [ ] **Step 5: 给语言按钮设置基于文本的最小宽度**
- [ ] **Step 6: 运行新测试确认通过**

Run: `python -m pytest tests/test_result_bar_toolbar.py -v`

Expected: PASS

## Chunk 3: 回归验证

### Task 3: 跑相关测试

**Files:**
- Modify: `src/ui/result_bar.py`
- Test: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: 跑结果条相关测试**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_close_behavior.py tests/test_startup_compile.py -v`

Expected: PASS

- [ ] **Step 2: 跑全量测试**

Run: `python -m pytest tests -v`

Expected: PASS
