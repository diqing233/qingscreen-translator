# Font + Icon System Design

**Date:** 2026-03-19
**Project:** ScreenTranslator (`c:/Users/Administrator/my-todo`)
**Status:** Approved

## Goals

- Each skin has a default font that reinforces its aesthetic personality and optimizes readability
- Each skin has a default icon weight (Phosphor Icons) that matches its visual tone
- Users can override font set and icon set independently in Settings > Appearance
- Zero breaking changes to existing 164 tests

## Architecture: Four-Layer Skin Composition

`get_skin()` composes four layers in order:

```python
def get_skin(
    name: str,
    button_style_variant: str = DEFAULT_BUTTON_STYLE_VARIANT,
    font_set: str | None = None,
    icon_set: str | None = None,
) -> dict:
    skin = dict(SKINS[name])
    fs = font_set or skin.get('default_font_set', 'sans')
    skin.update(FONT_SETS[fs])
    ic = icon_set or skin.get('default_icon_set', 'phosphor-regular')
    skin.update(ICON_SETS[ic])
    skin.update(BUTTON_STYLE_VARIANTS.get(button_style_variant, ...))
    return skin
```

Layer order (later layers win on key conflicts):
1. Base skin (colors, radius, etc.)
2. Font set (font_family, font sizes)
3. Icon set (icon_font, icon codepoints)
4. Button style variant (button colors, button font sizes)

## Font Sets

Five named font sets bundled as `.ttf` files under `assets/fonts/`:

| Key | Primary Font | CJK Fallback | Personality |
|-----|-------------|--------------|-------------|
| `sans` | Noto Sans SC | — (native CJK) | Clean, neutral, readable |
| `mono` | JetBrains Mono | Noto Sans SC | Terminal, technical |
| `rounded` | Nunito | Noto Sans SC | Soft, friendly, cute |
| `serif` | Noto Serif SC | — (native CJK) | Literary, organic |
| `display` | Orbitron | Noto Sans SC | Futuristic, sci-fi |

### Font Set Tokens (per set, 6 tokens)

```python
{
    'font_family': str,             # CSS font-family string with fallbacks
    'font_size_translation': int,   # main translation label (px)
    'font_size_ui': int,            # general UI text (px)
    'font_size_small': int,         # secondary/muted labels (px)
    'font_weight_translation': int, # translation text weight: 400 or 500
    'font_weight_ui': int,          # UI button/label weight: 400 or 600
}
```

### Skin → Font Set Mapping

| Font Set | Skins |
|----------|-------|
| `sans` | 深空暗夜, 霜雾玻璃, 玫瑰晶, 御剑蓝, 珊瑚暖阳, 极简商务, 薄荷清风, 清纯校园 |
| `mono` | 黑客矩阵, 复古琥珀 |
| `rounded` | 可爱动物 |
| `serif` | 国风水墨, 北欧森林 |
| `display` | 赛博朋克 |

## Icon Sets

Phosphor Icons font, three weight variants:

| Key | Weight | Font Family Name | Skins |
|-----|--------|-----------------|-------|
| `phosphor-light` | light | `"Phosphor Light"` | 国风水墨, 极简商务 |
| `phosphor-regular` | regular | `"Phosphor"` | 深空暗夜, 霜雾玻璃, 玫瑰晶, 御剑蓝, 珊瑚暖阳, 薄荷清风, 清纯校园, 可爱动物, 北欧森林 |
| `phosphor-bold` | bold | `"Phosphor Bold"` | 黑客矩阵, 复古琥珀, 赛博朋克 |

Each weight is a separate `.ttf` file registered as a distinct font family via `QFontDatabase.addApplicationFont()`. `QFont("Phosphor Light")` constructs the light variant; no weight parameter needed.

### Icon Set Tokens

```python
{
    'icon_font': str,          # registered font family name
    'icon_weight': str,        # 'light' | 'regular' | 'bold'
    'icon_size_toolbar': int,  # toolbar button icon size (px)
    'icon_size_action': int,   # action button icon size (px)
    # codepoints for all required icons:
    'icon_copy': str,
    'icon_close': str,
    'icon_translate': str,
    'icon_ai': str,
    'icon_pin': str,
    'icon_unpin': str,
    'icon_expand': str,
    'icon_collapse': str,
    'icon_font_up': str,    # existing A+ button (result_bar.py:553) → Phosphor text-increase icon
    'icon_font_down': str,  # existing A- button (result_bar.py:549) → Phosphor text-decrease icon
    'icon_settings': str,
    'icon_history': str,
}
```

## New Skin: 清纯校园 (`campus`)

Light mode skin with sky-blue + white + warm-yellow palette.

```python
'campus': {
    'name': '清纯校园',
    'description': '天空蓝白，青春制服感',
    'dark': False,
    'bg_rgb': (240, 248, 255),
    'border': 'rgba(80,140,240,30)',
    'radius': 8,
    'default_font_set': 'sans',
    'default_icon_set': 'phosphor-regular',
    # Full 63-token color set follows the same structure as existing light-mode skins
    # (e.g. coral, mint). Primary accent: #5090f0 (sky blue), secondary: #ffb43c (warm yellow).
    # Implementation: copy coral skin token-for-token, substitute blue/yellow for orange/amber.
    # This is a mechanical color substitution — no design decisions required.
    # All 63 token names and their roles are identical to coral; only the rgba values change.
    'swatch': ('#f0f8ff', '#5090f0', '#ffb43c'),
}
```

## Settings Storage

`~/.screen_translator/settings.json` gains two optional fields:

```json
{
  "font_set": null,
  "icon_set": null
}
```

`null` means "follow skin default". Non-null overrides for all skins.

## Settings UI

In `settings_window.py`, Appearance tab gains two new `QGroupBox` sections below Button Style:

**Font group:**
- Label: "字体集"
- Control: `QComboBox` with options: "跟随皮肤默认", "Sans · Noto Sans SC", "Mono · JetBrains Mono", "Rounded · Nunito", "Serif · Noto Serif SC", "Display · Orbitron"
- Hint label: shows current skin's default font

**Icons group:**
- Label: "图标集"
- Control: `QComboBox` with options: "跟随皮肤默认", "Phosphor Light", "Phosphor Regular", "Phosphor Bold"
- Hint label: shows current skin's default icon weight

## Files Changed

### New Files
```
assets/fonts/
  NotoSansSC-Regular.ttf
  NotoSansSC-Medium.ttf
  NotoSerifSC-Regular.ttf
  JetBrainsMono-Regular.ttf
  Nunito-Regular.ttf
  Orbitron-Regular.ttf
  Phosphor-Light.ttf
  Phosphor-Regular.ttf
  Phosphor-Bold.ttf
```

### Modified Files

| File | Changes |
|------|---------|
| `src/ui/theme.py` | Add `FONT_SETS`, `ICON_SETS`, `campus` skin; add `default_font_set`/`default_icon_set` to all skins; extend `get_skin()` |
| `src/main.py` | Register all font files via `QFontDatabase.addApplicationFont()` at startup |
| `src/core/settings.py` | Add `font_set: null`, `icon_set: null` to DEFAULTS |
| `src/ui/settings_window.py` | Add Font + Icons group boxes to Appearance tab |
| `src/ui/result_bar.py` | Consume `font_family`/`font_size_translation` tokens; migrate QPainter icon methods (`_draw_copy`, `_draw_close`, etc.) to Phosphor font text — existing `_draw_*` methods are deleted, not kept as fallback |
| `src/ui/translation_box.py` | Same font token consumption; same QPainter icon migration strategy |

## Testing

- Existing 164 tests: no changes required. The `_draw_*` methods (`_draw_copy`, `_draw_close`, etc.) are private QPainter helpers with no direct test coverage (confirmed: `grep -r "_draw_" tests/` returns no matches). Tests cover widget behavior, not drawing implementation details.
- New tests (~10): font set composition, icon set composition, campus skin token completeness, settings serialization for font_set/icon_set, font registration at startup
