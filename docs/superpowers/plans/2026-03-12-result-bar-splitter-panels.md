# Result Bar Compact Panels Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the result bar content area so it remains compact while translation, source, and AI explain panels can be inserted, removed, and resized independently.

**Architecture:** Keep the toolbar and action row fixed outside the content area. Replace the current mixed layout with a single content splitter that only contains visible content panels, and remove the legacy duplicated source / explain code paths so all behavior flows through one implementation.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Red Tests For The New Panel Model

### Task 1: Replace the old splitter expectations with compact-panel regression tests

**Files:**
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: Write the failing tests**

Add or update tests that assert:

- the content splitter initially contains only the translation panel
- source expand inserts the source panel into the splitter and places it below the action row
- AI explain inserts the explain panel into the splitter and uses the same panel for loading and final text
- when source / explain are collapsed they are removed from the splitter instead of retaining empty space
- all visible panels can still be resized independently

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: FAIL because the current implementation still uses the previous panel structure and legacy widget path.

## Chunk 2: Rebuild ResultBar Content Panels

### Task 2: Replace the old content hierarchy with a compact dynamic panel model

**Files:**
- Modify: `src/ui/result_bar.py`

- [ ] **Step 1: Remove legacy result-panel widgets and duplicate logic**

Delete the old `_lbl_source`, `_lbl_explain`, `_lbl_explain_loading`, `_btn_explain_hdr` path and any duplicated methods that still reference it.

- [ ] **Step 2: Rebuild the content area**

Implement:

- one dedicated content splitter below the fixed action row
- an always-present `translation_panel`
- dynamically inserted / removed `source_panel`
- dynamically inserted / removed `explain_panel`

- [ ] **Step 3: Reconnect source and explain behaviors**

Ensure:

- expanding source or explain grows the window downward only
- source edits still drive `重新翻译`
- explain loading and explain result share the same explain panel
- `show_result()` preserves active source edits

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

## Chunk 3: Full Verification

### Task 3: Verify the full suite after the rebuild

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `tests/test_result_bar_toolbar.py`

- [ ] **Step 1: Run the focused suite again**

Run: `python -m pytest tests/test_result_bar_toolbar.py -q`
Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS
