# Default Fixed Mode And Overlay Backdrop Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start the app in fixed translation mode and add a darker readable backdrop to both overlay display modes.

**Architecture:** Keep the mode default aligned in every layer that owns startup state, then tighten overlay styling in `TranslationBox` so both visual modes share a stronger contrast baseline without changing their positioning behavior.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Lock Behavior With Tests

### Task 1: Add failing tests for startup mode and overlay styling

**Files:**
- Modify: `tests/test_fixed_mode.py`
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run targeted pytest commands and confirm they fail for the expected reasons**
- [ ] **Step 3: Implement the minimum production changes**
- [ ] **Step 4: Re-run the targeted pytest commands and confirm they pass**

## Chunk 2: Align Startup Defaults

### Task 2: Make startup default to fixed mode everywhere it is owned

**Files:**
- Modify: `src/core/controller.py`
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Change controller startup mode from `temp` to `fixed`**
- [ ] **Step 2: Change result bar startup mode from `temp` to `fixed`**
- [ ] **Step 3: Ensure the mode button label and auto/manual toggle visibility still match the active mode**

## Chunk 3: Improve Overlay Readability

### Task 3: Strengthen the backdrop in both overlay modes

**Files:**
- Modify: `src/ui/translation_box.py`

- [ ] **Step 1: Update in-box overlay styling to use a darker backdrop**
- [ ] **Step 2: Update below-box overlay styling to use a matching darker backdrop**
- [ ] **Step 3: Keep geometry and font-size behavior unchanged**

## Chunk 4: Verify

### Task 4: Run regression coverage and startup smoke test

**Files:**
- Test: `tests/test_fixed_mode.py`
- Test: `tests/test_result_bar_toolbar.py`
- Test: `tests/test_subtitle.py`
- Test: `tests/test_settings.py`

- [ ] **Step 1: Run targeted regression tests**
- [ ] **Step 2: Run the full pytest suite**
- [ ] **Step 3: Run a startup smoke test with `python src/main.py`**
