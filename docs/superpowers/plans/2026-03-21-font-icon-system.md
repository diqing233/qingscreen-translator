# Font + Icon System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成字体集/图标集系统：迁移 result_bar.py 剩余 `_draw_*` 图标到 Phosphor，消费字体 token，补充测试。

**Architecture:** `get_skin()` 四层组合已实现。translation_box.py 图标迁移已完成（无翻译标签，无需字体 token 消费）。本 plan 只需完成 result_bar.py 图标迁移 + 字体 token 消费 + 补充测试。

**Tech Stack:** Python 3.11, PyQt5, Phosphor Icons font, pytest

---

## 当前状态（已完成，无需重做）

- `src/ui/theme.py`：`FONT_SETS`、`ICON_SETS`、`get_skin()` 四层组合、campus 皮肤 ✅
- `src/main.py`：字体注册 `_register_fonts()` ✅
- `src/core/settings.py`：`font_set: None`、`icon_set: None` ✅
- `src/ui/settings_window.py`：字体集/图标集 ComboBox ✅
- `src/ui/translation_box.py`：`_ph_icon()` + 图标迁移 ✅
- `assets/fonts/`：所有字体文件 ✅
- `tests/test_font_icon_system.py`：已存在，20 个测试通过 ✅

## 待完成

- `result_bar.py`：5 个按钮仍用 `_mk_icon(_draw_*)` → 迁移到 `_ph_icon()`，删除 `_draw_*` 和 `_mk_icon`
- `result_bar.py`：`_lbl_translation` 字体硬编码 → 消费 `font_family`/`font_size_translation`
- `tests/test_font_icon_system.py`：补充缺失测试

---

## File Map

| 文件 | 操作 |
|------|------|
| `src/ui/result_bar.py` | 修改：图标迁移 + 删除 `_draw_*`/`_mk_icon` + 字体 token 消费 |
| `tests/test_font_icon_system.py` | 修改：补充缺失测试 |

---

## Task 1: 迁移 result_bar.py 图标并删除旧方法

**Files:**
- Modify: `src/ui/result_bar.py`

需迁移的 5 处（`_mk_icon(_draw_*)` → `_ph_icon(key)`）：
- `_btn_copy_trans` → `icon_copy`
- `_btn_copy_src` → `icon_copy`
- `_btn_history` → `icon_history`
- `_btn_para_num` → `icon_paragraph`
- `_btn_stop_clear` → `icon_square`

- [ ] **Step 1: 替换初始化时的图标赋值（约第 607-748 行）**

```python
# _btn_copy_trans（约 609 行）
# 替换前: self._btn_copy_trans.setIcon(self._mk_icon(self._draw_copy))
self._btn_copy_trans.setIcon(self._ph_icon('icon_copy'))

# _btn_history（约 644 行）
# 替换前: self._btn_history.setIcon(self._mk_icon(self._draw_clock, 18))
self._btn_history.setIcon(self._ph_icon('icon_history', size=18))

# _btn_copy_src（约 726 行）
# 替换前: self._btn_copy_src.setIcon(self._mk_icon(self._draw_copy))
self._btn_copy_src.setIcon(self._ph_icon('icon_copy'))

# _btn_para_num（约 747 行）
# 替换前: self._btn_para_num.setIcon(self._mk_icon(self._draw_paragraph, 16))
self._btn_para_num.setIcon(self._ph_icon('icon_paragraph'))

# _btn_stop_clear（约 1244 行）
# 替换前: self._btn_stop_clear.setIcon(self._mk_icon(self._draw_square))
self._btn_stop_clear.setIcon(self._ph_icon('icon_square'))
```

- [ ] **Step 2: 替换 apply_skin() 中的图标重绘（约第 1644-1651 行）**

```python
# 替换前（5 行 _mk_icon 调用）:
# self._btn_copy_trans.setIcon(self._mk_icon(self._draw_copy))
# self._btn_copy_src.setIcon(self._mk_icon(self._draw_copy))
# self._btn_history.setIcon(self._mk_icon(self._draw_clock, 18))
# self._btn_history.setIconSize(QSize(18, 18))
# self._btn_para_num.setIcon(self._mk_icon(self._draw_paragraph, 16))
# self._btn_stop_clear.setIcon(self._mk_icon(self._draw_square))

# 替换后:
self._btn_copy_trans.setIcon(self._ph_icon('icon_copy'))
self._btn_copy_src.setIcon(self._ph_icon('icon_copy'))
self._btn_history.setIcon(self._ph_icon('icon_history', size=18))
self._btn_history.setIconSize(QSize(18, 18))
self._btn_para_num.setIcon(self._ph_icon('icon_paragraph'))
self._btn_stop_clear.setIcon(self._ph_icon('icon_square'))
```

- [ ] **Step 3: 确认无残留调用，删除 `_draw_*` 和 `_mk_icon` 方法**

```bash
grep -n "_draw_\|_mk_icon" src/ui/result_bar.py
```

若无调用，删除以下方法（约第 1070-1145 行）：
- `_mk_icon(self, draw_fn, size=14)`
- `_draw_copy(p, s)`
- `_draw_broom(p, s)`
- `_draw_clock(p, s)`
- `_draw_square(p, s)`
- `_draw_paragraph(p, s)`

检查 `QPainter`/`QPen`/`QPolygonF` 是否还有其他用途（`_ph_icon` 本身也用 QPainter，不能删）：

```bash
grep -n "QPolygonF" src/ui/result_bar.py
```

若 `QPolygonF` 无任何调用，从第 8 行 import 中移除 `QPolygonF`。`QPainter`/`QPen` 保留（`_ph_icon` 仍需要）。

- [ ] **Step 4: 运行测试**

```bash
python -m pytest -q
```

Expected: 全部通过（164 个）

- [ ] **Step 5: Commit**

```bash
git add src/ui/result_bar.py
git commit -m "feat: migrate result_bar _draw_* icons to Phosphor, remove _mk_icon"
```

---

## Task 2: result_bar.py 消费字体 token

**Files:**
- Modify: `src/ui/result_bar.py`

当前 `_lbl_translation` 字体硬编码（约第 706-708 行）：
```python
f = QFont()
f.setPixelSize(14)
self._lbl_translation.setFont(f)
```

- [ ] **Step 1: 修改初始化字体（约第 706-708 行）**

```python
# 替换为：
_ff = self._skin.get('font_family', '').split(',')[0].strip().strip('"')
f = QFont(_ff) if _ff else QFont()
f.setPixelSize(int(self._skin.get('font_size_translation', 14)))
self._lbl_translation.setFont(f)
```

- [ ] **Step 2: 在 apply_skin() 中同步更新字体**

在 `apply_skin()` 中找到 `self._lbl_translation.setStyleSheet(self._translation_text_style())` 这行（约第 1658 行），在其后添加：

```python
_ff = self._skin.get('font_family', '').split(',')[0].strip().strip('"')
_f = QFont(_ff) if _ff else QFont()
_f.setPixelSize(int(self._skin.get('font_size_translation', 14)))
self._lbl_translation.setFont(_f)
```

- [ ] **Step 3: 运行测试**

```bash
python -m pytest -q
```

Expected: 全部通过

- [ ] **Step 4: Commit**

```bash
git add src/ui/result_bar.py
git commit -m "feat: consume font tokens in result_bar translation label"
```

---

## Task 3: 补充测试

**Files:**
- Modify: `tests/test_font_icon_system.py`

当前文件已有 20 个测试。需补充：result_bar 图标迁移验证、字体 token 消费验证。

- [ ] **Step 1: 检查现有测试覆盖情况**

```bash
python -m pytest tests/test_font_icon_system.py -v
```

- [ ] **Step 2: 在文件末尾追加以下测试**

```python
def test_result_bar_skin_has_font_tokens():
    """result_bar 消费的 token 必须存在于皮肤中。"""
    for sid in list_skins():
        skin = get_skin(sid)
        assert 'font_family' in skin
        assert 'font_size_translation' in skin
        assert isinstance(skin['font_size_translation'], int)


def test_icon_codepoints_are_nonempty_strings():
    """所有图标 codepoint 必须是非空字符串。"""
    icon_codepoint_keys = [
        'icon_copy', 'icon_close', 'icon_translate', 'icon_ai',
        'icon_pin', 'icon_unpin', 'icon_expand', 'icon_collapse',
        'icon_font_up', 'icon_font_down', 'icon_settings', 'icon_history',
        'icon_paragraph', 'icon_broom', 'icon_square',
    ]
    for set_name, ic in ICON_SETS.items():
        for key in icon_codepoint_keys:
            val = ic.get(key, '')
            assert isinstance(val, str) and len(val) > 0, \
                f"ICON_SETS['{set_name}']['{key}'] is empty"


def test_font_family_strings_are_nonempty():
    """所有字体集的 font_family 必须是非空字符串。"""
    for name, fs in FONT_SETS.items():
        assert isinstance(fs['font_family'], str)
        assert len(fs['font_family']) > 0
```

- [ ] **Step 3: 运行新测试**

```bash
python -m pytest tests/test_font_icon_system.py -v
```

Expected: 全部 PASS

- [ ] **Step 4: 运行全量测试**

```bash
python -m pytest -q
```

Expected: 全部通过

- [ ] **Step 5: Commit**

```bash
git add tests/test_font_icon_system.py
git commit -m "test: add font/icon token validation tests"
```

---

## Task 4: 最终验证

- [ ] **Step 1: 运行全量测试**

```bash
python -m pytest -q
```

Expected: 全部通过

- [ ] **Step 2: 手动启动应用，切换皮肤验证图标和字体**

```bash
python src/main.py
```

切换到 matrix（mono 字体 + phosphor-bold）、kawaii（rounded 字体）、ink（serif 字体 + phosphor-light），确认翻译标签字体和工具栏图标随皮肤变化。

- [ ] **Step 3: 最终 commit**

```bash
git add -A
git commit -m "feat: complete font+icon system implementation"
```
