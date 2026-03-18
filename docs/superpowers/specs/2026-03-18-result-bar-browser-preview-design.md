# Result Bar Browser Preview Design

**Date:** 2026-03-18

## Goal

Create a browser-based preview that lets the user compare two button styling directions for the result bar:

- `Calm Hierarchy`: keep the current dark utility feel and strengthen hierarchy with restrained emphasis
- `Functional Color`: keep the compact desktop density but make button meaning more obvious through semantic color

The preview should feel close to the real result bar instead of showing isolated chips only.

## Context

The current PyQt result bar already has a clear functional grouping in [src/ui/result_bar.py](/c:/Users/Administrator/my-todo/src/ui/result_bar.py):

- start / stop / reset controls
- box mode and AI mode controls
- source and target language controls
- utility actions in the toolbar
- source / retranslate / AI actions in the lower action row
- expanded source and AI panels

The user wants to review styling directions visually in a browser before deciding which direction to carry into the real UI.

## Approaches Considered

### 1. Recommended: Full scenario preview plus button lab

- Show two full result-bar mockups side by side
- Include realistic states: idle, busy, source expanded, AI expanded
- Add a dedicated button-state board for each function group

**Pros:** Closest to real usage while still making single-button differences easy to inspect.

**Cons:** Slightly more work than a pure button gallery.

### 2. Full result-bar comparison only

- Show only complete mockups of the two directions

**Pros:** Fast and realistic.

**Cons:** Harder to inspect per-button hover, disabled, and active treatments.

### 3. Button lab only

- Show every button as a state grid without the surrounding result-bar frame

**Pros:** Precise comparison of individual controls.

**Cons:** Too detached from the actual tool.

## Decision

Use approach 1.

The preview should answer both questions at once:

- what each direction feels like in context
- how each button family behaves by function

## Preview Scope

The browser preview should include:

- two side-by-side result-bar mockups, one per direction
- a top toolbar row with start, stop/clear, reset, mode, language, copy/history/settings/window controls
- a lower action row with source, copy source, retranslate, AI split button, and paragraph numbering
- translation content, backend label, source panel, and AI panel
- a grouped button board that shows each control family in multiple states

## Visual Direction A: Calm Hierarchy

- Keep the current deep-space desktop-tool atmosphere.
- Use graphite and slate neutrals for most controls.
- Reserve strong blue emphasis for the primary “start/select” action and true mode toggles.
- Keep warm red/orange for stop, close, or other destructive actions only.
- Treat expand buttons such as source and AI as calm secondary controls with mild lift on active.

This direction should feel closer to the current product, just cleaner and more intentional.

## Visual Direction B: Functional Color

- Keep the same compact density and structure.
- Use semantic color groups so function is legible at a glance.
- Blue family: start, translate, box-mode flow
- Green or teal family: AI and explain actions
- Amber family: overlay or attention-related controls
- Neutral steel family: language, copy, history, settings, paragraph numbering
- Warm danger family: stop, close

This direction should feel more “instrument panel” than “quiet utility”.

## Interaction Rules

- Every clickable control should show clear hover and focus treatment.
- Active states should be stable and not depend on hover alone.
- Disabled buttons should still look intentional, especially retranslate when no edits exist.
- Split-button regions must remain visually distinguishable on the preview.
- Hover effects should lift color or glow subtly without shifting layout.

## Technical Design

Build the preview as a standalone generated artifact rather than editing the live PyQt widgets first.

- Use a small Python generator to describe button groups, states, and mock content
- Render one static HTML file with embedded CSS and lightweight JS for state toggles
- Store the generated preview in a standalone folder so it does not interfere with app code

This keeps the work reversible and safe while the real `result_bar.py` is still in active development.

## Verification

- Verify the generated page contains both directions and all required control groups.
- Verify the preview renders locally in a browser.
- Verify the button-state board includes normal, hover, pressed, active, and disabled examples where relevant.
- Verify the full mockups include the expanded source and AI sections.
