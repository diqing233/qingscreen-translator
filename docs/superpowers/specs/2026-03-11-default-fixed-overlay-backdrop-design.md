# Default Fixed Mode And Overlay Backdrop Design

**Date:** 2026-03-11

## Goal

Make the app start in fixed translation mode by default, and improve overlay readability by adding a dark backdrop in both in-place (`over`) and below-text (`below`) overlay modes.

## Decisions

1. The default box mode is `fixed`, not `temp`.
2. The initial state must stay consistent between controller logic and result bar UI.
3. Both overlay display modes use a darker, high-contrast backdrop behind translated text.
4. Existing overlay font-size controls remain unchanged and continue to affect both modes.

## UX Notes

- When the app starts, the mode button should already show the fixed-state label and behavior.
- In `over` mode, the translated text should remain inside the translation box and sit on top of a dark translucent panel.
- In `below` mode, the translated text should appear below the source box with the same darker backdrop language, so light page backgrounds do not wash out the text.
- The backdrop should prioritize readability over subtlety.

## Impacted Files

- `src/core/controller.py`
- `src/ui/result_bar.py`
- `src/ui/translation_box.py`
- `src/core/settings.py`
- `tests/test_fixed_mode.py`
- `tests/test_result_bar_toolbar.py`
- `tests/test_subtitle.py`
- `tests/test_settings.py`
