# Result Bar Browser Preview Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone browser preview that compares two result-bar button styling directions and shows every major button family in realistic states.

**Architecture:** Use a small Python generator that renders one static HTML preview from declarative mock data. Keep the preview isolated from the live PyQt widgets so it can be reviewed safely without modifying the active UI implementation first.

**Tech Stack:** Python, pytest, static HTML/CSS/JS

---

## Chunk 1: Lock the preview contract with tests

### Task 1: Add tests for the generated preview structure

**Files:**
- Create: `tests/test_result_bar_browser_preview.py`
- Create: `tools/result_bar_browser_preview.py`

- [ ] **Step 1: Write the failing test**

Add tests that assert the generator output contains:

- both direction headings
- a full result-bar mockup section
- a per-button state board
- all major button groups from the current result bar

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_browser_preview.py -q`
Expected: FAIL because the generator does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Create a generator module that returns HTML from declarative preview data.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_browser_preview.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_result_bar_browser_preview.py tools/result_bar_browser_preview.py
git commit -m "test: lock result bar browser preview structure"
```

## Chunk 2: Build the browser preview artifact

### Task 2: Generate the standalone comparison page

**Files:**
- Modify: `tools/result_bar_browser_preview.py`
- Create: `docs/previews/result-bar-button-preview.html`

- [ ] **Step 1: Write the failing test**

Add focused assertions for the richer output, including:

- grouped toolbar and action-row controls
- expanded source and AI panels
- state examples for hover, active, pressed, and disabled buttons

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_browser_preview.py -q`
Expected: FAIL because the richer layout is not rendered yet.

- [ ] **Step 3: Write minimal implementation**

Extend the generator and write the output HTML to `docs/previews/result-bar-button-preview.html`.

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_browser_preview.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tools/result_bar_browser_preview.py docs/previews/result-bar-button-preview.html tests/test_result_bar_browser_preview.py
git commit -m "feat: add result bar browser style preview"
```

## Chunk 3: Verify the preview locally

### Task 3: Run generation and browser verification

**Files:**
- Modify: `tools/result_bar_browser_preview.py`
- Modify: `docs/previews/result-bar-button-preview.html`

- [ ] **Step 1: Regenerate the preview**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe tools/result_bar_browser_preview.py`
Expected: HTML file updated successfully.

- [ ] **Step 2: Run focused tests**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_browser_preview.py -q`
Expected: PASS

- [ ] **Step 3: Manually inspect in browser**

Check:

- both styling directions are visible side by side
- full result-bar mockups feel close to the real widget layout
- button board covers every major function group
- visual differences between the two directions are obvious

- [ ] **Step 4: Commit**

```bash
git add tools/result_bar_browser_preview.py docs/previews/result-bar-button-preview.html tests/test_result_bar_browser_preview.py
git commit -m "test: verify result bar browser preview"
```
