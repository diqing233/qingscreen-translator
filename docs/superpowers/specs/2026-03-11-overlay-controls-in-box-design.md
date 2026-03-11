# Overlay Controls In Box Design

**Date:** 2026-03-11

## Goal

把覆盖翻译的操作入口从结果条移到每个翻译框内部，并提升“覆盖在原文上”模式的可读性。

## Decisions

1. 结果条不再显示覆盖按钮和覆盖字号按钮。
2. 每个翻译框顶部按钮栏新增三枚控件：
   - `⊞`：循环切换 `off -> over -> below`
   - `A-`：减小覆盖译文字号
   - `A+`：增大覆盖译文字号
3. 字号调整仍写入全局设置 `overlay_font_delta`，这样设置页与框内操作保持一致。
4. `over` 模式从“整块铺满框体”调整为“框内自适应小底板”，减少遮挡并提高对比度。

## UX Notes

- `over` 模式使用更深的半透明背景、更亮的文字和更明显的描边。
- 小底板默认贴近框左上角，宽高跟随内容自适应，但不超出框体。
- `below` 模式保持现有“原文下方显示”行为。

## Impacted Files

- `src/ui/result_bar.py`
- `src/ui/translation_box.py`
- `src/core/controller.py`
- `tests/test_result_bar_toolbar.py`
- `tests/test_subtitle.py`

