# Result Bar Expand Edit Design

**Date:** 2026-03-12

## Goal

Improve the result bar so:

1. Expanding `原文` or `AI科普` grows the window downward instead of squeezing the translation area upward.
2. The `原文` section becomes an editable source panel.
3. Users can edit or manually enter source text and trigger a new translation without re-running OCR.

## Decisions

1. Split the result bar body into three vertical sections:
   - translation display
   - source edit panel
   - AI explain panel
2. `原文` toggles an editable panel, not a read-only label.
3. The source edit panel always supports manual entry, even when OCR did not produce source text.
4. A new `重新翻译` button lives inside the source edit panel and translates the current edited text.
5. `AI科普` uses the current edited source text when present so behavior stays consistent with what the user sees.
6. Expanding or collapsing source/explain panels increases or decreases the bottom edge of the result bar while keeping the current top edge anchored.

## UX Rules

- Clicking `原文` opens a source editor below the button row.
- The translation text area stays visually stable and should not lose meaningful height because the source or explain panels opened.
- Clicking `AI科普` opens its section below the source editor area.
- If OCR source text exists, the editor is prefilled with it.
- If OCR source text does not exist, the editor opens empty with a placeholder inviting manual input.
- `重新翻译` is enabled only when the editor contains non-whitespace text.
- Closing and reopening either panel should preserve its current content in the session.

## Layout Strategy

### Translation Area

- Keep the translation display as the top content block inside the body.
- Preserve its current visual treatment and scrolling behavior.
- Give it higher layout priority than the expandable panels so it remains readable.

### Source Edit Panel

- Replace the read-only source label with a collapsible editor container.
- The container includes:
  - an editable text box
  - a compact `重新翻译` button
  - optional helper text / placeholder when no OCR source exists
- The panel sits directly below the action row that already contains `原文` and `AI科普`.

### Explain Panel

- Keep AI explain as a dedicated collapsible section below the source editor.
- Loading and loaded states remain in the explain section, not over the translation text.

### Window Growth

- The result bar currently auto-sizes through `adjustSize()`.
- Expand/collapse operations should measure the required content height and resize from the bottom.
- The current top-left position should stay fixed during these content-driven resizes.

## Data Flow

1. `show_result()` receives the translated text and original OCR text.
2. If the user is not actively editing, the source editor syncs to the latest `original`.
3. When the user edits the source text, the editor state becomes the active source of truth for:
   - `重新翻译`
   - `AI科普`
4. `ResultBar` emits a new signal carrying the edited source text for retranslation.
5. `CoreController` handles that signal by running translation directly from the provided text without OCR.
6. The returned translation updates the translation area as a normal result.

## Editing State Rules

- If the user is actively editing source text, incoming `show_result()` calls must not blindly overwrite the editor contents.
- If the editor has not been touched since the last result, `show_result()` may refresh it from the latest OCR text.
- `clear_current_content()` resets translation, source editor content, expand state, and explain content together.

## Error Handling

- Empty or whitespace-only editor content does not trigger retranslation.
- If retranslation fails, the existing translation remains visible and the normal error path is shown.
- If AI explain is requested with empty edited content and no OCR source, the request is ignored.
- If the user manually resized the window, content expansion still grows downward relative to the current top edge without unexpectedly re-centering the window.

## Testing Strategy

- Add result-bar UI tests that verify:
  - source expansion increases height downward
  - explain expansion increases height downward
  - source editor supports manual entry
  - `重新翻译` button enablement follows editor content
- Add controller tests that verify:
  - edited source text triggers translation without OCR
  - AI explain uses edited source text
- Keep existing toolbar and translation result tests green.

## Impacted Files

- `src/ui/result_bar.py`
- `src/core/controller.py`
- `tests/test_result_bar_toolbar.py`
- `tests/test_fixed_mode.py`
