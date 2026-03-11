# Overlay Paragraph Toolbar Safety Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `over` mode group OCR rows by paragraph instead of sentence fragments, and keep in-box translation bars readable without covering the top-left toolbar.

**Architecture:** Keep the current mixed overlay model, but tighten the box-local layout rules. `core.overlay_layout` will merge OCR rows with paragraph-oriented heuristics, while `ui.translation_box` will reserve a toolbar-safe inset for in-box overlays and always raise the toolbar above overlay child widgets.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Reproduce The Two Regressions

### Task 1: Add failing tests for paragraph grouping and toolbar-safe overlay layout

**Files:**
- Modify: `tests/test_overlay_layout.py`
- Modify: `tests/test_subtitle.py`
- Modify: `src/core/overlay_layout.py`
- Modify: `src/ui/translation_box.py`

- [ ] **Step 1: Write the failing tests**

Add tests that assert:

- OCR rows from one paragraph still merge when line spacing is looser than the current threshold
- paragraph overlays in `over` mode never start inside the toolbar safety band
- the toolbar remains visually above paragraph overlay bars

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_overlay_layout.py tests/test_subtitle.py -q`

Expected: FAIL on the new paragraph-merging and toolbar-safe assertions.

## Chunk 2: Implement The Minimal Fix

### Task 2: Relax paragraph grouping and reserve a toolbar-safe inset for in-box overlays

**Files:**
- Modify: `src/core/overlay_layout.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_overlay_layout.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Update paragraph grouping heuristics**

Adjust the grouping helper so same-paragraph rows merge when they are vertically close enough at paragraph scale, even if the current line-height heuristic would split them.

- [ ] **Step 2: Add a toolbar-safe overlay layout helper**

Clamp paragraph overlay geometry so `over` bars start below the top-left toolbar safety region, while still staying anchored to the source paragraph as closely as possible.

- [ ] **Step 3: Keep the toolbar visually on top**

After showing or relaying in-box overlays, explicitly raise the toolbar so it cannot be visually buried by child overlay widgets.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_overlay_layout.py tests/test_subtitle.py -q`

Expected: PASS

## Chunk 3: Verify Regressions And Existing Baseline

### Task 3: Run targeted regressions and record the pre-existing unrelated failure

**Files:**
- Modify: `src/core/overlay_layout.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_overlay_layout.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Run targeted overlay/controller regressions**

Run: `python -m pytest tests/test_overlay_layout.py tests/test_subtitle.py tests/test_fixed_mode.py -q`

Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`

Expected: current branch should still show the already-existing unrelated failure in `tests/test_result_bar_toolbar.py::test_toolbar_width_refreshes_when_toggle_visibility_changes`, with no new failures from this work.
