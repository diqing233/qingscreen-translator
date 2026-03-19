# 临时模式隐藏翻译条 设计文档

**日期**：2026-03-19
**状态**：已批准

## 背景

当前临时模式下，翻译完成后 result_bar（顶部深色浮动条）会弹出显示结果。用户希望在临时模式下默认隐藏翻译条，翻译结果直接以覆盖字幕形式显示在选区框下方，减少界面干扰。

## 目标

1. 切换到临时模式时，弹出一次性提示，告知用户行为变化
2. 用户确认后，result_bar 最小化，之后不主动弹出
3. 快捷键翻译完成后，结果自动显示在翻译框下方（OVERLAY_BELOW）
4. 用户可在设置界面关闭此行为，或重置提示

## 数据层

新增两个设置项（读写方式与现有 `settings.get/set` 一致）：

| Key | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `temp_mode_hide_bar` | bool | `true` | 临时模式下是否隐藏翻译条 |
| `temp_mode_hint_dismissed` | bool | `false` | 用户是否已永久关闭提示 |

## 提示对话框

**类**：`_TempModeHintDialog(QDialog)`，位于 `result_bar.py`

**触发条件**：用户在 result_bar 切换到"临时"模式，且 `temp_mode_hint_dismissed == False`

**内容**：
```
临时模式提示

翻译条将自动最小化，翻译结果会直接
显示在选区框下方。

按 Alt+Q 框选并翻译。

[不再提示]    [好的]
```

**按钮行为**：
- "好的"：关闭对话框，最小化 result_bar
- "不再提示"：同上 + 写入 `temp_mode_hint_dismissed=true`

**样式**：跟随当前皮肤（通过 `get_skin` 取色），无边框，圆角。

## 翻译流程变更

**改动位置**：`controller.py` 中翻译完成的回调

**判断条件**：当前 box_mode 为 `temp` 且 `temp_mode_hide_bar == true`

**新流程**：
1. Alt+Q 触发框选翻译
2. OCR + 翻译完成
3. controller 检查条件：
   - 满足 → 不调用 result_bar 显示逻辑；将当前 translation_box overlay 模式设为 `OVERLAY_BELOW`；调用 `translation_box.show_subtitle(text)`
   - 不满足 → 走原有逻辑，正常显示 result_bar

**result_bar 最小化时机**：用户在提示对话框点击确认后，立即调用现有 `_minimize()` 方法。

## 设置界面

**位置**：`settings_window.py`，General 标签页

**新增控件**：
```
☑ 临时模式下隐藏翻译条（翻译结果显示在选区框下方）
   [重置提示]
```

- 复选框绑定 `temp_mode_hide_bar`
- "重置提示"为小号文字链接按钮，点击后将 `temp_mode_hint_dismissed` 写回 `false`

## 涉及文件

| 文件 | 改动内容 |
|------|----------|
| `src/ui/result_bar.py` | 新增 `_TempModeHintDialog`；切换临时模式时触发提示；最小化逻辑 |
| `src/core/controller.py` | 翻译完成回调中加条件判断，临时模式走覆盖显示 |
| `src/ui/settings_window.py` | General 标签页新增复选框 + 重置提示按钮 |

## 不在范围内

- 固定模式、多框模式的行为不变
- 不修改现有覆盖翻译（overlay）系统的逻辑
- 不新增快捷键
