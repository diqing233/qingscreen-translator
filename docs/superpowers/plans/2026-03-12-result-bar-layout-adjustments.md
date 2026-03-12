# Result Bar Layout Adjustments Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix result-bar source/explain expansion so lower panels only grow downward, while moving `重新翻译` into the main action row with dirty-state enablement.

**Architecture:** Keep the current `ResultBar` structure, but change layout priorities so the translation area no longer absorbs expansion height from lower panels. Track a synced source baseline and use it to drive `重新翻译` enablement from the main action row.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Layout Regression Tests

### Task 1: Add failing tests for button order, stable translation height, and dirty-state enablement

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Write the failing test**

Add tests that assert:

- `重新翻译` sits after `复制原文` and before `AI科普`
- expanding `原文` does not increase the translation widget height
- expanding `AI科普` does not increase the translation widget height
- `重新翻译` stays disabled when the editor matches the synced source text and becomes enabled only after an actual edit

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: FAIL because the current layout lets the translation widget absorb expansion height and the retranslate button still lives inside the source panel.

- [ ] **Step 3: Write minimal implementation**

Update `src/ui/result_bar.py` so:

- the action row includes `重新翻译` between `复制原文` and `AI科普`
- the translation widget uses a bounded vertical policy / height strategy
- source dirty tracking compares against the last synced source value

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

## Chunk 2: Full Verification

### Task 2: Run focused and full verification

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`
Expected: PASS
