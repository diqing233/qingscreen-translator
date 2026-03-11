# Mixed Overlay Translation Bars Design

**Date:** 2026-03-12

## Goal

Replace the current single in-box overlay with a mixed rendering model:

1. `over` mode renders multiple small black translation bars aligned to OCR-detected paragraphs.
2. `below` mode keeps a single black translation bar below the full selection box.

The change must improve readability for dense paragraphs without changing the user's existing overlay toggle workflow.

## Decisions

1. `over` and `below` no longer share the same geometry model.
2. `over` mode is paragraph-aware and requires both OCR layout data and paragraph-specific translated text.
3. `below` mode remains box-level and continues to show one aggregated translation result.
4. Overlay mode switching stays `over -> below -> off` through the existing box toolbar button.
5. Overlay font-size controls remain global through `overlay_font_delta` and affect both rendering modes.
6. The controller must preserve the latest full-box translation text, the latest paragraph translations, and the latest OCR layout payload so overlays can be rebuilt on mode switches, moves, and refreshes.

## UX Notes

- In `over` mode, each OCR paragraph gets its own black subtitle surface instead of a single full-width band.
- Paragraph overlay bars should stay compact, sit near the matching source paragraph, and avoid covering unrelated text.
- In `below` mode, the translation still appears as one bar attached to the bottom of the selection box, matching the user's current mental model.
- The visual language should stay consistent across both modes: dark backdrop, light text, compact padding, and high contrast.

## Data Flow

1. `OCRWorker` keeps RapidOCR's positional rows and returns a structured payload alongside the flattened source text.
2. A shared paragraph-layout helper groups OCR rows into paragraph blocks with source text and anchor rectangles.
3. The controller stores the latest OCR layout for each `TranslationBox`.
4. The controller continues to request one full-box translation for the result bar and `below` mode.
5. When `over` mode is active, or when the user switches into it, the controller requests paragraph-level translations and caches them on the box.
6. `TranslationBox` renders:
   - `over`: one widget per paragraph using cached paragraph translations and paragraph anchors
   - `below`: one full-width bottom bar using the full-box translation

## Paragraph Grouping Strategy

- Start from RapidOCR line boxes in reading order.
- Merge nearby lines into one paragraph when they are vertically adjacent and horizontally compatible.
- Preserve source order so paragraph overlays appear in the same order as the source text.
- If grouping produces only one paragraph, `over` mode still uses the paragraph renderer, but with one local bar rather than the current full-box band.

## Error Handling

- If OCR returns text but no usable boxes, `over` mode falls back to a single compact in-box bar using the full-box translation.
- If paragraph translation requests fail or only partially complete, `over` mode falls back to the same single compact in-box bar instead of showing mismatched bars.
- If translation is empty, no overlay bars are shown in either mode.
- If a paragraph box is too narrow, its overlay bar may wrap to multiple lines but must stay anchored to that paragraph's bounds.
- When the box moves, hides, shows, resizes, or closes, all overlay widgets must update or clean up together to avoid orphaned windows.

## Testing Strategy

- Add OCR payload tests that verify structured line extraction is preserved alongside flattened text.
- Add paragraph-layout helper tests that verify OCR rows merge into stable paragraph groups.
- Add `TranslationBox` tests for:
  - paragraph overlay widget creation in `over` mode
  - single-bar behavior in `below` mode
  - geometry refresh on move/resize
  - cleanup on hide/close
- Add controller tests to verify:
  - full-box translation continues to feed the result bar and `below` mode
  - paragraph translations feed `over` mode
  - `stop/clear` still cancels every active translation worker
- Keep existing overlay toggle-cycle and font-delta behavior covered.

## Impacted Files

- `src/ocr/ocr_worker.py`
- `src/core/overlay_layout.py` (new)
- `src/core/controller.py`
- `src/ui/translation_box.py`
- `tests/test_overlay_layout.py` (new)
- `tests/test_fixed_mode.py`
- `tests/test_result_bar_stop_clear.py`
- `tests/test_subtitle.py`
- `tests/test_ocr_worker.py` (new)
