# 字幕覆盖翻译 + 固定模式修复 设计文档

日期：2026-03-10

## 背景

用户需要：
1. 每个翻译框增加"覆盖翻译"按钮，点击后在框的正下方显示译文字幕条（双语字幕效果），不遮挡原文。
2. 修复"固定"模式按钮未生效的问题。

---

## Bug 修复：固定按钮未生效

### 根因

`controller.py` 的 `_on_box_mode_changed` 切换到 'fixed' 时，只更新了 `self._box_mode`，没有对已存在的框调用 `set_mode('fixed')`。因此：

- 用户先框选（创建临时框）→ dismiss timer 已启动
- 再点"固定"按钮 → 旧框 timer 仍在跑 → 框自动消失

### 修复

在 `_on_box_mode_changed` 中，当切换到 'fixed' 时，对所有现存框调用 `box.set_mode('fixed')`（内部会 stop dismiss_timer）：

```python
def _on_box_mode_changed(self, mode: str):
    self._box_mode = mode
    if mode != 'multi':
        self._multi_results.clear()
    if mode == 'fixed':
        for box in self.box_manager._boxes.values():
            box.set_mode('fixed')
```

---

## 新功能：字幕条覆盖翻译

### 选定方案：独立浮动子窗口（方案B）

点击各框上的 `⊞` 按钮，在框正下方弹出一个独立的 `Qt.Tool` 浮动窗口作为字幕条，原文区域完全可见，互不遮挡。

### 变更范围

#### 1. `src/ui/translation_box.py`

**新增状态：**
- `self._subtitle_win = None` — 字幕窗口（懒创建）
- `self._subtitle_active = False` — 当前字幕是否激活

**新增按钮：**
在按钮栏（🔄 📌 👁 ✕）中加入 `⊞` 按钮，调用 `_on_toggle_subtitle()`。

**新增方法：**
- `_create_subtitle_win()` — 懒创建字幕窗口（Tool + FramelessWindowHint + WindowStaysOnTopHint + WA_TranslucentBackground）
- `show_subtitle(text: str)` — 按当前 box 位置和宽度定位字幕窗口并显示；内部调用 `_create_subtitle_win()`
- `hide_subtitle()` — 隐藏字幕窗口
- `_on_toggle_subtitle()` — 切换字幕显示/隐藏，更新按钮高亮

**字幕窗口位置：**
- x = `self.x()`，y = `self.y() + self.height()`
- width = `self.width()`，height = 自适应文本（min 32px）

**跟随移动/缩放：**
- `moveEvent`：重新定位字幕窗口
- `resizeEvent`（已有）：更新字幕窗口宽度和位置
- `hideEvent`：同步 `hide_subtitle()`
- `close_requested` 已有 → `_remove_box` 调用 `deleteLater`，需在 `_remove_box` 前先 `hide_subtitle()` 并销毁字幕窗口

**OCR region 不变：**`self.region` 只在框选/拖动时更新，字幕窗口不影响它。

**移除旧方法：**`show_translation_overlay` / `hide_translation_overlay`（全覆盖式 overlay）统一替换为新字幕方案。

#### 2. `src/core/controller.py`

- `_on_translate_done`：翻译完成后，若 `box._subtitle_active` 为 True，调用 `box.show_subtitle(translated_text)` 刷新字幕内容。
- `_on_overlay_requested`：改为调用 `box.show_subtitle(t)` / `box.hide_subtitle()`，与各框自己的按钮行为统一。

#### 3. `src/ui/result_bar.py`

无变化。`⊞` 按钮保留，继续全局切换所有框的字幕。

---

## 字幕窗口样式

```
背景：rgba(15, 15, 24, 210)
上边框：1px solid rgba(80, 140, 255, 0.4)   ← 与框的蓝色虚线呼应
字色：#f0f0f0
字号：13px
内边距：6px 12px
圆角：0 0 6px 6px（与框下沿接合）
```

---

## 测试要点

1. 框选 → 翻译完成 → 点击框上 `⊞` → 字幕条出现在框正下方
2. 拖动框 → 字幕条跟随
3. 调整框大小 → 字幕条宽度同步
4. 再次点 `⊞` → 字幕条隐藏
5. 关闭框 → 字幕条也消失
6. result bar 的 `⊞` 全局切换 → 所有框字幕同步开关
7. 翻译刷新（手动/自动）→ 字幕条内容同步更新
8. 固定按钮修复：先框选 → 再点"固定" → 框不再自动消失
