# 段落翻译优化设计文档

**日期**：2026-03-15
**状态**：已批准

---

## 背景

当前段落翻译功能在小字体、密集多段落内容（如 14px 字体的英文长文）上存在两个问题：

1. **段落检测失效**：`_can_merge_lines` 使用固定系数 `max_line_height × 2.4` 作为合并阈值，对小字体内容，段落间距和行间距都小于该阈值，导致所有文字被合并成一段，分段按钮置灰。

2. **翻译匹配失败**：将多段文字用 `\n\n` 拼接后发给 Google/Bing/Baidu 等后端，后端往往不保留 `\n\n`，导致 `split('\n\n')` 数量不匹配，`paragraphs` 被清空为 `[]`。

**约束**：不增加额外 API 调用次数（多段落用一个翻译请求完成）。

---

## 设计

### 第一部分：自适应段落检测

**文件**：`src/core/overlay_layout.py`
**函数**：`group_rows_into_paragraphs`

#### 当前逻辑

```python
height_threshold = max(12, int(max(prev['height'], curr['height']) * 1.6 * (1 + gap_ratio)))
if vertical_gap > height_threshold:
    # 新段落
```

固定系数导致小字体内容阈值过高，无法区分行间距和段落间距。

#### 新逻辑

1. 将 `_can_merge_lines` 的阈值计算从固定系数改为自适应：
   - 在 `group_rows_into_paragraphs` 中，先将所有行分好（`_group_rows_into_lines`）
   - **边界条件**：若 `len(lines) <= 1`，直接将全部内容作为单段返回，跳过阈值计算
   - 收集所有相邻行之间的垂直间距列表 `gaps`（长度 = `len(lines) - 1`）
   - 计算下中位数（lower median）：`median_gap = sorted(gaps)[(len(gaps) - 1) // 2]`
   - `break_threshold = max(median_gap * 1.8, 6) * (1 + gap_ratio)`
   - **注意**：`gap_ratio` 在新公式中仍作为倍率调节器，但基准值从"行高的固定倍数"变为"实际行间距的中位数"，量级通常远小于旧公式。升级后建议保持默认值 `0.5` 不变；如果用户此前已将 `gap_ratio` 调高来应对旧算法，新算法下可能需要适当降低该值。
2. 遍历行时，若相邻两行的 gap > break_threshold 则分段，否则合并

#### 效果示例

| 字体大小 | 行间距 | 段落间距 | 旧阈值 | 新阈值（中位数=4px） | 结果 |
|---------|-------|---------|-------|-----------------|------|
| 14px    | 4px   | 10px    | 43px  | 7px             | 正确分段 ✓ |
| 20px    | 6px   | 16px    | 58px  | 11px            | 正确分段 ✓ |
| 30px    | 8px   | 22px    | 84px  | 14px            | 正确分段 ✓ |

`gap_ratio` 设置仍然有效，用于用户在设置中微调灵敏度。

---

### 第二部分：编号列表分隔符

**文件**：`src/core/controller.py`

#### 发送格式改动（`_normalize_ocr_payload`）

将多段落文字格式化为有序列表再发送翻译：

```
# 当前
text = '\n\n'.join(para_texts)

# 改为
text = '\n'.join(f'{i+1}. {t}' for i, t in enumerate(para_texts))
```

大多数翻译后端识别有序列表格式，输出时保留编号：
```
1. First paragraph → 1. 第一段译文
2. Second paragraph → 2. 第二段译文
```

#### 解析策略（`_on_translate_done`）

提取一个独立辅助函数 `_parse_paragraph_translations(text, count) -> list[str]`，按优先级回退。**每一级：当且仅当 `len(result) == count` 时才使用该级结果，否则继续到下一级**：

1. **编号行正则**：`re.findall(r'^\d+[.)]\s*(.+)', text, re.MULTILINE)` → 仅当数量恰好等于 `count` 时使用
2. **双换行分割**：`[p.strip() for p in text.split('\n\n') if p.strip()]` → 仅当数量恰好等于 `count` 时使用
3. **单换行分割**：`[p.strip() for p in text.split('\n') if p.strip()]` → 仅当数量恰好等于 `count` 时使用
4. **全部失败**：返回 `[]`，`paragraphs=[]`，分段按钮置灰（与当前行为一致）

> 说明：正则会匹配所有以数字开头的行（包括翻译内容本身含有的编号），因此必须严格检查数量是否等于 `count`，不能在数量不符时直接使用。

---

## 不涉及的范围

- `result_bar.py`：显示逻辑不变（`[1] 译文 [2] 译文` 格式保持）
- 翻译后端（`router.py`、各 backend）：不改动
- `_format_para_text`：不改动
- 分段按钮 UI 逻辑：不改动
- `_run_paragraph_translate`（`controller.py` 第 406 行）：这是覆盖字幕（overlay）功能专用的逐段翻译路径，每个段落单独发请求，**不走编号列表格式，不受本次改动影响**，与新的 `_parse_paragraph_translations` 解析逻辑是完全独立的两条路径，互不干扰。

---

## 文件变更汇总

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/core/overlay_layout.py` | 修改 | `group_rows_into_paragraphs` 自适应阈值 |
| `src/core/controller.py` | 修改 | `_normalize_ocr_payload` 改发送格式；`_on_translate_done` 新增解析辅助函数 |
