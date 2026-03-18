# Theme System Expansion — 8 New Skins

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan.

**Goal:** Add 8 new skins to `src/ui/theme.py` using the flat-extension approach (Option A from brainstorm), keeping existing 5 skins intact. Update settings window to show all skins with live swatches.

**Architecture:** Each new skin is a complete flat dict with all tokens (colors + `swatch`). No structural changes to `get_skin()` or consuming code. Tests follow TDD.

**Tech Stack:** Python, PyQt5, pytest
**Worktree:** `.worktrees/theme-system` on branch `feature/theme-system`

---

## Task 1: Add `minimal` and `coral` skins

**Files:**
- Modify: `src/ui/theme.py`
- Modify: `tests/test_theme_variants.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting:
- `get_skin('minimal')` returns a dict with `dark == False`, `bg_rgb == (248, 249, 250)`, and `btn_primary_bg` containing `26,26,46`
- `get_skin('coral')` returns a dict with `dark == False`, `bg_rgb == (255, 245, 230)`, and `btn_primary_bg` containing `232,96,26`
- Both skins appear in `list_skins()`

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 3: Implement**

Add to `SKINS` in `src/ui/theme.py`:

**`minimal`** (极简商务，浅色):
```python
'minimal': {
    'name': '极简商务', 'description': '干净利落，专业高效', 'dark': False,
    'bg_rgb': (248, 249, 250), 'border': 'rgba(26,26,46,18)', 'radius': 3,
    'text': '#1a1a2e', 'text_muted': 'rgba(80,80,110,210)', 'text_ocr': 'rgba(40,40,80,160)',
    'btn_bg': 'rgba(230,232,238,200)', 'btn_border': 'rgba(26,26,46,30)',
    'btn_fg': 'rgba(26,26,46,220)', 'btn_hover': 'rgba(210,215,228,220)',
    'btn_disabled_bg': 'rgba(220,222,228,100)', 'btn_disabled_fg': 'rgba(100,100,120,120)',
    'btn_active_bg': 'rgba(26,26,46,180)', 'btn_active_border': 'rgba(74,157,156,120)',
    'btn_active_fg': 'rgba(255,255,255,240)', 'btn_active_hover': 'rgba(40,40,70,200)',
    'btn_primary_bg': 'rgba(26,26,46,210)', 'btn_primary_border': 'rgba(74,157,156,160)',
    'btn_primary_hover': 'rgba(40,40,80,230)',
    'btn_danger_bg': 'rgba(229,57,53,180)', 'btn_danger_border': 'rgba(229,57,53,120)',
    'btn_danger_hover': 'rgba(211,47,47,200)',
    'btn_stop_bg': 'rgba(229,57,53,180)', 'btn_stop_border': 'rgba(229,57,53,120)',
    'btn_stop_hover': 'rgba(211,47,47,200)',
    'btn_mode_active_bg': 'rgba(26,26,46,200)', 'btn_mode_active_border': 'rgba(74,157,156,150)',
    'btn_mode_active_hover': 'rgba(40,40,80,220)',
    'box_border_temp': (26, 26, 46, 120), 'box_border_fixed': (26, 26, 46, 200),
    'box_fill': (240, 242, 248, 8),
    'overlay_bg': (240, 242, 248, 240), 'overlay_text': '#1a1a2e',
    'overlay_border': (26, 26, 46, 80),
    'overlay_below_bg': (235, 237, 245, 232), 'overlay_below_text': '#1a1a2e',
    'overlay_below_border': (26, 26, 46, 60),
    'toggle_track': (220, 222, 230, 220), 'toggle_track_border': (26, 26, 46, 30),
    'toggle_manual': (26, 26, 46, 220), 'toggle_auto': (74, 157, 156, 220),
    'split_bg': (225, 228, 236, 200), 'split_border': (26, 26, 46, 30),
    'split_active_bg': (26, 26, 46, 180), 'split_active_border': (74, 157, 156, 120),
    'split_text': (26, 26, 46, 230),
    'menu_bg': 'rgba(240,242,248,245)', 'menu_text': 'rgba(26,26,46,230)',
    'menu_border': 'rgba(26,26,46,30)', 'menu_selected': 'rgba(26,26,46,180)',
    'menu_checked': 'rgba(26,26,90,255)',
    'scrollbar_bg': 'rgba(26,26,46,8)', 'scrollbar_handle': 'rgba(26,26,46,40)',
    'sep_color': 'rgba(26,26,46,15)',
    'source_editor_bg': 'rgba(26,26,46,6)', 'source_editor_border': 'rgba(26,26,46,25)',
    'source_editor_text': 'rgba(26,26,46,220)',
    'explain_bg': 'rgba(74,157,156,8)', 'explain_text': 'rgba(20,60,80,220)',
    'swatch': ('#f8f9fa', '#1a1a2e', '#4a9d9c'),
}
```

**`coral`** (珊瑚暖阳，浅色):
```python
'coral': {
    'name': '珊瑚暖阳', 'description': '活力四射，橘色暖白', 'dark': False,
    'bg_rgb': (255, 245, 230), 'border': 'rgba(232,96,26,25)', 'radius': 8,
    'text': '#4a1a00', 'text_muted': 'rgba(160,88,40,210)', 'text_ocr': 'rgba(120,60,20,160)',
    'btn_bg': 'rgba(255,220,180,190)', 'btn_border': 'rgba(232,96,26,35)',
    'btn_fg': 'rgba(74,26,0,220)', 'btn_hover': 'rgba(255,200,150,215)',
    'btn_disabled_bg': 'rgba(255,220,180,100)', 'btn_disabled_fg': 'rgba(160,100,60,110)',
    'btn_active_bg': 'rgba(232,96,26,180)', 'btn_active_border': 'rgba(255,179,71,130)',
    'btn_active_fg': 'rgba(255,255,255,240)', 'btn_active_hover': 'rgba(210,80,10,200)',
    'btn_primary_bg': 'rgba(232,96,26,210)', 'btn_primary_border': 'rgba(255,140,60,160)',
    'btn_primary_hover': 'rgba(210,80,10,230)',
    'btn_danger_bg': 'rgba(200,40,40,180)', 'btn_danger_border': 'rgba(220,80,80,120)',
    'btn_danger_hover': 'rgba(180,30,30,200)',
    'btn_stop_bg': 'rgba(200,40,40,180)', 'btn_stop_border': 'rgba(220,80,80,120)',
    'btn_stop_hover': 'rgba(180,30,30,200)',
    'btn_mode_active_bg': 'rgba(232,96,26,200)', 'btn_mode_active_border': 'rgba(255,140,60,150)',
    'btn_mode_active_hover': 'rgba(210,80,10,220)',
    'box_border_temp': (232, 150, 80, 140), 'box_border_fixed': (232, 96, 26, 200),
    'box_fill': (255, 240, 200, 8),
    'overlay_bg': (255, 245, 225, 238), 'overlay_text': '#4a1a00',
    'overlay_border': (232, 96, 26, 90),
    'overlay_below_bg': (250, 238, 215, 230), 'overlay_below_text': '#4a1a00',
    'overlay_below_border': (210, 80, 10, 70),
    'toggle_track': (255, 215, 165, 220), 'toggle_track_border': (232, 96, 26, 30),
    'toggle_manual': (232, 96, 26, 220), 'toggle_auto': (100, 180, 80, 220),
    'split_bg': (255, 215, 170, 200), 'split_border': (232, 96, 26, 35),
    'split_active_bg': (232, 96, 26, 185), 'split_active_border': (255, 140, 60, 130),
    'split_text': (74, 26, 0, 230),
    'menu_bg': 'rgba(255,245,225,245)', 'menu_text': 'rgba(74,26,0,230)',
    'menu_border': 'rgba(232,96,26,30)', 'menu_selected': 'rgba(232,96,26,180)',
    'menu_checked': 'rgba(180,60,0,255)',
    'scrollbar_bg': 'rgba(232,96,26,8)', 'scrollbar_handle': 'rgba(232,96,26,45)',
    'sep_color': 'rgba(232,96,26,18)',
    'source_editor_bg': 'rgba(232,96,26,6)', 'source_editor_border': 'rgba(232,96,26,28)',
    'source_editor_text': 'rgba(74,26,0,220)',
    'explain_bg': 'rgba(255,200,100,10)', 'explain_text': 'rgba(100,40,0,220)',
    'swatch': ('#fff5e6', '#e8601a', '#ffb347'),
}
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 5: Commit**

```
git add src/ui/theme.py tests/test_theme_variants.py
git commit -m "feat: add minimal and coral skins"
```

---

## Task 2: Add `forest` and `retro` skins

**Files:**
- Modify: `src/ui/theme.py`
- Modify: `tests/test_theme_variants.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting:
- `get_skin('forest')` returns `dark == True`, `bg_rgb == (26, 46, 26)`, `btn_primary_bg` containing `76,175,80`
- `get_skin('retro')` returns `dark == True`, `bg_rgb == (42, 26, 8)`, `btn_primary_bg` containing `200,134,10`
- Both in `list_skins()`

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 3: Implement**

**`forest`** (北欧森林，暗色):
```python
'forest': {
    'name': '北欧森林', 'description': '护眼自然，有机木质感', 'dark': True,
    'bg_rgb': (26, 46, 26), 'border': 'rgba(76,175,80,40)', 'radius': 8,
    'text': '#c8e6c9', 'text_muted': 'rgba(165,214,167,215)', 'text_ocr': 'rgba(200,230,200,160)',
    'btn_bg': 'rgba(36,66,36,195)', 'btn_border': 'rgba(76,175,80,35)',
    'btn_fg': 'rgba(200,230,201,220)', 'btn_hover': 'rgba(50,88,50,215)',
    'btn_disabled_bg': 'rgba(24,44,24,110)', 'btn_disabled_fg': 'rgba(100,140,100,110)',
    'btn_active_bg': 'rgba(46,110,46,200)', 'btn_active_border': 'rgba(102,187,106,90)',
    'btn_active_fg': 'rgba(232,245,233,236)', 'btn_active_hover': 'rgba(56,130,56,220)',
    'btn_primary_bg': 'rgba(76,175,80,200)', 'btn_primary_border': 'rgba(129,199,132,160)',
    'btn_primary_hover': 'rgba(102,187,106,220)',
    'btn_danger_bg': 'rgba(255,112,67,180)', 'btn_danger_border': 'rgba(255,138,101,120)',
    'btn_danger_hover': 'rgba(244,81,30,200)',
    'btn_stop_bg': 'rgba(255,112,67,180)', 'btn_stop_border': 'rgba(255,138,101,120)',
    'btn_stop_hover': 'rgba(244,81,30,200)',
    'btn_mode_active_bg': 'rgba(76,175,80,200)', 'btn_mode_active_border': 'rgba(129,199,132,155)',
    'btn_mode_active_hover': 'rgba(102,187,106,220)',
    'box_border_temp': (140, 195, 140, 150), 'box_border_fixed': (76, 175, 80, 200),
    'box_fill': (20, 40, 20, 4),
    'overlay_bg': (20, 36, 20, 244), 'overlay_text': '#dcedc8',
    'overlay_border': (100, 180, 100, 110),
    'overlay_below_bg': (20, 36, 20, 232), 'overlay_below_text': '#c8e6c9',
    'overlay_below_border': (80, 160, 80, 90),
    'toggle_track': (30, 54, 30, 228), 'toggle_track_border': (76, 175, 80, 35),
    'toggle_manual': (76, 175, 80, 220), 'toggle_auto': (139, 195, 74, 220),
    'split_bg': (36, 64, 36, 192), 'split_border': (76, 175, 80, 35),
    'split_active_bg': (48, 110, 48, 200), 'split_active_border': (102, 187, 106, 90),
    'split_text': (200, 230, 201, 236),
    'menu_bg': 'rgba(22,40,22,240)', 'menu_text': 'rgba(200,230,201,230)',
    'menu_border': 'rgba(76,175,80,40)', 'menu_selected': 'rgba(76,175,80,180)',
    'menu_checked': 'rgba(165,214,167,255)',
    'scrollbar_bg': 'rgba(76,175,80,8)', 'scrollbar_handle': 'rgba(76,175,80,50)',
    'sep_color': 'rgba(76,175,80,25)',
    'source_editor_bg': 'rgba(30,54,30,200)', 'source_editor_border': 'rgba(76,175,80,35)',
    'source_editor_text': 'rgba(200,230,201,220)',
    'explain_bg': 'rgba(30,54,30,200)', 'explain_text': 'rgba(180,230,180,210)',
    'swatch': ('#1a2e1a', '#4caf50', '#8bc34a'),
}
```

**`retro`** (复古琥珀，暗色):
```python
'retro': {
    'name': '复古琥珀', 'description': '老式终端质感，复古情怀', 'dark': True,
    'bg_rgb': (42, 26, 8), 'border': 'rgba(200,134,10,40)', 'radius': 4,
    'text': '#f0c060', 'text_muted': 'rgba(212,160,96,215)', 'text_ocr': 'rgba(220,175,90,160)',
    'btn_bg': 'rgba(66,42,14,195)', 'btn_border': 'rgba(200,134,10,38)',
    'btn_fg': 'rgba(240,192,96,220)', 'btn_hover': 'rgba(86,56,18,215)',
    'btn_disabled_bg': 'rgba(44,28,8,110)', 'btn_disabled_fg': 'rgba(140,100,40,110)',
    'btn_active_bg': 'rgba(120,80,10,200)', 'btn_active_border': 'rgba(212,160,60,90)',
    'btn_active_fg': 'rgba(255,220,120,236)', 'btn_active_hover': 'rgba(140,96,12,220)',
    'btn_primary_bg': 'rgba(200,134,10,200)', 'btn_primary_border': 'rgba(230,175,60,160)',
    'btn_primary_hover': 'rgba(218,150,12,220)',
    'btn_danger_bg': 'rgba(160,50,20,180)', 'btn_danger_border': 'rgba(210,90,50,120)',
    'btn_danger_hover': 'rgba(180,60,24,200)',
    'btn_stop_bg': 'rgba(160,50,20,180)', 'btn_stop_border': 'rgba(210,90,50,120)',
    'btn_stop_hover': 'rgba(180,60,24,200)',
    'btn_mode_active_bg': 'rgba(200,134,10,200)', 'btn_mode_active_border': 'rgba(230,175,60,155)',
    'btn_mode_active_hover': 'rgba(218,150,12,220)',
    'box_border_temp': (200,160,80,140), 'box_border_fixed': (200,134,10,200),
    'box_fill': (40,24,4,4),
    'overlay_bg': (36,22,4,244), 'overlay_text': '#ffd060',
    'overlay_border': (200,150,60,110),
    'overlay_below_bg': (36,22,4,232), 'overlay_below_text': '#e8b848',
    'overlay_below_border': (180,130,40,90),
    'toggle_track': (52,32,10,228), 'toggle_track_border': (200,134,10,38),
    'toggle_manual': (200,134,10,220), 'toggle_auto': (139,100,30,220),
    'split_bg': (62,40,12,192), 'split_border': (200,134,10,38),
    'split_active_bg': (118,78,10,200), 'split_active_border': (212,160,60,90),
    'split_text': (240,192,96,236),
    'menu_bg': 'rgba(36,22,4,240)', 'menu_text': 'rgba(240,192,96,230)',
    'menu_border': 'rgba(200,134,10,42)', 'menu_selected': 'rgba(180,120,10,180)',
    'menu_checked': 'rgba(255,210,80,255)',
    'scrollbar_bg': 'rgba(200,134,10,8)', 'scrollbar_handle': 'rgba(200,134,10,50)',
    'sep_color': 'rgba(200,134,10,25)',
    'source_editor_bg': 'rgba(56,36,10,200)', 'source_editor_border': 'rgba(200,134,10,38)',
    'source_editor_text': 'rgba(240,192,96,220)',
    'explain_bg': 'rgba(56,36,10,200)', 'explain_text': 'rgba(255,210,100,210)',
    'swatch': ('#2a1a08', '#c8860a', '#d4a060'),
}
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 5: Commit**

```
git add src/ui/theme.py tests/test_theme_variants.py
git commit -m "feat: add forest and retro skins"
```

---

## Task 3: Add `cyberpunk`, `ink`, `mint` skins

**Files:**
- Modify: `src/ui/theme.py`
- Modify: `tests/test_theme_variants.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting:
- `get_skin('cyberpunk')` returns `dark == True`, `bg_rgb == (10, 0, 24)`, `text == '#ff00ff'`
- `get_skin('ink')` returns `dark == False`, `bg_rgb == (245, 240, 232)`, `text == '#2c1a00'`
- `get_skin('mint')` returns `dark == False`, `bg_rgb == (232, 250, 244)`, `btn_primary_bg` containing `0,137,123`
- All three in `list_skins()`

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 3: Implement**

**`cyberpunk`** (赛博朋克，暗色):
```python
'cyberpunk': {
    'name': '赛博朋克', 'description': '霓虹都市，未来感极强', 'dark': True,
    'bg_rgb': (10, 0, 24), 'border': 'rgba(255,0,255,40)', 'radius': 0,
    'text': '#ff00ff', 'text_muted': 'rgba(0,255,255,200)', 'text_ocr': 'rgba(255,0,255,160)',
    'btn_bg': 'rgba(30,0,60,200)', 'btn_border': 'rgba(255,0,255,50)',
    'btn_fg': 'rgba(255,0,255,220)', 'btn_hover': 'rgba(50,0,90,220)',
    'btn_disabled_bg': 'rgba(18,0,36,110)', 'btn_disabled_fg': 'rgba(130,0,130,110)',
    'btn_active_bg': 'rgba(0,60,80,200)', 'btn_active_border': 'rgba(0,255,255,80)',
    'btn_active_fg': 'rgba(0,255,255,240)', 'btn_active_hover': 'rgba(0,80,100,220)',
    'btn_primary_bg': 'rgba(255,0,255,180)', 'btn_primary_border': 'rgba(255,100,255,160)',
    'btn_primary_hover': 'rgba(255,50,255,200)',
    'btn_danger_bg': 'rgba(255,255,0,160)', 'btn_danger_border': 'rgba(255,255,100,120)',
    'btn_danger_hover': 'rgba(220,220,0,180)',
    'btn_stop_bg': 'rgba(255,255,0,160)', 'btn_stop_border': 'rgba(255,255,100,120)',
    'btn_stop_hover': 'rgba(220,220,0,180)',
    'btn_mode_active_bg': 'rgba(0,255,255,160)', 'btn_mode_active_border': 'rgba(100,255,255,140)',
    'btn_mode_active_hover': 'rgba(0,220,220,180)',
    'box_border_temp': (255, 0, 255, 150), 'box_border_fixed': (0, 255, 255, 200),
    'box_fill': (10, 0, 24, 4),
    'overlay_bg': (8, 0, 20, 248), 'overlay_text': '#00ffff',
    'overlay_border': (255, 0, 255, 110),
    'overlay_below_bg': (8, 0, 20, 235), 'overlay_below_text': '#ff00ff',
    'overlay_below_border': (0, 255, 255, 90),
    'toggle_track': (20, 0, 44, 228), 'toggle_track_border': (255, 0, 255, 40),
    'toggle_manual': (255, 0, 255, 220), 'toggle_auto': (0, 255, 255, 220),
    'split_bg': (28, 0, 56, 200), 'split_border': (255, 0, 255, 50),
    'split_active_bg': (0, 50, 70, 200), 'split_active_border': (0, 255, 255, 80),
    'split_text': (255, 0, 255, 236),
    'menu_bg': 'rgba(12,0,28,245)', 'menu_text': 'rgba(255,0,255,230)',
    'menu_border': 'rgba(255,0,255,50)', 'menu_selected': 'rgba(255,0,255,160)',
    'menu_checked': 'rgba(0,255,255,255)',
    'scrollbar_bg': 'rgba(255,0,255,8)', 'scrollbar_handle': 'rgba(255,0,255,55)',
    'sep_color': 'rgba(255,0,255,25)',
    'source_editor_bg': 'rgba(20,0,50,200)', 'source_editor_border': 'rgba(255,0,255,45)',
    'source_editor_text': 'rgba(255,0,255,220)',
    'explain_bg': 'rgba(0,30,50,200)', 'explain_text': 'rgba(0,255,255,210)',
    'swatch': ('#0a0018', '#ff00ff', '#00ffff'),
}
```

**`ink`** (国风水墨，浅色):
```python
'ink': {
    'name': '国风水墨', 'description': '宣纸米白，朱砂点缀', 'dark': False,
    'bg_rgb': (245, 240, 232), 'border': 'rgba(44,26,0,18)', 'radius': 2,
    'text': '#2c1a00', 'text_muted': 'rgba(122,80,48,210)', 'text_ocr': 'rgba(80,50,20,160)',
    'btn_bg': 'rgba(220,210,192,195)', 'btn_border': 'rgba(44,26,0,30)',
    'btn_fg': 'rgba(44,26,0,220)', 'btn_hover': 'rgba(200,188,168,215)',
    'btn_disabled_bg': 'rgba(215,205,188,100)', 'btn_disabled_fg': 'rgba(120,90,55,110)',
    'btn_active_bg': 'rgba(44,26,0,175)', 'btn_active_border': 'rgba(192,57,43,100)',
    'btn_active_fg': 'rgba(245,240,232,240)', 'btn_active_hover': 'rgba(60,36,0,195)',
    'btn_primary_bg': 'rgba(192,57,43,200)', 'btn_primary_border': 'rgba(220,100,80,160)',
    'btn_primary_hover': 'rgba(170,40,28,220)',
    'btn_danger_bg': 'rgba(160,30,30,175)', 'btn_danger_border': 'rgba(200,80,60,120)',
    'btn_danger_hover': 'rgba(140,22,22,195)',
    'btn_stop_bg': 'rgba(160,30,30,175)', 'btn_stop_border': 'rgba(200,80,60,120)',
    'btn_stop_hover': 'rgba(140,22,22,195)',
    'btn_mode_active_bg': 'rgba(192,57,43,195)', 'btn_mode_active_border': 'rgba(220,100,80,155)',
    'btn_mode_active_hover': 'rgba(170,40,28,215)',
    'box_border_temp': (139, 92, 42, 130), 'box_border_fixed': (44, 26, 0, 195),
    'box_fill': (240, 230, 210, 8),
    'overlay_bg': (242, 236, 224, 238), 'overlay_text': '#2c1a00',
    'overlay_border': (139, 92, 42, 90),
    'overlay_below_bg': (238, 230, 216, 230), 'overlay_below_text': '#2c1a00',
    'overlay_below_border': (120, 78, 36, 70),
    'toggle_track': (210, 198, 178, 220), 'toggle_track_border': (44, 26, 0, 28),
    'toggle_manual': (44, 26, 0, 220), 'toggle_auto': (192, 57, 43, 220),
    'split_bg': (216, 206, 188, 200), 'split_border': (44, 26, 0, 30),
    'split_active_bg': (44, 26, 0, 178), 'split_active_border': (192, 57, 43, 100),
    'split_text': (44, 26, 0, 230),
    'menu_bg': 'rgba(242,236,222,245)', 'menu_text': 'rgba(44,26,0,230)',
    'menu_border': 'rgba(44,26,0,28)', 'menu_selected': 'rgba(192,57,43,175)',
    'menu_checked': 'rgba(160,30,20,255)',
    'scrollbar_bg': 'rgba(44,26,0,8)', 'scrollbar_handle': 'rgba(44,26,0,38)',
    'sep_color': 'rgba(44,26,0,14)',
    'source_editor_bg': 'rgba(44,26,0,5)', 'source_editor_border': 'rgba(44,26,0,24)',
    'source_editor_text': 'rgba(44,26,0,220)',
    'explain_bg': 'rgba(192,57,43,6)', 'explain_text': 'rgba(80,20,10,220)',
    'swatch': ('#f5f0e8', '#2c1a00', '#c0392b'),
}
```

**`mint`** (薄荷清风，浅色):
```python
'mint': {
    'name': '薄荷清风', 'description': '清新薄荷绿白，简洁现代', 'dark': False,
    'bg_rgb': (232, 250, 244), 'border': 'rgba(0,137,123,22)', 'radius': 10,
    'text': '#004d40', 'text_muted': 'rgba(0,105,92,210)', 'text_ocr': 'rgba(0,77,64,160)',
    'btn_bg': 'rgba(178,223,219,195)', 'btn_border': 'rgba(0,137,123,32)',
    'btn_fg': 'rgba(0,77,64,220)', 'btn_hover': 'rgba(155,206,200,215)',
    'btn_disabled_bg': 'rgba(178,223,219,100)', 'btn_disabled_fg': 'rgba(80,140,130,110)',
    'btn_active_bg': 'rgba(0,137,123,180)', 'btn_active_border': 'rgba(0,191,165,120)',
    'btn_active_fg': 'rgba(255,255,255,240)', 'btn_active_hover': 'rgba(0,121,107,200)',
    'btn_primary_bg': 'rgba(0,137,123,210)', 'btn_primary_border': 'rgba(0,191,165,160)',
    'btn_primary_hover': 'rgba(0,121,107,230)',
    'btn_danger_bg': 'rgba(229,57,53,175)', 'btn_danger_border': 'rgba(239,83,80,120)',
    'btn_danger_hover': 'rgba(211,47,47,195)',
    'btn_stop_bg': 'rgba(229,57,53,175)', 'btn_stop_border': 'rgba(239,83,80,120)',
    'btn_stop_hover': 'rgba(211,47,47,195)',
    'btn_mode_active_bg': 'rgba(0,137,123,200)', 'btn_mode_active_border': 'rgba(0,191,165,155)',
    'btn_mode_active_hover': 'rgba(0,121,107,220)',
    'box_border_temp': (0, 191, 165, 140), 'box_border_fixed': (0, 137, 123, 200),
    'box_fill': (200, 245, 238, 8),
    'overlay_bg': (228, 248, 241, 238), 'overlay_text': '#004d40',
    'overlay_border': (0, 150, 136, 90),
    'overlay_below_bg': (222, 244, 236, 230), 'overlay_below_text': '#004d40',
    'overlay_below_border': (0, 130, 118, 70),
    'toggle_track': (170, 220, 212, 220), 'toggle_track_border': (0, 137, 123, 28),
    'toggle_manual': (0, 137, 123, 220), 'toggle_auto': (105, 240, 174, 220),
    'split_bg': (174, 218, 212, 200), 'split_border': (0, 137, 123, 32),
    'split_active_bg': (0, 137, 123, 182), 'split_active_border': (0, 191, 165, 120),
    'split_text': (0, 77, 64, 230),
    'menu_bg': 'rgba(228,248,240,245)', 'menu_text': 'rgba(0,77,64,230)',
    'menu_border': 'rgba(0,137,123,30)', 'menu_selected': 'rgba(0,137,123,178)',
    'menu_checked': 'rgba(0,105,92,255)',
    'scrollbar_bg': 'rgba(0,137,123,8)', 'scrollbar_handle': 'rgba(0,137,123,45)',
    'sep_color': 'rgba(0,137,123,18)',
    'source_editor_bg': 'rgba(0,137,123,6)', 'source_editor_border': 'rgba(0,137,123,26)',
    'source_editor_text': 'rgba(0,77,64,220)',
    'explain_bg': 'rgba(0,150,136,8)', 'explain_text': 'rgba(0,60,50,220)',
    'swatch': ('#e8faf4', '#00897b', '#00bfa5'),
}
```

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 5: Commit**

```
git add src/ui/theme.py tests/test_theme_variants.py
git commit -m "feat: add cyberpunk, ink, and mint skins"
```

---

## Task 4: Add `kawaii` skin

**Files:**
- Modify: `src/ui/theme.py`
- Modify: `tests/test_theme_variants.py`

- [ ] **Step 1: Write failing test**

Add test asserting:
- `get_skin('kawaii')` returns `dark == False`, `bg_rgb == (255, 245, 248)`, `radius == 16`
- `'kawaii'` in `list_skins()`

- [ ] **Step 2: Run test to verify it fails**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 3: Implement**

**`kawaii`** (可爱动物，浅色):
```python
'kawaii': {
    'name': '可爱动物', 'description': '奶油粉彩，圆角萌系', 'dark': False,
    'bg_rgb': (255, 245, 248), 'border': 'rgba(255,133,168,28)', 'radius': 16,
    'text': '#cc4466', 'text_muted': 'rgba(180,100,140,210)', 'text_ocr': 'rgba(160,80,120,160)',
    'btn_bg': 'rgba(255,215,228,195)', 'btn_border': 'rgba(255,133,168,35)',
    'btn_fg': 'rgba(180,50,100,220)', 'btn_hover': 'rgba(255,190,210,215)',
    'btn_disabled_bg': 'rgba(255,215,228,100)', 'btn_disabled_fg': 'rgba(180,120,150,110)',
    'btn_active_bg': 'rgba(255,133,168,180)', 'btn_active_border': 'rgba(255,107,157,130)',
    'btn_active_fg': 'rgba(255,255,255,240)', 'btn_active_hover': 'rgba(255,107,157,200)',
    'btn_primary_bg': 'rgba(255,133,168,210)', 'btn_primary_border': 'rgba(255,155,185,160)',
    'btn_primary_hover': 'rgba(255,107,157,230)',
    'btn_danger_bg': 'rgba(255,96,96,175)', 'btn_danger_border': 'rgba(255,130,130,120)',
    'btn_danger_hover': 'rgba(240,70,70,195)',
    'btn_stop_bg': 'rgba(255,96,96,175)', 'btn_stop_border': 'rgba(255,130,130,120)',
    'btn_stop_hover': 'rgba(240,70,70,195)',
    'btn_mode_active_bg': 'rgba(255,133,168,200)', 'btn_mode_active_border': 'rgba(255,155,185,155)',
    'btn_mode_active_hover': 'rgba(255,107,157,220)',
    'box_border_temp': (255, 180, 200, 140), 'box_border_fixed': (255, 133, 168, 200),
    'box_fill': (255, 240, 245, 8),
    'overlay_bg': (255, 242, 246, 238), 'overlay_text': '#cc4466',
    'overlay_border': (255, 133, 168, 90),
    'overlay_below_bg': (255, 236, 242, 230), 'overlay_below_text': '#cc4466',
    'overlay_below_border': (255, 107, 157, 70),
    'toggle_track': (255, 205, 220, 220), 'toggle_track_border': (255, 133, 168, 28),
    'toggle_manual': (255, 133, 168, 220), 'toggle_auto': (255, 179, 71, 220),
    'split_bg': (255, 210, 225, 200), 'split_border': (255, 133, 168, 35),
    'split_active_bg': (255, 133, 168, 182), 'split_active_border': (255, 107, 157, 130),
    'split_text': (180, 50, 100, 230),
    'menu_bg': 'rgba(255,242,246,245)', 'menu_text': 'rgba(180,50,100,230)',
    'menu_border': 'rgba(255,133,168,32)', 'menu_selected': 'rgba(255,133,168,178)',
    'menu_checked': 'rgba(220,50,100,255)',
    'scrollbar_bg': 'rgba(255,133,168,8)', 'scrollbar_handle': 'rgba(255,133,168,48)',
    'sep_color': 'rgba(255,133,168,18)',
    'source_editor_bg': 'rgba(255,133,168,5)', 'source_editor_border': 'rgba(255,133,168,28)',
    'source_editor_text': 'rgba(180,50,100,220)',
    'explain_bg': 'rgba(255,179,71,8)', 'explain_text': 'rgba(140,60,20,220)',
    'swatch': ('#fff5f8', '#ff85a8', '#ffb347'),
}
```

- [ ] **Step 4: Run test to verify it passes**

```
python -m pytest tests/test_theme_variants.py -q
```

- [ ] **Step 5: Commit**

```
git add src/ui/theme.py tests/test_theme_variants.py
git commit -m "feat: add kawaii skin"
```

---

## Task 5: Update settings window to show all 13 skins

**Files:**
- Modify: `src/ui/settings_window.py`
- Modify: `tests/test_settings.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting:
- The settings window skin list contains all 13 skin IDs returned by `list_skins()`
- Selecting a new skin ID (e.g. `'kawaii'`) and saving persists it

- [ ] **Step 2: Run tests to verify they fail**

```
python -m pytest tests/test_settings.py -q
```

- [ ] **Step 3: Implement**

The settings window skin selector is data-driven from `list_skins()`. Verify it calls `list_skins()` and `get_skin(id)` to populate. If it currently hardcodes skin IDs, update it to use the dynamic list. The swatch colors come from `skin['swatch']` — no code change needed if already dynamic.

Check `src/ui/settings_window.py` for the skin selector and confirm it iterates `list_skins()`.

- [ ] **Step 4: Run tests to verify they pass**

```
python -m pytest tests/test_settings.py -q
```

- [ ] **Step 5: Full test suite**

```
python -m pytest -q
```

- [ ] **Step 6: Commit**

```
git add src/ui/settings_window.py tests/test_settings.py
git commit -m "feat: settings window supports all 13 skins dynamically"
```

---

## Final Verification

- [ ] Run `python -m pytest -q` — all tests pass
- [ ] Confirm `list_skins()` returns 13 skin IDs
- [ ] Verify `get_skin('kawaii')`, `get_skin('cyberpunk')`, `get_skin('ink')` etc. all return valid dicts
