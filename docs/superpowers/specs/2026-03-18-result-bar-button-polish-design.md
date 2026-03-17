# Result Bar Button Polish Design

**Date:** 2026-03-18

## Goal

Polish the result-bar and translation-box buttons so they feel more natural and cohesive while preserving the current dark desktop utility look. The work should improve visual hierarchy, interaction feedback, and panel expansion behavior without changing the existing translation workflow.

## Approaches Considered

### 1. Recommended: Unify the existing button language and soften state changes

- Keep the current dark utility styling.
- Standardize shared metrics, borders, and hover behavior across toolbar, action-row, split, and toggle controls.
- Reserve strong highlight states for true mode toggles and keep expand / utility actions visually calmer.

**Pros:** Matches the approved direction, small blast radius, low behavior risk.

**Cons:** Requires touching several button helpers instead of one isolated widget.

### 2. Rebuild the controls into a more obvious chip system

- Convert both the toolbar and the lower action row into a stronger chip-style component language.

**Pros:** Very consistent and visually tidy.

**Cons:** Feels more like a redesign than a polish pass.

### 3. Limit the work to the lower action row only

- Leave the top toolbar mostly unchanged and only restyle the source / retranslate / AI controls.

**Pros:** Lowest risk.

**Cons:** Would leave the main source of inconsistency in place because the toolbar and floating box controls would still speak different visual languages.

## Decision

Use approach 1. The user wants to preserve the current look, so the right move is to tighten hierarchy and interaction feedback rather than replace the visual system.

## Design

### Visual Language

- Keep the top toolbar visually secondary to the translation content.
- Treat the lower action row as the primary control group for source and AI actions.
- Use one shared baseline for button height, corner radius, border weight, and padding wherever practical.
- Keep the existing blue / green accent vocabulary for active translation modes, but reduce contrast for neutral controls.
- Preserve the current dark palette and desktop-tool feel instead of introducing a new theme.

### Interaction Hierarchy

- **Mode buttons** such as `_btn_box_mode_cycle`, `_btn_ai_mode`, and `TranslateToggle` may use the strongest active state.
- **Utility buttons** such as copy, history, settings, and reset stay neutral and should not compete with the content area.
- **Expand buttons** such as `_btn_source` and `_btn_ai` use a mild active treatment: arrow flips, border / fill lift slightly, but they do not become high-emphasis CTA buttons.
- **Danger buttons** such as stop / close overlay keep the warm warning treatment and remain the only consistently warm controls.
- Standardize `hover`, `pressed`, `disabled`, and `checked/active` feedback across all button families.

### Expand and Panel Behavior

- Opening source or AI panels must not move the toolbar or action row.
- The source panel remains directly below the translation panel.
- The AI explain panel remains directly below the source panel when both are visible.
- Window growth stays bottom-anchored so expansion feels stable.
- Source and explain panels should share container language: same rounding, border framing, spacing, and scroll treatment, with color carrying the semantic difference.
- `_btn_retranslate` stays in place at all times and communicates availability only through enabled / disabled state.

### Component Boundaries

- Consolidate shared style rules inside the existing helper methods in `ResultBar`:
  - `_action_btn`
  - `_icon_btn`
  - `_small_toolbar_btn`
  - `_mode_btn_style`
  - `_lang_btn_style`
- Update `_SplitButton` so it follows the same neutral / hover / expanded logic as the standard action buttons while preserving split hit targets.
- Update `TranslateToggle` so the track, pill, and label contrast feel calmer and clearer without changing its behavior.
- Update `TranslationBox._make_btn()` and the pin / subtitle state refresh methods so the floating box toolbar feels like the same product family as the result bar.

### Testing

- Keep automated tests focused on behavior and layout, not exact color values.
- Extend or adjust existing UI tests to cover:
  - stable control ordering in the result-bar action row
  - source / explain expansion remaining bottom-anchored
  - split-button click regions continuing to work
  - translation-box toolbar controls staying in the expected order
- Rely on manual verification for the final visual polish of hover, pressed, disabled, and expanded states.

## Impacted Files

- `src/ui/result_bar.py`
- `src/ui/translation_box.py`
- `tests/test_result_bar_toolbar.py`
- `tests/test_subtitle.py`
