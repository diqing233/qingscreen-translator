# Translation Box Overlay Lock Design

**Date:** 2026-03-12

## Goal

Fix three interaction failures in translation boxes:

1. In-box overlay translations must always render on top of a real black background plate so the text stays readable.
2. The top-left toolbar must appear whenever the cursor is inside the original selection box, even if overlay translation content is covering part of that box.
3. The pin button must lock only the current box position so the box cannot be dragged away by the mouse.

## Decisions

1. Use a mixed rendering model:
   - `over` mode uses in-box child widgets for overlay subtitles.
   - `below` mode keeps using detached helper windows outside the original box.
2. The "inside box" rule is defined only by the original selection rectangle.
   - Hovering the detached `below` subtitle bar does not count as being inside the box.
3. Per-box position locking is a dedicated state and is not the same thing as the global box mode.
4. Global result-bar modes (`temp` / `fixed` / `multi`) continue to control defaults for newly created boxes.
5. The box pin button controls only the current box:
   - lock current box position
   - stop temp-dismiss while locked
   - prevent dragging while locked

## Root Cause

1. `over` subtitles are currently separate top-level windows. Even if they are mouse-transparent, they still sit outside the main box widget tree, so hover behavior for the box is unreliable.
2. Toolbar visibility currently relies on `enterEvent` / `leaveEvent`, which is too fragile when overlay layers are involved.
3. The pin button currently toggles `mode` on the box, but no surrounding controller state is synchronized from that button. The result is a local state flip that does not reliably enforce the intended "pin current box in place" behavior.

## UX Rules

- In-box overlay translation must always have a black background plate behind the translated text.
- The black plate is only required for translation content rendered inside the original box.
- Hovering any pixel inside the original box rectangle must show the toolbar.
- Hovering detached subtitle bars outside the original box must not show the toolbar.
- Pinning a box means its position is locked. The user can still use the toolbar buttons, but cannot drag the box itself.

## Architecture

### 1. In-box overlay surfaces

- Add dedicated child subtitle surfaces inside `TranslationBox` for `over` mode.
- These surfaces paint their own dark background and border in `paintEvent()`.
- They remain `WA_TransparentForMouseEvents` so interaction stays with the main box.

### 2. Detached below surfaces

- Keep detached helper windows only for `below` mode.
- They continue to display outside the selection box and are excluded from hover detection.

### 3. Hover detection

- Replace toolbar visibility based on widget enter/leave events with an explicit geometry check.
- `TranslationBox` should periodically or explicitly evaluate whether `QCursor.pos()` is inside the original box rectangle.
- Toolbar visibility should be updated from that geometry test after move, resize, show, hide, and cursor polling.

### 4. Position lock

- Add `_position_locked` to `TranslationBox`.
- The pin button toggles `_position_locked` and updates button state.
- Drag handlers and temp-dismiss logic must respect `_position_locked`.
- `mode` remains reserved for global translation behavior (`temp` vs `fixed`) and is no longer overloaded to mean "this specific box is pinned".

## Error Handling

- If paragraph geometry is unavailable in `over` mode, fall back to a single in-box black subtitle plate.
- If translation text is empty, hide all overlay content.
- If a box is locked while a temp-dismiss timer is already running, stop the timer immediately.
- If a locked temp box is unlocked again, temp-dismiss behavior should resume consistently from the current box state.

## Testing Strategy

- Extend `tests/test_subtitle.py` to cover:
  - `over` mode rendering with an in-box background plate
  - toolbar visibility based on explicit cursor-inside-box checks
  - detached `below` bars not counting as inside-box hover
  - position locking preventing drag movement
  - position locking suppressing temp-dismiss close
- Extend `tests/test_fixed_mode.py` only if controller-facing behavior needs regression coverage.
- Keep existing overlay rendering and move/resize cleanup tests green.
