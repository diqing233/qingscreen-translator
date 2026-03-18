import os
import sys
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_settings(**overrides):
    settings = MagicMock()
    values = {
        'source_language': 'auto',
        'target_language': 'zh-CN',
        'result_bar_position': 'top',
        'result_bar_opacity': 0.85,
        'overlay_default_mode': 'off',
        'overlay_font_delta': 0,
        'skin': 'deep_space',
        'button_style_variant': 'calm',
    }
    values.update(overrides)

    def get_value(key, default=None):
        return values.get(key, default)

    settings.get.side_effect = get_value
    settings.set.side_effect = lambda key, value: values.__setitem__(key, value)
    settings._values = values
    return settings


def _make_bar(**overrides):
    from ui.result_bar import ResultBar

    bar = ResultBar(_make_settings(**overrides))
    bar.show()
    _app.processEvents()
    return bar


def _result(original='hello world', translated='你好，世界'):
    return {
        'original': original,
        'translated': translated,
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'test',
    }


def test_toggle_is_placed_after_copy_button():
    bar = _make_bar()
    layout = bar._tb_scroll.widget().layout()

    assert layout.indexOf(bar._toggle) > layout.indexOf(bar._btn_copy_trans)


def test_stop_clear_button_is_placed_after_play_button():
    bar = _make_bar()
    layout = bar._tb_scroll.widget().layout()

    assert layout.indexOf(bar._btn_stop_clear) > layout.indexOf(bar._btn_play)
    assert layout.indexOf(bar._btn_stop_clear) < layout.indexOf(bar._btn_reset_size)


def test_toolbar_width_refreshes_when_toggle_visibility_changes():
    bar = _make_bar()
    content = bar._tb_scroll.widget()
    fixed_width = content.geometry().width()

    bar._on_mode_btn_click('temp')
    _app.processEvents()
    temp_width = content.geometry().width()

    bar._on_mode_btn_click('fixed')
    _app.processEvents()

    assert temp_width < fixed_width
    assert content.geometry().width() == fixed_width


def test_default_width_fits_toolbar_in_fixed_mode():
    bar = _make_bar()

    bar._on_mode_btn_click('fixed')
    _app.processEvents()

    assert bar._tb_scroll.viewport().width() >= bar._tb_scroll.widget().width()


def test_language_buttons_reserve_enough_width_for_labels():
    bar = _make_bar()

    assert bar._btn_src_lang.minimumWidth() >= bar._btn_src_lang.sizeHint().width()
    assert bar._btn_tgt_lang.minimumWidth() >= bar._btn_tgt_lang.sizeHint().width()


def test_result_bar_no_longer_exposes_overlay_controls():
    bar = _make_bar()

    assert not hasattr(bar, '_btn_overlay')
    assert not hasattr(bar, '_btn_overlay_font_up')
    assert not hasattr(bar, '_btn_overlay_font_down')


def test_box_mode_cycle_button_rotates_modes():
    from ui.result_bar import BOX_MODE_META

    bar = _make_bar()

    assert bar._box_mode == 'fixed'
    assert bar._toggle.isVisible()
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['fixed'][0]

    bar._btn_box_mode_cycle.click()
    _app.processEvents()
    assert bar._box_mode == 'temp'
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['temp'][0]

    bar._btn_box_mode_cycle.click()
    _app.processEvents()
    assert bar._box_mode == 'multi'
    assert bar._toggle.isVisible()
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['multi'][0]

    bar._btn_box_mode_cycle.click()
    _app.processEvents()
    assert bar._box_mode == 'fixed'
    assert bar._toggle.isVisible()
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['fixed'][0]


def test_source_panel_expands_downward_without_moving_top_edge():
    bar = _make_bar()
    bar.show_result(_result())
    _app.processEvents()
    original_y = bar.y()
    original_height = bar.height()
    translation_height = bar._lbl_translation.height()

    bar._toggle_source()
    _app.processEvents()

    assert bar.y() == original_y
    assert bar.height() > original_height
    assert bar._source_editor.isVisible()
    assert abs(bar._lbl_translation.height() - translation_height) <= 4
    assert not bar._btn_retranslate.isEnabled()


def test_retranslate_button_is_placed_between_copy_source_and_ai_buttons():
    bar = _make_bar()
    bar.show_result(_result())
    _app.processEvents()

    source_pos = bar._btn_source.mapTo(bar._body, bar._btn_source.rect().topLeft())
    copy_pos = bar._btn_copy_src.mapTo(bar._body, bar._btn_copy_src.rect().topLeft())
    retranslate_pos = bar._btn_retranslate.mapTo(bar._body, bar._btn_retranslate.rect().topLeft())
    ai_pos = bar._btn_ai.mapTo(bar._body, bar._btn_ai.rect().topLeft())

    assert max(source_pos.y(), copy_pos.y(), retranslate_pos.y(), ai_pos.y()) - min(
        source_pos.y(), copy_pos.y(), retranslate_pos.y(), ai_pos.y()
    ) <= 2
    assert source_pos.x() < copy_pos.x() < retranslate_pos.x() < ai_pos.x()


def test_action_row_buttons_share_consistent_height():
    bar = _make_bar()
    bar.show_result(_result())
    _app.processEvents()

    heights = {
        bar._btn_source.height(),
        bar._btn_copy_src.height(),
        bar._btn_retranslate.height(),
        bar._btn_ai.height(),
    }

    assert len(heights) == 1


def test_ai_split_button_emits_left_and_right_clicks_from_respective_regions():
    bar = _make_bar()
    left = []
    right = []
    bar._btn_ai.left_clicked.connect(lambda: left.append('left'))
    bar._btn_ai.right_clicked.connect(lambda: right.append('right'))

    left_event = MagicMock()
    left_event.button.return_value = Qt.LeftButton
    left_event.x.return_value = 2

    right_event = MagicMock()
    right_event.button.return_value = Qt.LeftButton
    right_event.x.return_value = bar._btn_ai.width() - 2

    bar._btn_ai.mousePressEvent(left_event)
    bar._btn_ai.mousePressEvent(right_event)

    assert left == ['left']
    assert right == ['right']


def test_content_splitter_starts_with_translation_panel_only():
    bar = _make_bar()

    assert bar._content_splitter.orientation() == Qt.Vertical
    assert bar._content_splitter.count() == 1
    assert bar._content_splitter.widget(0) is bar._translation_panel


def test_source_toggle_inserts_editable_source_panel_into_content_splitter():
    bar = _make_bar()
    bar.show_result(_result(original='source text'))
    _app.processEvents()

    bar._toggle_source()
    _app.processEvents()

    button_bottom = bar._btn_source.mapTo(bar._body, bar._btn_source.rect().bottomLeft()).y()
    translation_top = bar._translation_panel.mapTo(bar._body, bar._translation_panel.rect().topLeft()).y()
    translation_bottom = bar._translation_panel.mapTo(bar._body, bar._translation_panel.rect().bottomLeft()).y()
    source_top = bar._source_panel.mapTo(bar._body, bar._source_panel.rect().topLeft()).y()

    assert bar._content_splitter.count() == 2
    assert bar._content_splitter.widget(1) is bar._source_panel
    assert bar._source_panel.isVisible()
    assert not hasattr(bar, '_lbl_source')
    assert bar._source_editor.toPlainText() == 'source text'
    # button row is now inside translation_panel (below translation text, above source panel)
    assert translation_top <= button_bottom <= translation_bottom
    assert 0 <= source_top - translation_bottom <= 10


def test_source_toggle_keeps_button_hit_target_clickable():
    bar = _make_bar()
    bar.show_result(_result())
    _app.processEvents()

    bar._toggle_source()
    _app.processEvents()

    hit = QApplication.widgetAt(bar._btn_source.mapToGlobal(bar._btn_source.rect().center()))

    assert hit is bar._btn_source


def test_explain_panel_reuses_single_content_panel():
    bar = _make_bar()
    bar.show_result(_result())
    _app.processEvents()

    bar.show_explain_loading()
    _app.processEvents()

    assert bar._content_splitter.count() == 2
    assert bar._content_splitter.widget(1) is bar._explain_panel
    assert bar._explain_panel.isVisible()
    assert bar._explain_loading_label.isVisible()
    assert not bar._explain_text.isVisible()

    bar.show_explain('facts')
    _app.processEvents()

    assert bar._content_splitter.count() == 2
    assert bar._content_splitter.widget(1) is bar._explain_panel
    assert not bar._explain_loading_label.isVisible()
    assert bar._explain_text.isVisible()
    assert bar._explain_text.toPlainText() == 'facts'


def test_collapsing_panels_removes_them_from_content_splitter():
    bar = _make_bar()
    bar.show_result(_result())
    bar._toggle_source()
    bar.show_explain('facts')
    _app.processEvents()

    assert bar._content_splitter.count() == 3

    bar._toggle_source()
    _app.processEvents()

    assert bar._content_splitter.count() == 2
    assert bar._content_splitter.widget(1) is bar._explain_panel

    bar._toggle_explain_section()
    _app.processEvents()

    assert bar._content_splitter.count() == 1
    assert bar._content_splitter.widget(0) is bar._translation_panel


def test_splitter_sections_can_be_resized_independently():
    bar = _make_bar()
    bar.resize(bar.width(), 420)
    bar.show_result(_result())
    bar._toggle_source()
    bar._source_editor.setPlainText('edited source')
    bar.show_explain('facts\nmore facts\nthird line')
    _app.processEvents()

    before = (
        bar._translation_panel.height(),
        bar._source_panel.height(),
        bar._explain_panel.height(),
    )

    assert bar._content_splitter.count() == 3

    bar._content_splitter.setSizes([220, 110, 70])
    _app.processEvents()

    after = (
        bar._translation_panel.height(),
        bar._source_panel.height(),
        bar._explain_panel.height(),
    )

    assert after != before
    assert after[0] > after[2]
    assert after[1] > 0
    assert after[2] > 0


def test_ai_panel_expands_downward_and_uses_edited_source_text():
    bar = _make_bar()
    bar.show_result(_result())
    bar._toggle_source()
    bar._source_editor.setPlainText('edited source')
    _app.processEvents()

    original_y = bar.y()
    original_height = bar.height()
    translation_height = bar._lbl_translation.height()
    seen = []
    bar.explain_requested.connect(seen.append)

    bar._on_explain()
    _app.processEvents()

    assert seen == ['edited source']
    assert bar.y() == original_y
    assert bar.height() > original_height
    assert bar._explain_panel.isVisible()
    assert abs(bar._lbl_translation.height() - translation_height) <= 4


def test_manual_source_entry_can_trigger_retranslation_without_ocr_text():
    bar = _make_bar()
    bar._toggle_source()
    _app.processEvents()

    assert not bar._btn_retranslate.isEnabled()

    bar._source_editor.setPlainText('manual source')
    _app.processEvents()

    seen = []
    bar.retranslate_requested.connect(seen.append)

    assert bar._btn_retranslate.isEnabled()

    bar._btn_retranslate.click()
    _app.processEvents()

    assert not bar._btn_retranslate.isEnabled()
    assert seen == ['manual source']


def test_retranslate_remains_disabled_until_source_text_changes():
    bar = _make_bar()
    bar.show_result(_result(original='same source'))
    bar._toggle_source()
    _app.processEvents()

    assert not bar._btn_retranslate.isEnabled()

    bar._source_editor.setPlainText('same source')
    _app.processEvents()

    assert not bar._btn_retranslate.isEnabled()

    bar._source_editor.setPlainText('updated source')
    _app.processEvents()

    assert bar._btn_retranslate.isEnabled()


def test_show_result_does_not_overwrite_active_source_edits():
    bar = _make_bar()
    bar.show_result(_result(original='first source'))
    bar._toggle_source()
    bar._source_editor.setPlainText('edited source')
    _app.processEvents()

    bar.show_result(_result(original='new source', translated='新译文'))
    _app.processEvents()

    assert bar._source_editor.toPlainText() == 'edited source'


def test_clear_current_content_resets_source_editor_and_explain_panel():
    bar = _make_bar()
    bar.show_result(_result())
    bar._toggle_source()
    bar._source_editor.setPlainText('edited source')
    bar.show_explain('facts')
    _app.processEvents()

    bar.clear_current_content()
    _app.processEvents()

    assert bar._source_editor.toPlainText() == ''
    assert not bar._source_panel.isVisible()
    assert not bar._explain_panel.isVisible()
    assert not bar._btn_retranslate.isEnabled()
    assert bar._explain_text.toPlainText() == ''


def test_button_style_variant_changes_result_bar_button_styles():
    calm = _make_bar(button_style_variant='calm')
    semantic = _make_bar(button_style_variant='semantic')

    assert calm._btn_play.styleSheet() != semantic._btn_play.styleSheet()
    assert calm._btn_retranslate.styleSheet() != semantic._btn_retranslate.styleSheet()


@pytest.mark.parametrize('variant', ['calm', 'semantic'])
def test_result_bar_uses_custom_copy_and_broom_icons_for_each_variant(variant):
    bar = _make_bar(button_style_variant=variant)
    bar.set_stop_clear_busy(False)

    assert bar._skin['button_style_variant'] == variant
    assert not bar._btn_copy_trans.icon().isNull()
    assert not bar._btn_copy_src.icon().isNull()
    assert '📋' not in bar._btn_copy_src.text()
    assert not bar._btn_stop_clear.icon().isNull()
