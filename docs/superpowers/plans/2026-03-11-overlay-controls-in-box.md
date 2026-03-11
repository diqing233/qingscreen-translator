# Overlay Controls In Box Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把覆盖翻译控件从结果条迁移到翻译框内，并让 over 模式覆盖译文更清晰易读。

**Architecture:** 结果条只保留全局翻译操作，不再承担覆盖控件。翻译框自身负责覆盖模式切换和字号入口，字号变化继续写入全局设置，并通过控制器刷新已存在翻译框的覆盖样式。

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Tests First

### Task 1: Update UI placement tests

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Implement minimal code**
- [ ] **Step 4: Run test to verify it passes**

## Chunk 2: Move Controls

### Task 2: Move overlay controls into translation boxes

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/ui/translation_box.py`
- Modify: `src/core/controller.py`

- [ ] **Step 1: Remove result bar overlay controls**
- [ ] **Step 2: Add box-local overlay and font buttons**
- [ ] **Step 3: Wire font delta refresh through controller**
- [ ] **Step 4: Verify targeted tests pass**

## Chunk 3: Visual Readability

### Task 3: Improve over-mode surface

**Files:**
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Make over-mode use a compact in-box surface**
- [ ] **Step 2: Refresh geometry/style on move and resize**
- [ ] **Step 3: Run full test suite**
- [ ] **Step 4: Run startup smoke check**

