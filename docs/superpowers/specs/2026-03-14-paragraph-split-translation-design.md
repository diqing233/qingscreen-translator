# 分段翻译功能设计文档

**日期**：2026-03-14
**项目**：ScreenTranslator
**状态**：已审批

---

## 背景与目标

当前 OCR 识别出来的多行文本以空格连接为一整段，发给翻译后端后译文也是一整段。对于包含多个自然段的长文章，用户无法区分原文和译文各段对应关系。

本功能目标：

1. 在 OCR 层根据行坐标间距自动检测段落边界
2. 原文和译文均以 `[1] [2] ...` 编号格式分段显示
3. 在结果条和翻译框各加一个"分段"切换按钮
4. 设置页新增"自动分段"开关和"间距阈值"参数

---

## 方案选择

选用**方案 C（整体翻译 + `\n\n` 段落标记）**：

- OCR 段落间用 `\n\n` 连接后发给翻译接口
- 绝大多数后端天然保留 `\n\n`，译文可按 `\n\n` 切分还原段落
- 若段落数不匹配则降级为整体显示（鲁棒性保证）

---

## 数据流

```
OCR 识别
  ↓ _run_rapidocr() 新增 _detect_paragraphs()
payload = {
  text:       "para1\n\npara2",     ← \n\n 连接
  rows:       [...],
  paragraphs: [{text, rows, rect}, ...]
}
  ↓ controller._on_ocr_done()
  ↓ 暂存 paragraphs 到 box._last_ocr_paragraphs
  ↓ 用 payload.text 启动 TranslationWorker
  ↓ router.translate("para1\n\npara2")
  ↓ 翻译后端返回 "译1\n\n译2"
  ↓ controller._on_translate_done()
  ↓ 切分译文 → ["译1","译2"]，与原文段落配对
result = {
  translated:  "译1\n\n译2",
  original:    "para1\n\npara2",
  paragraphs:  [{text,translation,rect}, ...],  ← 新字段
  backend:     "...",
  source_lang: "...",
}
  ↓ result_bar.show_result(result)   ← [1]/[2] 格式显示
  ↓ box.show_subtitle(translated)    ← 段落覆盖翻译（原有逻辑）
```

---

## 模块设计

### 1. `src/ocr/ocr_worker.py`

新增静态方法：

```python
@staticmethod
def _detect_paragraphs(rows: list, gap_ratio: float = 0.5) -> list:
    """
    根据行 bbox 的垂直间距检测段落边界。
    gap_ratio: 间距 > gap_ratio × 中位行高 时判定为段落分隔。
    返回 List[{text:str, rows:list, rect:{x,y,width,height}}]
    """
```

算法：
1. 从每行 box 四个顶点提取 top/bottom Y 坐标，计算行高列表
2. 取中位行高 `median_h`
3. 遍历相邻行：`gap = curr_top - prev_bottom`，若 `gap > gap_ratio * median_h` 则切断
4. 每段计算包围矩形 rect（覆盖翻译时按位置显示）

修改 `_run_rapidocr()` 返回值：

```python
paras = OCRWorker._detect_paragraphs(normalized_rows)
# 仅多段时用 \n\n 连接；单段保持空格连接（向后兼容）
para_text = "\n\n".join(p["text"] for p in paras) if len(paras) > 1 else " ".join(lines).strip()
return {
    "text":       para_text,
    "rows":       normalized_rows,
    "paragraphs": paras,
}
```

`gap_ratio` 从 `settings.get('para_gap_ratio', 0.5)` 读取，通过 worker 构造参数传入，或直接在 `_ocr_pipeline` 中读取。

### 2. `src/core/settings.py`

```python
DEFAULTS 新增：
  'para_split_enabled': True,
  'para_gap_ratio':     0.5,
```

### 3. `src/core/controller.py`

`_on_ocr_done(payload, region)` 中：

```python
paras = payload.get('paragraphs', [])
if not self.settings.get('para_split_enabled', True) or len(paras) <= 1:
    # 不分段：把 text 里的 \n\n 替换回空格，清空 paragraphs
    payload['text'] = payload['text'].replace('\n\n', ' ')
    paras = []
# 暂存段落到 box（box 对象在此处可访问）
box._last_ocr_paragraphs = [
    {'text': p['text'], 'rect': p['rect']} for p in paras
]
```

`_on_translate_done(result, box)` 中：

```python
original_paras = getattr(box, '_last_ocr_paragraphs', [])
if original_paras:
    translated_parts = result.get('translated', '').split('\n\n')
    if len(translated_parts) == len(original_paras):
        result['paragraphs'] = [
            {**orig, 'translation': trans}
            for orig, trans in zip(original_paras, translated_parts)
        ]
    else:
        result['paragraphs'] = []   # 降级
else:
    result['paragraphs'] = []
```

### 4. `src/ui/settings_window.py`

在"通用"标签页 `QFormLayout` 末尾追加：

```
[✓] 自动识别段落，分段翻译
    段落间距阈值（×行高）: [0.50 ↕]   (范围 0.1~3.0，step 0.1，仅 checkbox 勾选时可用)
```

`_save()` 中写入：

```python
self.settings.set('para_split_enabled', self._para_check.isChecked())
self.settings.set('para_gap_ratio', self._para_ratio_spin.value())
```

### 5. `src/ui/result_bar.py`

**新状态变量**：

```python
self._para_mode: bool  # 初始值 = settings.get('para_split_enabled', True)
```

**新按钮** `_btn_para`，插入 `_details_actions_widget` 的 `_btn_source` 前面：

```
[分段 ▼]  [原文 ▼]  [📋 原文]  [重新翻译]  [💬 AI科普]
```

点击回调 `_toggle_para_mode()`：翻转 `_para_mode`，更新按钮文字（`分段 ▲` / `分段 ▼`），用当前 `_current_result` 刷新显示。

**格式化方法**：

```python
def _format_para_text(self, paragraphs: list, key: str) -> str:
    return "\n".join(f"[{i+1}] {p[key]}" for i, p in enumerate(paragraphs))
```

**`show_result` 修改**：

```python
paras = result.get('paragraphs', [])
if self._para_mode and paras:
    self._set_translation_text(self._format_para_text(paras, 'translation'))
    self._set_source_text(self._format_para_text(paras, 'text'), mark_clean=True)
else:
    self._set_translation_text(result.get('translated', ''))
    self._set_source_text(result.get('original', ''), mark_clean=True)
```

**`_btn_para` 可用性**：无 result 时或 `paragraphs` 为空时置灰。

### 6. `src/ui/translation_box.py`

**新按钮** `_btn_para`（标签 `¶`），插入 `_btn_translate` 之后：

```python
self._btn_para = self._make_btn("¶", "分段翻译", self._on_toggle_para)
```

初始状态跟随 `settings.get('para_split_enabled', True)`。

**填充段落数据**（在收到翻译结果时调用，新增 `set_paragraph_result` 方法）：

```python
def set_paragraph_result(self, paragraphs: list):
    """由 controller 在 show_subtitle 之前调用。"""
    self._last_ocr_paragraphs = [
        {'text': p['text'], 'rect': p['rect']} for p in paragraphs
    ]
    self._last_paragraph_translations = [p['translation'] for p in paragraphs]
```

原有 `_can_render_paragraph_subtitles()` / `_layout_paragraph_subtitles()` 逻辑无需修改，自动生效。

---

## 降级策略

| 情况 | 行为 |
|------|------|
| 翻译后端未保留 `\n\n`，段落数不匹配 | `result['paragraphs'] = []`，显示整体文本 |
| `para_split_enabled = False` | text 空格连接，`paragraphs = []`，按钮存在但无编号 |
| 仅 1 个段落 | 同上，不加 `[1]` 编号 |
| box 无坐标信息（rows 为空） | 不做段落检测，`paragraphs = []` |

---

## 修改文件清单

| 文件 | 改动范围 |
|------|---------|
| `src/ocr/ocr_worker.py` | 新增 `_detect_paragraphs()`；修改 `_run_rapidocr()` 返回值 |
| `src/core/settings.py` | 2 个新默认值 |
| `src/core/controller.py` | `_on_ocr_done` + `_on_translate_done` 各约 10 行 |
| `src/ui/settings_window.py` | 通用 tab 新增 2 个控件 + `_save` |
| `src/ui/result_bar.py` | 新按钮 + `_para_mode` 状态 + `show_result` 逻辑 |
| `src/ui/translation_box.py` | 新按钮 + `set_paragraph_result()` 方法 |

---

## 验证方案

1. **段落检测**：选取包含多段英文或中文文章的截图，开启分段后翻译，确认原文和译文均出现 `[1] [2]` 编号
2. **单段降级**：选取单行短文本，确认不出现 `[1]` 编号
3. **段落数不匹配降级**：使用不保留换行的后端，确认显示整体文本而不是乱序编号
4. **分段按钮切换**：点击"分段 ▼/▲"按钮，确认实时在编号格式和整体格式之间切换
5. **设置开关**：关闭"自动识别段落"设置后重新翻译，确认文本整体显示、按钮置灰
6. **覆盖翻译**：启用"覆盖翻译（原文上）"模式，确认段落译文按位置分段显示（复用原有逻辑）
