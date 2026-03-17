# Result Bar Button Polish Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the result-bar and translation-box controls so the buttons feel more natural and cohesive while preserving the current dark desktop utility style.

**Architecture:** Keep the existing widget structure and behavior, but consolidate button styling rules into a smaller set of shared helpers. Limit strong active states to actual mode toggles, keep source / AI expansion behavior visually stable, and align the floating translation-box toolbar with the result-bar action language.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Lock the current behavior with focused tests

### Task 1: Add or update focused tests for stable layout and button structure

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing test**

Add or update tests that assert:

- the result-bar action buttons stay ordered as source -> copy source -> retranslate -> AI
- source expansion keeps the translation block stable and bottom-anchors growth
- AI split-button left and right hit regions still emit the correct actions
- translation-box overlay controls remain ordered after subtitle and retain their visibility rules

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: FAIL if the intended layout / hit-target expectations are not yet encoded or if style-related structure changes accidentally disturb control placement.

- [ ] **Step 3: Write minimal implementation**

Update the tests only as needed to describe the intended structure and interaction behavior without asserting raw color strings.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_result_bar_toolbar.py tests/test_subtitle.py
git commit -m "test: lock result bar button polish behavior"
```

## Chunk 2: Unify result-bar button styles

### Task 2: Refine the toolbar, action-row, split-button, and toggle styling in `ResultBar`

**Files:**
- Modify: `src/ui/result_bar.py`
- Test: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: Write the failing test**

Add focused assertions for any structural changes needed by the polish pass, such as stable button heights or explicit enabled / disabled behavior that is not already covered.

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py -q`
Expected: FAIL because the current `ResultBar` helpers still apply inconsistent button treatments.

- [ ] **Step 3: Write minimal implementation**

Update `src/ui/result_bar.py` to:

- introduce shared neutral button styling for toolbar and action-row helpers
- keep strong active styles only for true mode buttons
- soften expand-button active feedback for `_btn_source` and `_btn_ai`
- align `_SplitButton` rendering with the same neutral container language
- refine `TranslateToggle.paintEvent()` so the two states are clearer without becoming louder

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/result_bar.py tests/test_result_bar_toolbar.py
git commit -m "feat: polish result bar button hierarchy"
```

## Chunk 3: Align floating translation-box controls

### Task 3: Apply the same button language to `TranslationBox`

**Files:**
- Modify: `src/ui/translation_box.py`
- Test: `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing test**

Add or update focused tests that protect button ordering and any state behavior needed while polishing the floating toolbar.

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_subtitle.py -q`
Expected: FAIL if the floating toolbar still diverges from the approved interaction hierarchy.

- [ ] **Step 3: Write minimal implementation**

Update `src/ui/translation_box.py` to:

- restyle `_make_btn()` so the floating toolbar matches the calmer dark utility language
- keep warning and active states reserved for the few buttons that need them
- preserve current toolbar ordering, hover visibility, and pin / overlay behavior

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_subtitle.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/translation_box.py tests/test_subtitle.py
git commit -m "feat: align translation box button styling"
```

## Chunk 4: Verify the combined UI behavior

### Task 4: Run focused and broader verification

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Run focused tests**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest -q`
Expected: PASS

- [ ] **Step 3: Perform manual visual verification**

Check these states in the running UI:

- toolbar neutral buttons stay visually secondary to content
- mode toggles remain the strongest active state
- source and AI expand controls feel calmer and consistent
- disabled retranslate still reads as intentionally unavailable
- translation-box toolbar feels like the same product family as the result bar

- [ ] **Step 4: Commit**

```bash
git add src/ui/result_bar.py src/ui/translation_box.py tests/test_result_bar_toolbar.py tests/test_subtitle.py
git commit -m "test: verify result bar button polish"
```
