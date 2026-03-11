# Mixed Overlay Translation Bars Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `over` mode render paragraph-level black translation bars with matching paragraph translations while keeping `below` mode as one black translation bar below the full selection box.

**Architecture:** Preserve OCR layout metadata from `OCRWorker`, group rows into paragraphs in a shared helper, and let the controller manage two translation caches per box: one full-box result and one paragraph result list. `TranslationBox` then renders paragraph widgets for `over` and a single widget for `below`, with a fallback to one compact in-box bar if paragraph layout or paragraph translation data is missing.

**Tech Stack:** Python, PyQt5, pytest, RapidOCR

---

## Chunk 1: OCR Layout Payload

### Task 1: Add failing tests for structured OCR rows

**Files:**
- Create: `tests/test_ocr_worker.py`
- Modify: `src/ocr/ocr_worker.py`

- [ ] **Step 1: Write the failing test**

```python
def test_run_rapidocr_returns_text_and_rows(monkeypatch):
    import ocr.engine
    from ocr.ocr_worker import OCRWorker

    worker = OCRWorker(None)
    monkeypatch.setattr(ocr.engine, "get_engine", lambda: lambda img: (
        [
            [[[0, 0], [20, 0], [20, 10], [0, 10]], "First line", 0.99],
            [[[0, 20], [20, 20], [20, 30], [0, 30]], "Second line", 0.98],
        ],
        0.01,
    ))

    payload = worker._run_rapidocr(object())

    assert payload["text"] == "First line Second line"
    assert len(payload["rows"]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ocr_worker.py::test_run_rapidocr_returns_text_and_rows -v`

Expected: FAIL because `_run_rapidocr()` currently returns a plain string.

- [ ] **Step 3: Write minimal implementation**

Implement `_run_rapidocr()` so it returns a payload like:

```python
{
    "text": "First line Second line",
    "rows": [
        {"text": "First line", "box": [[0, 0], [20, 0], [20, 10], [0, 10]]},
        {"text": "Second line", "box": [[0, 20], [20, 20], [20, 30], [0, 30]]},
    ],
}
```

Update the OCR pipeline helpers to consume `payload["text"]` instead of assuming a raw string.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_ocr_worker.py::test_run_rapidocr_returns_text_and_rows -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_ocr_worker.py src/ocr/ocr_worker.py
git commit -m "test: preserve OCR row layout payload"
```

### Task 2: Add a shared paragraph-layout helper

**Files:**
- Create: `src/core/overlay_layout.py`
- Create: `tests/test_overlay_layout.py`

- [ ] **Step 1: Write the failing test**

Add tests that pass OCR row boxes into a grouping helper and assert:

- nearby rows merge into one paragraph
- larger vertical gaps create separate paragraphs
- grouped output preserves source text order and anchor rectangles

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_overlay_layout.py -v`

Expected: FAIL because no helper exists yet.

- [ ] **Step 3: Write minimal implementation**

Create `src/core/overlay_layout.py` with focused helpers such as:

```python
def group_rows_into_paragraphs(rows):
    ...
```

Each paragraph should contain:

```python
{
    "text": "Paragraph text",
    "rows": [...],
    "rect": {"x": 0, "y": 0, "width": 100, "height": 40},
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_overlay_layout.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/overlay_layout.py tests/test_overlay_layout.py
git commit -m "feat: add OCR paragraph layout helper"
```

### Task 3: Thread OCR payload through the controller boundary

**Files:**
- Modify: `src/ocr/ocr_worker.py`
- Modify: `src/core/controller.py`
- Modify: `tests/test_fixed_mode.py`

- [ ] **Step 1: Write the failing test**

Add a controller test that passes a structured OCR payload into `_on_ocr_done()` and asserts the box stores both flattened text and layout metadata.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fixed_mode.py::test_ocr_done_preserves_layout_payload -v`

Expected: FAIL because the controller currently only forwards plain text.

- [ ] **Step 3: Write minimal implementation**

- Change `OCRWorker.result_ready` to emit the structured payload.
- Normalize controller code so the translation request still uses flattened text.
- Store the latest OCR rows on the box, for example in `_last_ocr_rows`.

- [ ] **Step 4: Run targeted tests**

Run: `python -m pytest tests/test_ocr_worker.py tests/test_overlay_layout.py tests/test_fixed_mode.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ocr/ocr_worker.py src/core/controller.py src/core/overlay_layout.py tests/test_fixed_mode.py tests/test_overlay_layout.py tests/test_ocr_worker.py
git commit -m "feat: carry OCR layout data into translation boxes"
```

## Chunk 2: Paragraph Translation Orchestration

### Task 4: Add controller tests for mixed translation caches

**Files:**
- Modify: `src/core/controller.py`
- Modify: `tests/test_fixed_mode.py`
- Modify: `tests/test_result_bar_stop_clear.py`

- [ ] **Step 1: Write the failing test**

Add tests that expect:

- the controller still stores one full-box translation result
- `over` mode also stores paragraph translations in source order
- `stop/clear` cancels all active paragraph translation workers
- switching from `below` to `over` can reuse cached OCR paragraphs and paragraph translations

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py -v`

Expected: FAIL because the controller currently manages only one translation result per box.

- [ ] **Step 3: Write minimal implementation**

- Add per-box paragraph cache fields such as `_last_ocr_paragraphs` and `_last_paragraph_translations`.
- Reuse `TranslationWorker` for paragraph text jobs.
- Trigger paragraph translation refresh only when `over` mode needs it.
- Keep full-box translation behavior unchanged for result bar and `below` mode.

- [ ] **Step 4: Run targeted tests**

Run: `python -m pytest tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/controller.py tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py
git commit -m "feat: cache paragraph translations for overlay mode"
```

## Chunk 3: Mixed Overlay Rendering

### Task 5: Add failing UI tests for mixed overlay widgets

**Files:**
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing test**

Add tests that expect:

- `over` mode creates multiple overlay widgets when paragraph anchors and paragraph translations exist
- `below` mode still uses exactly one overlay widget
- fallback to one compact in-box widget occurs when paragraph data is missing
- move/resize/close updates or destroys all overlay widgets

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_subtitle.py -v`

Expected: FAIL because `TranslationBox` currently manages only one `_subtitle_win`.

- [ ] **Step 3: Write minimal implementation**

- Introduce separate state for:
  - one bottom-bar widget in `below`
  - many paragraph widgets in `over`
  - one fallback compact widget when paragraph rendering cannot be used
- Add helpers for:
  - paragraph widget creation/reuse
  - bottom-bar widget creation/reuse
  - cleanup of all overlay widgets
- Keep the existing button and font-size behavior unchanged.

- [ ] **Step 4: Run targeted tests**

Run: `python -m pytest tests/test_subtitle.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/translation_box.py tests/test_subtitle.py
git commit -m "feat: render mixed overlay translation bars"
```

## Chunk 4: Controller Integration And Regression Coverage

### Task 6: Refresh the correct overlay renderer after translation completes

**Files:**
- Modify: `src/core/controller.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_fixed_mode.py`

- [ ] **Step 1: Write the failing test**

Add controller tests that verify:

- `over` mode calls the paragraph overlay refresh path.
- `below` mode still calls the single bottom-bar path.
- switching modes after a translation reuses the stored OCR layout and latest translation text.
- switching into `over` reuses cached paragraph translations when available and requests them when missing.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_fixed_mode.py -v`

Expected: FAIL because the controller currently only knows about `show_subtitle(translated)`.

- [ ] **Step 3: Write minimal implementation**

Update the controller and `TranslationBox` public API so `show_subtitle()` can rebuild overlays from:

- the latest translated text
- the latest OCR row payload / paragraph anchors
- the latest paragraph translation list
- the active overlay mode

- [ ] **Step 4: Run targeted tests**

Run: `python -m pytest tests/test_fixed_mode.py tests/test_subtitle.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/controller.py src/ui/translation_box.py tests/test_fixed_mode.py tests/test_subtitle.py
git commit -m "feat: refresh mixed overlay renderers from controller"
```

### Task 7: Final regression and smoke verification

**Files:**
- Modify: `src/ocr/ocr_worker.py`
- Modify: `src/core/overlay_layout.py`
- Modify: `src/core/controller.py`
- Modify: `src/ui/translation_box.py`
- Create: `tests/test_overlay_layout.py`
- Modify: `tests/test_fixed_mode.py`
- Modify: `tests/test_result_bar_stop_clear.py`
- Modify: `tests/test_subtitle.py`
- Create: `tests/test_ocr_worker.py`

- [ ] **Step 1: Run focused regression suite**

Run: `python -m pytest tests/test_ocr_worker.py tests/test_overlay_layout.py tests/test_subtitle.py tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py -v`

Expected: PASS

- [ ] **Step 2: Run broader UI/backend regression suite**

Run: `python -m pytest tests/test_result_bar_toolbar.py tests/test_translation_backends.py -v`

Expected: PASS

- [ ] **Step 3: Run a startup smoke check**

Run: `python -c "from src.ui.translation_box import TranslationBox; from PyQt5.QtCore import QRect; print('translation_box import ok')"`

Expected: prints `translation_box import ok`

- [ ] **Step 4: Commit final integration**

```bash
git add src/ocr/ocr_worker.py src/core/overlay_layout.py src/core/controller.py src/ui/translation_box.py tests/test_ocr_worker.py tests/test_overlay_layout.py tests/test_subtitle.py tests/test_fixed_mode.py tests/test_result_bar_stop_clear.py
git commit -m "feat: support paragraph overlays for in-box translations"
```
