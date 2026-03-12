# Result Bar Source Regression Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the duplicated source/explain UI path in `ResultBar` and restore correct source expansion behavior.

**Architecture:** Keep the current editable source panel and explain panel as the only implementation. Delete the obsolete read-only source/explain widgets and duplicate methods, then lock the behavior in with focused UI regression tests.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Regression Tests

### Task 1: Add failing UI tests for duplicated source rendering and toolbar interaction

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Write the failing test**

Add tests that assert:

- expanding `原文` does not show `_lbl_source`
- expanding `原文` shows `_source_panel` exactly once
- the source panel geometry starts below the translation widget
- the `原文` button can still collapse and re-expand the panel after the first click

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: FAIL because the current class still exposes both old and new source paths.

- [ ] **Step 3: Write minimal implementation**

Update `src/ui/result_bar.py` to remove the old source/explain widgets and duplicate method definitions so only the editable panel logic remains.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

## Chunk 2: Full Verification

### Task 2: Re-run focused and full regressions

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: Run focused result-bar tests**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest -q`
Expected: PASS
