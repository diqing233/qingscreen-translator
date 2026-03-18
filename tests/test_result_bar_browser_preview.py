from html import unescape
from pathlib import Path

from tools.result_bar_browser_preview import DEFAULT_OUTPUT_PATH, build_preview_html, write_preview


def test_build_preview_html_contains_both_visual_directions():
    html = unescape(build_preview_html())

    assert "Calm Hierarchy" in html
    assert "Functional Color" in html
    assert html.count('data-preview="full-mockup"') == 2


def test_build_preview_html_covers_all_major_button_groups_and_states():
    html = unescape(build_preview_html())

    for label in (
        "Start & Session",
        "Modes & Languages",
        "Toolbar Utilities",
        "Source & Explain",
        "Window Controls",
        "normal",
        "hover",
        "pressed",
        "active",
        "disabled",
    ):
        assert label in html

    for control in (
        "开始框选",
        "停止/清空",
        "框选模式",
        "AI 模式",
        "源语言",
        "目标语言",
        "复制译文",
        "原文",
        "重新翻译",
        "AI 科普",
        "历史",
        "设置",
        "最小化",
        "关闭",
    ):
        assert control in html


def test_write_preview_creates_html_file():
    output_path = Path("docs/previews/test-result-bar-button-preview.html")

    try:
        written = write_preview(output_path)

        assert written == output_path
        assert output_path.exists()
        assert "ScreenTranslator Button Style Preview" in output_path.read_text(encoding="utf-8")
    finally:
        if output_path.exists():
            output_path.unlink()


def test_default_output_path_is_in_docs_previews():
    assert DEFAULT_OUTPUT_PATH == Path("docs/previews/result-bar-button-preview.html")
