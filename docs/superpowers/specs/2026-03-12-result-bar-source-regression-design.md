# Result Bar Source Regression Design

**Date:** 2026-03-12

## Goal

Fix the result bar regressions introduced by the editable-source work so that:

1. Clicking `原文` with translated content does not create a large blank area above the source content.
2. The source content appears exactly once.
3. The action buttons remain clickable after expanding `原文`.

## Root Cause

`src/ui/result_bar.py` currently mixes two implementations:

- the old read-only source / AI explain widgets are still created and added to the body layout
- the new editable source / explain panels are also created and added to the same layout
- several methods (`show_result`, `clear_current_content`, `_toggle_source`, `_on_explain`) are defined twice, with the later versions partially overriding earlier behavior

This creates duplicate visible sections, incorrect height growth, and overlapping layout regions.

## Approaches Considered

### 1. Recommended: Remove the old source/explain path entirely

- Delete the old read-only source label, old AI loading label, old AI text block, and the earlier duplicate methods.
- Keep the editable source panel and explain panel as the only supported implementation.
- Add regression tests that prove only one source section is shown and the toolbar remains interactive.

**Pros:** Smallest long-term surface area, clearest ownership, lowest chance of more layout collisions.

**Cons:** Requires touching a large existing file instead of adding another small patch.

### 2. Hide the old widgets but keep the code

- Leave the old widgets and methods in place.
- Force them hidden whenever the new panels are used.

**Pros:** Smaller diff in the short term.

**Cons:** Keeps contradictory state paths alive, so future regressions remain likely.

### 3. Split the result bar into new helper classes first

- Refactor source/explain sections into dedicated widgets before fixing behavior.

**Pros:** Better architecture.

**Cons:** Too large for this bugfix and adds unnecessary risk.

## Decision

Use approach 1. This is a regression fix, not a new feature, so the correct move is to remove the obsolete path instead of trying to coordinate two implementations in one class.

## Design

### UI Structure

- Keep the translation text block as the top content area.
- Keep one action row with `原文`, `复制原文`, and `AI科普`.
- Keep one editable `_source_panel` below the action row.
- Keep one `_explain_panel` below the source panel.

### State Rules

- `_source_expanded` controls only `_source_panel`.
- `_explain_expanded` controls only `_explain_panel`.
- `show_result()` updates translation text and source editor state without reintroducing the old label path.
- `clear_current_content()` clears only the surviving widgets and resets both panel states.

### Interaction Rules

- Expanding `原文` must only grow the window downward and must not insert any hidden spacer from old controls.
- The source area must render once.
- The toolbar row must stay on top of its own interaction region and remain clickable after expansion.

### Testing

- Add UI regression tests for:
  - exactly one source section becoming visible after `原文` expand
  - no extra blank source label becoming visible
  - the source panel appearing below the translation area
  - the toolbar buttons still being enabled and clickable after expand
- Keep the existing editable-source tests green.
