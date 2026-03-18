# Global Button Style Variants Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a global button-style variant setting so every skin can switch between the Calm Hierarchy and Functional Color button systems from the Appearance settings, while unifying button typography and rolling out the approved geometric icon family.

**Architecture:** Keep the existing skin catalog intact and add a second configuration layer named `button_style_variant`. Theme composition should merge a base skin with variant-specific button token overrides, while shared button typography and icon helpers provide the consistent rendering layer used by the result bar, translation boxes, and settings-driven controls.

**Tech Stack:** Python, PyQt5, pytest

---

## Chunk 1: Persist the new global setting

### Task 1: Add settings coverage for `button_style_variant`

**Files:**
- Modify: `src/core/settings.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write the failing test**

Add tests asserting:

- the default variant is `calm`
- saving `button_style_variant` persists across `SettingsStore` reloads

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_settings.py -q`
Expected: FAIL because the setting is not in `DEFAULTS` yet.

- [ ] **Step 3: Write minimal implementation**

Add `button_style_variant` to `DEFAULTS` in [settings.py](/c:/Users/Administrator/my-todo/src/core/settings.py).

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_settings.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/settings.py tests/test_settings.py
git commit -m "test: add button style variant settings coverage"
```

## Chunk 2: Compose skins with button-style variants

### Task 2: Add theme composition and token tests

**Files:**
- Modify: `src/ui/theme.py`
- Create: `tests/test_theme_variants.py`

- [ ] **Step 1: Write the failing test**

Add tests asserting:

- `get_skin(...)` keeps base non-button tokens from the selected skin
- `calm` and `semantic` produce different button token values for the same base skin
- unknown variant values fall back safely to `calm`

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_theme_variants.py -q`
Expected: FAIL because variant composition does not exist yet.

- [ ] **Step 3: Write minimal implementation**

Update [theme.py](/c:/Users/Administrator/my-todo/src/ui/theme.py) to:

- define button-style variant override maps
- expose a composition path based on `skin` and `button_style_variant`
- keep base skin dictionaries immutable

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_theme_variants.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/theme.py tests/test_theme_variants.py
git commit -m "feat: compose skins with button style variants"
```

## Chunk 3: Expose the selector in Appearance settings

### Task 3: Add the new variant selector to the settings window

**Files:**
- Modify: `src/ui/settings_window.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write the failing test**

Add focused tests or UI-level assertions covering:

- settings window loads the saved `button_style_variant`
- saving the dialog writes the selected variant
- reset-to-default restores `calm`

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_settings.py -q`
Expected: FAIL because the selector is not present yet.

- [ ] **Step 3: Write minimal implementation**

Update [settings_window.py](/c:/Users/Administrator/my-todo/src/ui/settings_window.py) to:

- add a compact “按钮风格” section to the Appearance tab
- provide two explicit options:
  - `A · Calm Hierarchy`
  - `B · Functional Color`
- load, save, and reset `button_style_variant`

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_settings.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/settings_window.py tests/test_settings.py
git commit -m "feat: add button style selector to appearance settings"
```

## Chunk 4: Apply variants, typography, and icons across result bar and translation boxes

### Task 4: Verify composed tokens flow through existing button code and icon mappings

**Files:**
- Modify: `src/ui/result_bar.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Write the failing test**

Add focused assertions that construct widgets with both variants and verify:

- widget creation succeeds
- existing layout and ordering expectations still hold
- style application paths still run for both variants
- translation-box pin control no longer exposes the raw `钉` label
- clear action still exposes the custom broom icon in the idle state
- copy controls keep a consistent icon approach across result bar and translation box where applicable

- [ ] **Step 2: Run test to verify it fails**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: FAIL if any style path assumes a single skin-only model.
Expected: FAIL if icon or typography expectations are not yet encoded.

- [ ] **Step 3: Write minimal implementation**

Update [result_bar.py](/c:/Users/Administrator/my-todo/src/ui/result_bar.py) and [translation_box.py](/c:/Users/Administrator/my-todo/src/ui/translation_box.py) only where needed so they consistently consume the composed skin and remain stable under both variants.
Update [result_bar.py](/c:/Users/Administrator/my-todo/src/ui/result_bar.py) and [translation_box.py](/c:/Users/Administrator/my-todo/src/ui/translation_box.py) to:

- consume the composed skin under both variants
- apply the shared button typography choices
- use the approved geometric icon family
- keep the clear action on a broom icon
- replace the translation-box `钉` label with a pin icon

- [ ] **Step 4: Run test to verify it passes**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/ui/result_bar.py src/ui/translation_box.py tests/test_result_bar_toolbar.py tests/test_subtitle.py
git commit -m "feat: apply global button style variants to UI controls"
```

## Chunk 5: Final verification

### Task 5: Run complete verification for the variant system

**Files:**
- Modify: `src/core/settings.py`
- Modify: `src/ui/theme.py`
- Modify: `src/ui/settings_window.py`
- Modify: `src/ui/result_bar.py`
- Modify: `src/ui/translation_box.py`
- Modify: `tests/test_settings.py`
- Modify: `tests/test_theme_variants.py`
- Modify: `tests/test_result_bar_toolbar.py`
- Modify: `tests/test_subtitle.py`

- [ ] **Step 1: Run focused verification**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest tests/test_settings.py tests/test_theme_variants.py tests/test_result_bar_toolbar.py tests/test_subtitle.py -q`
Expected: PASS

- [ ] **Step 2: Run the full suite**

Run: `C:\Users\Administrator\AppData\Local\Python\bin\python.exe -m pytest -q`
Expected: PASS

- [ ] **Step 3: Perform manual UI verification**

Check:

- Appearance tab can switch skins independently from button variants
- both variants apply after save
- result bar and translation box visibly change button language while keeping layout stable
- unusual skins such as `matrix` and `rose` still maintain readable button contrast
- broom icon reads clearly for clear translation
- translation-box pin button reads clearly as a pin after replacing the text label
- button typography feels consistent across toolbar and action-row controls

- [ ] **Step 4: Commit**

```bash
git add src/core/settings.py src/ui/theme.py src/ui/settings_window.py src/ui/result_bar.py src/ui/translation_box.py tests/test_settings.py tests/test_theme_variants.py tests/test_result_bar_toolbar.py tests/test_subtitle.py
git commit -m "test: verify global button style variants"
```
