# Result Bar Compact Panels Design

**Date:** 2026-03-12

## Goal

Rebuild the result bar so it behaves like a compact floating results strip instead of a stacked document viewer:

1. The toolbar and action row stay fixed at the top.
2. The content area only contains the visible content panels: translation, source, and AI explain.
3. Each visible panel can be resized independently with a vertical splitter.
4. Opening source or AI explain grows the window downward without leaving blank areas above.
5. The existing editable-source and retranslate dirty-state behavior remains intact.

## Root Cause

The current implementation mixes two incompatible layouts:

- a compact floating toolbar layout
- a multi-section text viewer layout

It also still contains duplicated legacy methods and widgets (`_lbl_source`, `_lbl_explain`, `_btn_explain_hdr`) that describe an older panel model. Even though the recent splitter patch made tests pass, the widget hierarchy still behaves like stacked text areas inside a reused layout, so the UI expands into large blocks and does not visually match the intended compact strip.

## Approaches Considered

### 1. Recommended: Compact shell with dynamic content panels

- Keep toolbar and action row outside the content splitter.
- Use a single `QSplitter(Qt.Vertical)` only for the content area.
- Insert or remove source / AI panels from the splitter when toggled.

**Pros:** Matches the desired UI model, eliminates hidden-space artifacts, keeps the result bar visually compact.

**Cons:** Requires a deeper cleanup of `ResultBar` and removal of legacy panel code.

### 2. Keep the current nested layout and tune sizing rules again

- Retain the existing splitter-plus-wrapper approach.
- Continue adjusting visibility and preferred sizes.

**Pros:** Smaller diff.

**Cons:** Builds on a layout that already proved misleading in the real UI; likely to regress again.

### 3. Move source / AI explain into separate popups

- Keep the main strip minimal.
- Open auxiliary viewers for source and AI explain.

**Pros:** Simplest main bar.

**Cons:** Not the requested interaction; adds friction.

## Decision

Use approach 1. The content area should be a dedicated splitter of visible content panels only, while the shell above it stays fixed.

## Design

### Layout Structure

- Keep the outer `ResultBar` shell unchanged at a high level:
  - top toolbar
  - fixed action row
  - lower content region
- Replace the current mixed content stack with a dedicated content container:
  - `translation_panel` is always present
  - `source_panel` is inserted only when source is expanded
  - `explain_panel` is inserted only when AI explain is expanded
- The content container is a single vertical splitter that manages only content panels.

### Panel Rules

#### Translation Panel

- Always visible.
- Starts with a compact default height so the result bar still reads as a strip.
- Scrolls internally when content overflows.
- Can be enlarged by dragging the splitter or resizing the window taller.

#### Source Panel

- Not part of the splitter until the user expands source.
- Contains the editable source text editor only.
- Gets a sensible initial height when inserted.
- Is removed from the splitter entirely when collapsed, so it leaves no blank slot.

#### AI Explain Panel

- Not part of the splitter until AI explain is requested or expanded.
- Loading state and result state both live inside the same panel.
- Gets a sensible initial height when inserted.
- Is removed from the splitter entirely when collapsed.

### Resize Rules

- Opening source or AI explain increases total window height downward while preserving the top edge.
- Once visible, each panel can be resized independently through the splitter.
- Window resizing should give additional space to the content splitter rather than forcing fixed text-area heights.
- Each panel scrolls internally; the window should not create fake whitespace to reveal more text.

### State Rules

- Keep one active implementation path only.
- Remove the legacy source / explain widgets and duplicated methods.
- Preserve existing dirty-state behavior:
  - source editor starts synced to OCR text
  - `重新翻译` only enables after real edits
  - `show_result()` must not overwrite active source edits
- `show_explain_loading()` and `show_explain()` update the same explain panel instead of separate ad-hoc widgets.

### Testing

- Replace the current layout assertions with tests that verify:
  - toolbar and action row remain outside the content splitter
  - the content splitter initially contains only the translation panel
  - expanding source inserts the source panel without leaving blank space
  - expanding AI explain inserts the explain panel without leaving blank space
  - all visible panels resize independently
  - top-edge preservation still holds
  - retranslate dirty-state still holds

## Impacted Files

- `src/ui/result_bar.py`
- `tests/test_result_bar_toolbar.py`
