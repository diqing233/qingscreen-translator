# Result Bar Expand Edit Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the result bar expand downward for source/explain panels and let users edit source text and retranslate directly from the result bar.

**Architecture:** `ResultBar` will separate the translation display from two collapsible lower panels: an editable source panel and an AI explain panel. A new result-bar signal will carry edited source text into `CoreController`, which will reuse the existing translation pipeline without re-running OCR.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Result Bar Expansion And Editable Source UI

### Task 1: Add failing tests for downward expansion and editable source state

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Write the failing test**

Add tests that assert:

- opening `原文` increases the result-bar height while keeping `y()` unchanged
- opening `AI科普` also increases height while keeping `y()` unchanged
- the source section uses an editable widget instead of the old read-only label
- the `重新翻译` button is disabled for blank editor content and enabled for non-blank editor content

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`

Expected: FAIL because the current source section is a read-only label and expansion behavior is not bottom-anchored.

- [ ] **Step 3: Write minimal implementation**

Update `src/ui/result_bar.py` so:

- the body contains separate translation, source-edit, and explain sections
- the source section is a collapsible editor container with a `重新翻译` button
- content-driven resizing preserves the current top edge

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_result_bar_toolbar.py src/ui/result_bar.py
git commit -m "feat: add editable source panel to result bar"
```

## Chunk 2: Controller Retranslate Integration

### Task 2: Add failing tests for retranslate and explain from edited source

**Files:**
- Modify: `tests/test_fixed_mode.py`
- Modify: `src/core/controller.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Write the failing test**

Add controller tests that assert:

- a new result-bar retranslate signal calls `_run_translate(edited_text, None-or-sentinel)` style logic without starting OCR
- AI explain uses the current edited source text when present instead of stale `_current_result['original']`

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fixed_mode.py -q`

Expected: FAIL because `ResultBar` does not emit a retranslate signal and controller only explains from the stored OCR original.

- [ ] **Step 3: Write minimal implementation**

Implement:

- a `retranslate_requested` signal on `ResultBar`
- controller wiring from `ResultBar` to a new `_on_retranslate_requested(text)` handler
- explain-path lookup that prefers current edited source text

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_fixed_mode.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_fixed_mode.py src/core/controller.py src/ui/result_bar.py
git commit -m "feat: translate and explain from edited result bar source"
```

## Chunk 3: Result Synchronization And Regression Coverage

### Task 3: Add tests for result syncing, clear/reset behavior, and final regressions

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_fixed_mode.py`
- Modify: `src/ui/result_bar.py`
- Modify: `src/core/controller.py`

- [ ] **Step 1: Write the failing test**

Add tests that assert:

- `show_result()` refreshes the source editor only when the user is not actively editing
- `clear_current_content()` resets the source editor, explain section, and retranslate button state
- collapsing and reopening source/explain panels preserves current panel content until clear/reset

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_fixed_mode.py -q`

Expected: FAIL because the current result-bar state model does not track editable-source ownership.

- [ ] **Step 3: Write minimal implementation**

Implement the smallest state needed in `ResultBar`:

- a dirty/editing flag for the source editor
- helper methods to sync editor content from results without clobbering active edits
- reset behavior wired into `clear_current_content()`

- [ ] **Step 4: Run focused regressions**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_fixed_mode.py -q`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_result_bar_toolbar.py tests/test_fixed_mode.py src/ui/result_bar.py src/core/controller.py
git commit -m "fix: preserve editable source state in result bar"
```

## Chunk 4: Full Verification

### Task 4: Run full suite and smoke verification

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/core/controller.py`
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_fixed_mode.py`

- [ ] **Step 1: Run focused UI/controller regressions**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py -q`

Expected: PASS

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest -q`

Expected: PASS

- [ ] **Step 3: Run compile smoke check**

Run: `python -m pytest tests/test_startup_compile.py -q`

Expected: PASS

- [ ] **Step 4: Commit final integration**

```bash
git add src/ui/result_bar.py src/core/controller.py tests/test_result_bar_toolbar.py tests/test_fixed_mode.py
git commit -m "feat: support editable source retranslation in result bar"
```
