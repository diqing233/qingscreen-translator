# Result Bar Stop/Clear Button Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为结果条顶部增加一个小方块双态按钮，在翻译中时可停止并丢弃当前结果，空闲时可清空当前显示内容，同时拉长默认结果条宽度。

**Architecture:** `ResultBar` 只负责按钮 UI、tooltip 和清空显示；`CoreController` 负责追踪活动翻译任务、响应停止/清空请求并丢弃已取消结果；`TranslationWorker` 在发信号前检查中断状态。默认宽度通过调整常量完成，不改现有滚动布局结构。

**Tech Stack:** Python 3.x, PyQt5, pytest

---

## Chunk 1: 结果条 UI 回归测试

### Task 1: 为按钮位置和默认宽度写失败测试

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: 写失败测试，定义停止/清空按钮位于框选按钮右侧**
- [ ] **Step 2: 运行该测试确认先失败**

Run: `python -m pytest tests/test_result_bar_toolbar.py::test_stop_clear_button_is_placed_after_play_button -v`
Expected: FAIL

- [ ] **Step 3: 写失败测试，定义默认宽度下固定模式工具栏无需滚动**
- [ ] **Step 4: 运行该测试确认先失败**

Run: `python -m pytest tests/test_result_bar_toolbar.py::test_default_width_fits_toolbar_in_fixed_mode -v`
Expected: FAIL

## Chunk 2: 控制器取消逻辑测试

### Task 2: 为停止/清空分流和取消结果写失败测试

**Files:**
- Create: `tests/test_result_bar_stop_clear.py`
- Modify: `src/core/controller.py`
- Modify: `src/ocr/ocr_worker.py`

- [ ] **Step 1: 写失败测试，定义忙碌时点击按钮会请求中断并清空内容**
- [ ] **Step 2: 运行该测试确认先失败**

Run: `python -m pytest tests/test_result_bar_stop_clear.py::test_busy_stop_clear_requests_interruption_and_clears_result_bar -v`
Expected: FAIL

- [ ] **Step 3: 写失败测试，定义空闲时点击按钮只清空内容**
- [ ] **Step 4: 运行该测试确认先失败**

Run: `python -m pytest tests/test_result_bar_stop_clear.py::test_idle_stop_clear_only_clears_result_bar -v`
Expected: FAIL

- [ ] **Step 5: 写失败测试，定义已取消翻译结果会被丢弃**
- [ ] **Step 6: 运行该测试确认先失败**

Run: `python -m pytest tests/test_result_bar_stop_clear.py::test_cancelled_translation_result_is_ignored -v`
Expected: FAIL

## Chunk 3: 最小实现

### Task 3: 实现结果条按钮和控制器取消逻辑

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/core/controller.py`
- Modify: `src/ocr/ocr_worker.py`
- Test: `tests/test_result_bar_toolbar.py`
- Test: `tests/test_result_bar_stop_clear.py`

- [ ] **Step 1: 在结果条中新增停止/清空按钮、信号、状态更新方法和清空方法**
- [ ] **Step 2: 拉长默认结果条宽度**
- [ ] **Step 3: 在控制器中跟踪活动翻译 worker 和取消任务 ID**
- [ ] **Step 4: 点击按钮时，忙碌则请求中断并丢弃结果，空闲则清空内容**
- [ ] **Step 5: 让 TranslationWorker 在发结果/错误前检查中断状态**
- [ ] **Step 6: 跑新测试确认通过**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_result_bar_stop_clear.py -v`
Expected: PASS

## Chunk 4: 回归验证

### Task 4: 跑相关回归和全量测试

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/core/controller.py`
- Modify: `src/ocr/ocr_worker.py`
- Test: `tests/test_result_bar_toolbar.py`
- Test: `tests/test_result_bar_stop_clear.py`

- [ ] **Step 1: 跑相关测试**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_result_bar_stop_clear.py tests/test_close_behavior.py -v`
Expected: PASS

- [ ] **Step 2: 跑全量测试**

Run: `python -m pytest tests -v`
Expected: PASS
