# Translation Box Overlay Lock Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make in-box overlay translations readable with a real black background plate, keep the toolbar visible whenever the cursor is inside the original box, and make the pin button lock only the current box position.

**Architecture:** `TranslationBox` will separate three concerns that are currently entangled: global translation mode, per-box position lock, and overlay rendering. `over` subtitles will move inside the box as child subtitle surfaces, while `below` subtitles remain detached helper windows. Toolbar visibility will come from explicit cursor-vs-box geometry checks instead of widget enter/leave events.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Reproduce The Three Bugs In Tests

### Task 1: Add failing tests for in-box overlay readability, hover logic, and position locking

**Files:**
- Modify: `tests/test_subtitle.py`
- Modify: `src/ui/translation_box.py`

- [ ] **Step 1: Write failing tests**

Add tests that assert:

- `over` mode paragraph overlays are rendered as child widgets of `TranslationBox`
- in-box overlay surfaces produce non-transparent pixels when grabbed
- toolbar visibility is driven by cursor positions inside the original box rectangle
- detached `below` subtitle bars do not count as inside-box hover
- the pin button locks the current box and prevents drag movement
- a locked temp box does not emit `close_requested` on dismiss timeout

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_subtitle.py -q`

Expected: FAIL on the new assertions before implementation.

## Chunk 2: Implement The Minimal TranslationBox Fix

### Task 2: Split in-box overlays, detached below overlays, and per-box locking

**Files:**
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Add dedicated in-box subtitle surfaces**

Implement child subtitle widgets that:

- live inside `TranslationBox`
- paint a black background plate explicitly
- remain mouse-transparent

- [ ] **Step 2: Keep detached helper windows only for `below` mode**

Update subtitle layout helpers so:

- `over` mode uses in-box child subtitle surfaces
- `below` mode keeps detached helper windows
- fallback single-surface rendering still works when paragraph anchors are missing

- [ ] **Step 3: Add explicit toolbar hover-state refresh**

Implement a helper that decides toolbar visibility from a global cursor point and the original box rectangle.

- [ ] **Step 4: Add per-box position locking**

Implement `_position_locked` and update:

- pin button behavior
- drag handlers
- temp-dismiss behavior
- pin button visual state

- [ ] **Step 5: Run focused tests**

Run: `python -m pytest tests/test_subtitle.py -q`

Expected: PASS

## Chunk 3: Verify Integration

### Task 3: Run regression slices and full verification

**Files:**
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_subtitle.py`
- Modify: `tests/test_fixed_mode.py` (only if needed)

- [ ] **Step 1: Run focused translation-box regressions**

Run: `python -m pytest tests/test_subtitle.py -q`

Expected: PASS

- [ ] **Step 2: Run controller regressions**

Run: `python -m pytest tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py tests/test_result_bar_toolbar.py -q`

Expected: PASS

- [ ] **Step 3: Run full verification**

Run: `python -m pytest -q`

Expected: PASS
