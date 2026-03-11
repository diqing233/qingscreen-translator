import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_settings():
    settings = MagicMock()
    values = {
        'source_language': 'auto',
        'target_language': 'zh-CN',
        'result_bar_position': 'top',
        'result_bar_opacity': 0.85,
        'overlay_default_mode': 'off',
        'overlay_font_delta': 0,
    }

    def get_value(key, default=None):
        return values.get(key, default)

    settings.get.side_effect = get_value
    settings.set.side_effect = lambda key, value: values.__setitem__(key, value)
    settings._values = values
    return settings


def _make_bar():
    from ui.result_bar import ResultBar

    bar = ResultBar(_make_settings())
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
    assert bar._box_mode == 'multi'
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['multi'][0]

    bar._btn_box_mode_cycle.click()
    _app.processEvents()
    assert bar._box_mode == 'temp'
    assert not bar._toggle.isVisible()
    assert bar._btn_box_mode_cycle.text() == BOX_MODE_META['temp'][0]

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

    bar._toggle_source()
    _app.processEvents()

    assert bar.y() == original_y
    assert bar.height() > original_height
    assert bar._source_editor.isVisible()
    assert bar._btn_retranslate.isEnabled()


def test_ai_panel_expands_downward_and_uses_edited_source_text():
    bar = _make_bar()
    bar.show_result(_result())
    bar._toggle_source()
    bar._source_editor.setPlainText('edited source')
    _app.processEvents()

    original_y = bar.y()
    original_height = bar.height()
    seen = []
    bar.explain_requested.connect(seen.append)

    bar._on_explain()
    _app.processEvents()

    assert seen == ['edited source']
    assert bar.y() == original_y
    assert bar.height() > original_height
    assert bar._explain_panel.isVisible()


def test_manual_source_entry_can_trigger_retranslation_without_ocr_text():
    bar = _make_bar()
    bar._toggle_source()
    _app.processEvents()

    assert not bar._btn_retranslate.isEnabled()

    bar._source_editor.setPlainText('manual source')
    _app.processEvents()

    seen = []
    bar.retranslate_requested.connect(seen.append)
    bar._btn_retranslate.click()
    _app.processEvents()

    assert bar._btn_retranslate.isEnabled()
    assert seen == ['manual source']


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
