# Result Bar Layout Adjustments Design

**Date:** 2026-03-12

## Goal

Adjust the result bar so that:

1. Expanding `原文` does not create extra blank space above the button row.
2. `原文` and `AI科普` each resize the window independently and extend only downward.
3. `重新翻译` moves to the main action row, immediately to the right of `复制原文`.
4. `重新翻译` stays disabled until the source text differs from the current synced source content.

## Approaches Considered

### 1. Recommended: Clamp the translation area and treat lower sections as independent panels

- Keep the translation text area visually stable by giving it a bounded preferred height instead of allowing it to absorb all extra height.
- Keep `_source_panel` and `_explain_panel` as the only expandable sections.
- Track a clean synced source value so `重新翻译` reflects whether the user actually changed the source text.

**Pros:** Directly fixes the visible regression, keeps existing structure, small blast radius.

**Cons:** Requires a little more state in `ResultBar`.

### 2. Manually recompute the full widget height on every state change

- Measure translation, toolbar, source panel, and explain panel every time and resize the whole window from scratch.

**Pros:** Deterministic layout.

**Cons:** More invasive, easier to regress manual sizing and existing auto-size behavior.

### 3. Split source/explain into a nested container with a separate layout root

- Put translation in one fixed region and source/explain in another dedicated lower container.

**Pros:** Stronger long-term separation.

**Cons:** Too much restructuring for this bugfix.

## Decision

Use approach 1. The current issue is not missing functionality; it is layout priority and state ownership. The smallest correct fix is to stabilize the translation block and tighten button/panel state.

## Design

### Layout

- The translation area remains the top content block, but it should not grow when lower panels open.
- The action row should contain, in order:
  - `原文`
  - `复制原文`
  - `重新翻译`
  - `AI科普`
- `原文` expands a single source editor panel below the action row.
- `AI科普` expands a single explain panel below the source panel.

### Resize Rules

- Opening `原文` increases only the bottom edge of the window.
- Opening `AI科普` increases only the bottom edge of the window.
- Opening one panel must not reflow the translation area upward or create extra dead space above the action row.
- If both panels are open, each contributes only its own panel height.

### Retranslate State

- `show_result()` syncs the editor with the latest OCR source and stores that value as the clean baseline.
- Editing the source marks the baseline dirty only when the current text differs from the synced baseline.
- `重新翻译` is enabled only when:
  - the current source text is non-blank, and
  - it differs from the last synced source value.
- After `重新翻译` is emitted, the current editor value becomes the new clean baseline.

### Testing

- Add regression tests for:
  - source expansion not increasing the translation widget height
  - explain expansion not increasing the translation widget height
  - button order with `重新翻译` between `复制原文` and `AI科普`
  - `重新翻译` disabled until the source text is actually modified

## Impacted Files

- `src/ui/result_bar.py`
- `tests/test_result_bar_toolbar.py`
