# 分段翻译功能设计文档

**日期**：2026-03-14
**项目**：ScreenTranslator
**状态**：已审批（经 spec-review 第三轮修订）

---

## 背景与目标

当前 OCR 识别出来的多行文本以空格连接为一整段，发给翻译后端后译文也是一整段。对于包含多个自然段的长文章，用户无法区分原文和译文各段对应关系。

本功能目标：

1. 复用现有的 `group_rows_into_paragraphs()`（`src/core/overlay_layout.py`）检测段落边界
2. 原文和译文均以 `[1] [2] ...` 编号格式分段显示
3. 在结果条和翻译框各加一个"分段"切换按钮
4. 设置页新增"自动分段"开关和"间距阈值"参数

---

## 方案选择

选用**整体翻译 + `\n\n` 段落标记**：

- OCR 段落间用 `\n\n` 连接后发给翻译接口（每段内部行用空格连接，压平 `\n`）
- 绝大多数后端天然保留 `\n\n`，译文可按 `\n\n` 切分还原段落
- 若段落数不匹配则降级为整体显示（鲁棒性保证）

---

## 现有基础设施（复用，不重复实现）

| 文件 | 内容 |
|------|------|
| `src/core/overlay_layout.py` | `group_rows_into_paragraphs(rows)` — 已实现行坐标间距分段算法（**需扩展 `gap_ratio` 参数**，见下文） |
| `src/ui/translation_box.py` | `_last_ocr_paragraphs`, `_last_paragraph_translations`, `_layout_paragraph_subtitles()` 等覆盖翻译段落基础设施 |
| `src/core/controller.py` | `_normalize_ocr_payload` 目前是**模块级函数**（**需改为实例方法**，见下文） |

> **注意**：`translation_box.py` 的 `_last_ocr_paragraphs` / `_last_paragraph_translations` 归覆盖翻译（overlay）专用。结果条的分段数据通过 `result['paragraphs']` 传递，两条路径独立，互不干扰。

---

## 数据流

```
OCR 识别
  ↓ ocr_worker._run_rapidocr()：不改动，仍输出 {text, rows}
  ↓
controller._normalize_ocr_payload(payload)
  — 修改：调用 group_rows_into_paragraphs(rows, gap_ratio) 生成 paragraphs
  — 若 para_split_enabled=True 且段落数 ≥ 2：
      para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
      text = "\n\n".join(para_texts)
  — 否则 text 保持原空格连接，paragraphs = []，para_texts = []
  — payload 新增 paragraphs 和 para_texts 字段

controller._on_ocr_done(payload, region, box)
  — 已有的 overlay 段落写入保持不变（box._last_ocr_paragraphs）
  — 直接使用 normalized_payload['para_texts'] 暂存（无重复计算）：
      box._pending_para_texts = normalized_payload.get('para_texts', [])

TranslationWorker.translate("para1\n\npara2")
  ↓
router.translate() 返回 {translated: "译1\n\n译2", ...}

controller._on_translate_done(result, box)  ← 第 643 行（另一份是死代码）
  if box is not None:
      pending = getattr(box, '_pending_para_texts', [])
      if pending:
          parts = result['translated'].split('\n\n')
          if len(parts) == len(pending):
              result['paragraphs'] = [
                  {'text': orig, 'translation': trans}
                  for orig, trans in zip(pending, parts)
              ]
          else:
              result['paragraphs'] = []   # 降级
          box._pending_para_texts = []
  result.setdefault('paragraphs', [])

result_bar.show_result(result)   ← [1]/[2] 格式显示
box.show_subtitle(translated)    ← 覆盖翻译：复用原有段落逻辑
```

---

## 模块设计

### 1. `src/core/settings.py`

```python
DEFAULTS 新增：
  'para_split_enabled': True,
  'para_gap_ratio':     0.5,
```

### 2. `src/core/overlay_layout.py`

**需扩展 `gap_ratio` 参数**（当前签名不接受该参数，需修改两处）：

```python
def _can_merge_lines(previous_rect, current_rect, gap_ratio: float = 0.0):
    vertical_gap = current_rect['y'] - _rect_bottom(previous_rect)
    if vertical_gap < 0:
        vertical_gap = 0

    # gap_ratio=0 时公式退化为原始值 max(12, h * 1.6)，向后兼容
    # gap_ratio>0 时阈值增大，段落更难被切分（段落间距更宽松）
    height_threshold = max(12, int(max(previous_rect['height'], current_rect['height']) * 1.6 * (1 + gap_ratio)))
    if vertical_gap > height_threshold:
        return False

    overlap = _horizontal_overlap(previous_rect, current_rect)
    min_width = max(1, min(previous_rect['width'], current_rect['width']))
    if overlap >= int(min_width * 0.15):
        return True

    indent_threshold = max(18, int(max(previous_rect['height'], current_rect['height']) * 2.5))
    return abs(previous_rect['x'] - current_rect['x']) <= indent_threshold


def group_rows_into_paragraphs(rows, gap_ratio: float = 0.0):
    # ... 其余不变，仅在 _can_merge_lines 调用处透传 gap_ratio ...
    for line in lines:
        if current is None or not _can_merge_lines(previous_line['rect'], line['rect'], gap_ratio):
            ...
```

> **关键**：`gap_ratio` 默认值为 `0.0`（保持原始阈值 `h * 1.6`，向后兼容）。已有的 overlay 路径（`controller._on_ocr_done` 中的直接调用）不传 `gap_ratio`，行为不变。新的分段翻译路径（`_normalize_ocr_payload`）显式传入 `gap_ratio=gap_ratio`（从 settings `para_gap_ratio` 取值，默认 `0.5`），即用户可通过设置调整段落灵敏度。

### 3. `src/core/controller.py`

**清理前置**：删除第 468 行处的重复 `_on_translate_done`（死代码），保留第 643 行的有效版本。

> **实施注意**：删除前必须逐行对比两个版本的差异，确认第 643 行版本包含了第 468 行的所有有效逻辑（包括 `self._box_mode == 'multi'` 检查和 box 守护条件）。同理清理重复的 `_on_overlay_requested`（保留第 605 行版本，删除第 562 行版本），以及重复的 `_trigger_explain`（保留第 626 行版本，删除第 205 行版本），均需先 diff 后删除。

**`_normalize_ocr_payload` 改为实例方法**：

当前代码中 `_normalize_ocr_payload` 是**模块级函数**（无 `self`），无法访问 `self.settings`。必须将其移入 `Controller` 类并添加 `self` 参数，同时更新两处调用点：原调用 `_normalize_ocr_payload(payload)` 改为 `self._normalize_ocr_payload(payload)`。

> **AI 框选路径（第 324 行）**：该行调用 `_normalize_ocr_payload(payload)['text']` 仅取文本，改为 `self._normalize_ocr_payload(payload)['text']` 后会执行段落检测但结果被丢弃，开销可忽略，行为正确，无需特殊处理。

**修改后的实例方法**（返回值中增加 `para_texts` 字段，避免下游重复计算）：

```python
def _normalize_ocr_payload(self, payload: dict) -> dict:
    rows = payload.get('rows', [])
    para_enabled = self.settings.get('para_split_enabled', True)
    gap_ratio = float(self.settings.get('para_gap_ratio', 0.5))

    paras = []
    para_texts = []
    if para_enabled and rows:
        paras = group_rows_into_paragraphs(rows, gap_ratio=gap_ratio)

    if para_enabled and len(paras) >= 2:
        # 每段内部行压平为空格，段间用 \n\n
        para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
        text = '\n\n'.join(para_texts)
    else:
        text = payload.get('text', '')  # 原有空格连接
        paras = []
        para_texts = []

    return {
        'text':       text,
        'rows':       rows,
        'paragraphs': paras,       # 新增：段落对象列表
        'para_texts': para_texts,  # 新增：各段纯文本列表，供 _on_ocr_done 直接使用
    }
```

**`_on_ocr_done`** — 在已有的 overlay 段落写入后，追加（直接使用 `normalized_payload['para_texts']`，无需重复推导）：

```python
# 暂存段落文本列表供 _on_translate_done 使用
if box is not None:
    box._pending_para_texts = normalized_payload.get('para_texts', [])
```

**`_on_translate_done(result, box)`**（第 643 行版本）— 在现有 `if box is not None:` 块内追加：

```python
pending = getattr(box, '_pending_para_texts', [])
if pending:
    parts = result.get('translated', '').split('\n\n')
    if len(parts) == len(pending):
        result['paragraphs'] = [
            {'text': orig, 'translation': trans}
            for orig, trans in zip(pending, parts)
        ]
    else:
        result['paragraphs'] = []
    box._pending_para_texts = []
result.setdefault('paragraphs', [])
```

### 4. `src/ui/settings_window.py`

在"通用"标签页 `QFormLayout` 末尾追加：

```
[✓] 自动识别段落，分段翻译
    段落间距阈值（×行高）: [0.50 ↕]   (范围 0.1~3.0，step 0.1)
```

仅 checkbox 勾选时，spin box 可用（`_para_ratio_spin.setEnabled(checked)`）。

`_save()` 中写入：

```python
self.settings.set('para_split_enabled', self._para_check.isChecked())
self.settings.set('para_gap_ratio', self._para_ratio_spin.value())
```

### 5. `src/ui/result_bar.py`

**新状态变量**：

```python
self._para_mode: bool  # __init__ 中初始值 = settings.get('para_split_enabled', True)
```

**新方法 `sync_para_mode_from_settings()`**（供 `settings_saved` 信号连接）：

```python
def sync_para_mode_from_settings(self):
    self._para_mode = self.settings.get('para_split_enabled', True)
    self._update_para_button()
    if self._current_result:
        self.show_result(self._current_result)
```

**新按钮** `_btn_para`，插入 `_details_actions_widget` 的 `_btn_source` 前面：

```
[分段 ▼]  [原文 ▼]  [📋 原文]  [重新翻译]  [💬 AI科普]
```

点击回调 `_toggle_para_mode()`：翻转 `_para_mode`，调用 `_update_para_button()`，用 `_current_result` 刷新显示。

**`_update_para_button()`**：

```python
def _update_para_button(self):
    has_paras = bool(
        self._current_result and self._current_result.get('paragraphs')
    )
    self._btn_para.setText('分段 ▲' if self._para_mode else '分段 ▼')
    self._btn_para.setEnabled(has_paras)
```

**格式化方法**：

```python
def _format_para_text(self, paragraphs: list, key: str) -> str:
    return "\n".join(f"[{i+1}] {p[key]}" for i, p in enumerate(paragraphs))
```

**`show_result` 修改**（保留现有 `_source_dirty` 守护逻辑）：

```python
def show_result(self, result: dict):
    ...
    paras = result.get('paragraphs', [])
    if self._para_mode and paras:
        self._set_translation_text(self._format_para_text(paras, 'translation'))
        # 保留现有守护：用户已手动编辑原文时不覆盖
        if not self._source_dirty or not self.current_source_text():
            self._set_source_text(self._format_para_text(paras, 'text'), mark_clean=True)
    else:
        self._set_translation_text(result.get('translated', ''))
        if not self._source_dirty or not self.current_source_text():
            self._set_source_text(result.get('original', ''), mark_clean=True)
    self._update_para_button()
    ...
```

### 6. `src/ui/translation_box.py`

**新按钮** `_btn_para`（标签 `¶`），插入 `_btn_translate` 之后：

```python
self._btn_para = self._make_btn("¶", "切换分段显示", self._on_toggle_para)
```

状态与 `_para_mode` 同步，高亮样式复用 `_btn_subtitle` 的激活样式。

> **覆盖翻译段落数据**（`_last_ocr_paragraphs` / `_last_paragraph_translations`）仍由现有的 overlay 异步翻译流程写入，**本功能不改动这条路径**。翻译框的"分段"按钮仅控制是否在框内的 `_ocr_label` 区域以编号格式显示文本（可选，低优先级）。

---

## `controller.py` 信号连接补充

在 `_show_settings()` 连接 `settings_saved` 信号处，追加：

```python
settings_win.settings_saved.connect(self.result_bar.sync_para_mode_from_settings)
```

---

## 降级策略

| 情况 | 行为 |
|------|------|
| 翻译后端未保留 `\n\n`，段落数不匹配 | `result['paragraphs'] = []`，显示整体文本 |
| `para_split_enabled = False` | text 空格连接，`paragraphs = []`，"分段"按钮置灰 |
| 仅 1 个段落 | 同上，不加编号 |
| `box = None`（重翻译场景） | 段落拼接逻辑在 `if box is not None:` 内，安全跳过 |
| rows 为空或坐标异常 | `group_rows_into_paragraphs` 返回空列表，降级 |

---

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `src/core/settings.py` | 2 个新默认值 |
| `src/core/overlay_layout.py` | `_can_merge_lines` 和 `group_rows_into_paragraphs` 各增加 `gap_ratio: float = 0.5` 参数 |
| `src/core/controller.py` | ① 清理重复方法；② `_normalize_ocr_payload` **从模块级函数改为实例方法**（加 `self`，更新两处调用点）并新增段落检测；③ `_on_ocr_done` 暂存段落文本；④ `_on_translate_done` 配对段落；⑤ `settings_saved` 连接 |
| `src/ui/settings_window.py` | 通用 tab 新增 2 个控件 + `_save` |
| `src/ui/result_bar.py` | `_btn_para` 按钮 + `_para_mode` 状态 + `show_result` 逻辑 + `sync_para_mode_from_settings` |
| `src/ui/translation_box.py` | `_btn_para` 按钮（低优先级，可后做） |

> `src/ocr/ocr_worker.py` **无需改动**，复用现有 rows 输出。

---

## 验证方案

1. **段落检测**：选取包含多段英文或中文文章截图，翻译后确认原文和译文均出现 `[1] [2]` 编号
2. **单段降级**：选取单行短文本，确认不出现 `[1]` 编号
3. **段落数不匹配降级**：使用不保留换行的后端，确认整体文本显示
4. **分段按钮切换**：点击"分段 ▼/▲"，实时在编号格式和整体格式之间切换
5. **设置开关同步**：改"自动分段"设置保存后，结果条按钮状态与之同步
6. **box=None 重翻译**：手动修改原文重新翻译，确认无崩溃
7. **覆盖翻译不受影响**：启用"覆盖翻译"模式，段落覆盖显示仍正常工作
