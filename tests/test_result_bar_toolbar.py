import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_settings():
    settings = MagicMock()

    def get_value(key, default=None):
        values = {
            'source_language': 'auto',
            'target_language': 'zh-CN',
            'result_bar_position': 'top',
            'result_bar_opacity': 0.85,
        }
        return values.get(key, default)

    settings.get.side_effect = get_value
    return settings


def _make_bar():
    from ui.result_bar import ResultBar

    bar = ResultBar(_make_settings())
    bar.show()
    _app.processEvents()
    return bar


def test_toggle_is_placed_after_overlay_button():
    bar = _make_bar()
    layout = bar._tb_scroll.widget().layout()

    assert layout.indexOf(bar._toggle) > layout.indexOf(bar._btn_overlay)


def test_stop_clear_button_is_placed_after_play_button():
    bar = _make_bar()
    layout = bar._tb_scroll.widget().layout()

    assert layout.indexOf(bar._btn_stop_clear) > layout.indexOf(bar._btn_play)
    assert layout.indexOf(bar._btn_stop_clear) < layout.indexOf(bar._btn_reset_size)


def test_toolbar_width_refreshes_when_toggle_becomes_visible():
    bar = _make_bar()
    content = bar._tb_scroll.widget()
    initial_width = content.geometry().width()

    bar._on_mode_btn_click('fixed')
    _app.processEvents()

    assert content.geometry().width() > initial_width


def test_default_width_fits_toolbar_in_fixed_mode():
    bar = _make_bar()

    bar._on_mode_btn_click('fixed')
    _app.processEvents()

    assert bar._tb_scroll.viewport().width() >= bar._tb_scroll.widget().width()


def test_language_buttons_reserve_enough_width_for_labels():
    bar = _make_bar()

    assert bar._btn_src_lang.minimumWidth() >= bar._btn_src_lang.sizeHint().width()
    assert bar._btn_tgt_lang.minimumWidth() >= bar._btn_tgt_lang.sizeHint().width()
