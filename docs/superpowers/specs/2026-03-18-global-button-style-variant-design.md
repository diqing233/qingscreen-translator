# Global Button Style Variant Design

**Date:** 2026-03-18

## Goal

Keep both approved button directions and let the user switch between them from the Appearance settings.

The switch should be global, not result-bar-only:

- result bar
- floating translation boxes
- settings window and other skin-driven widgets

The approved direction is to keep the existing skin system and add a second layer for button styling variants.

## Context

The current UI already has a global skin system:

- [theme.py](/c:/Users/Administrator/my-todo/src/ui/theme.py) defines skin tokens
- [settings.py](/c:/Users/Administrator/my-todo/src/core/settings.py) persists the selected `skin`
- [settings_window.py](/c:/Users/Administrator/my-todo/src/ui/settings_window.py) exposes the Appearance tab
- [result_bar.py](/c:/Users/Administrator/my-todo/src/ui/result_bar.py) and [translation_box.py](/c:/Users/Administrator/my-todo/src/ui/translation_box.py) both read button colors from `get_skin(...)`

That means the safest way to preserve A and B is not to duplicate the full theme catalog. Instead, keep each base skin and overlay a button-style variant on top of it.

## Approaches Considered

### 1. Recommended: `skin + button_style_variant`

- Keep the current base skin selection unchanged
- Add a new global setting such as `button_style_variant`
- Compose final UI tokens from:
  - base skin tokens
  - variant-specific button overrides

**Pros:**

- preserves the current skin system
- keeps the Appearance tab understandable
- scales cleanly across all skins
- avoids duplicating every existing theme

**Cons:**

- requires a small theme-composition layer instead of plain dictionary lookup

### 2. Duplicate every skin into A and B versions

- Example: `deep_space_calm`, `deep_space_semantic`, `rose_calm`, `rose_semantic`

**Pros:**

- straightforward lookup logic

**Cons:**

- theme count doubles immediately
- ongoing maintenance becomes expensive
- Appearance UI gets cluttered fast

### 3. Hardcode A/B branches inside widgets

- Add conditional button styling logic in each widget

**Pros:**

- low upfront code movement

**Cons:**

- does not behave like a real global appearance setting
- easy for widgets to drift apart
- poor long-term maintainability

## Decision

Use approach 1.

The final appearance model becomes:

- `skin`: controls overall visual environment
- `button_style_variant`: controls button semantics and button emphasis

## Variant Model

Add two global variants:

- `calm`
- `semantic`

### `calm`

- preserve the current dark utility feeling
- rely mostly on elevation and contrast shifts
- keep most utility buttons restrained
- let only true primary, mode, and danger actions carry strong emphasis

### `semantic`

- keep the same structural layout and base skin
- make button purpose more obvious through semantic accent groups
- translation flow stays blue-led
- AI actions move toward teal/green
- warning or overlay-related actions can carry amber attention
- danger remains warm red
- neutral utility actions stay subdued but distinct from content

## Theme Architecture

### Base Principle

Base skins remain the single source of truth for:

- container backgrounds
- borders
- text colors
- editor backgrounds
- overlay surfaces
- scrollbars
- swatches and skin card previews

Button variants override only button-related tokens and closely related accent tokens.

### Recommended Token Boundary

Existing tokens already group buttons well enough for a variant layer to override selectively:

- `btn_bg`
- `btn_border`
- `btn_fg`
- `btn_hover`
- `btn_disabled_bg`
- `btn_disabled_fg`
- `btn_active_bg`
- `btn_active_border`
- `btn_active_fg`
- `btn_active_hover`
- `btn_primary_bg`
- `btn_primary_border`
- `btn_primary_hover`
- `btn_danger_bg`
- `btn_danger_border`
- `btn_danger_hover`
- `btn_stop_bg`
- `btn_stop_border`
- `btn_stop_hover`
- `btn_mode_active_bg`
- `btn_mode_active_border`
- `btn_mode_active_hover`
- `toggle_manual`
- `toggle_auto`
- `split_bg`
- `split_border`
- `split_active_bg`
- `split_active_border`
- `split_text`

The implementation should compose tokens rather than mutate the base `SKINS` dictionaries in place.

## Settings UX

The Appearance tab should keep the existing skin card grid and add a second control group for button style.

Recommended layout:

1. Short Appearance intro text
2. Skin card grid
3. New “按钮风格” selector with two explicit options:
   - `A · Calm Hierarchy`
   - `B · Functional Color`

The selector should explain that:

- skin controls the overall window palette
- button style controls the emphasis language of interactive controls

This avoids teaching users that A and B are separate full themes.

## Widget Scope

The variant should apply anywhere buttons already use `get_skin(...)` output:

- result bar toolbar buttons
- result bar action-row buttons
- split buttons and toggle controls
- floating translation-box buttons
- settings-window buttons that are meant to follow global styling

Window layout and behavior must not change as part of this work.

## Behavior Rules

- changing the variant must take effect after saving settings just like skin changes do now
- existing layout, ordering, and signals must remain unchanged
- busy and disabled states must remain more important than pure stylistic differences
- semantic coloring must not reduce readability on niche skins such as `matrix` or `rose`

## Testing

### Settings Persistence

Extend [test_settings.py](/c:/Users/Administrator/my-todo/tests/test_settings.py) to cover:

- default `button_style_variant`
- persistence after saving

### Theme Composition

Add focused tests for theme composition logic:

- base skin tokens remain available
- variant-specific button tokens differ between `calm` and `semantic`
- non-button tokens stay inherited from the selected skin

### UI Integration

Extend existing UI tests to verify:

- settings window loads and saves the new selector
- result bar and translation box continue to construct correctly with either variant
- no control ordering or enable/disable behavior regresses

Visual exact-color assertions are not required; behavior and token selection are the important automated checks.

## Risks

### Contrast drift on non-default skins

`semantic` may look good on `deep_space` but fail on `matrix` or `rose` if it is implemented as raw color substitution without contrast tuning.

Mitigation:

- define variant overrides per token family
- keep text and disabled contrast explicit

### Appearance settings confusion

Users may assume the new selector replaces skins rather than modifies button behavior.

Mitigation:

- use precise labels and helper copy in the Appearance tab

## Out of Scope

- replacing all icons in this task
- redesigning layout or panel ordering
- changing translation workflows
- adding live preview inside the settings dialog unless it becomes necessary during implementation
