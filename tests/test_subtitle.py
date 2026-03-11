import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_box(overlay_default_mode='off', overlay_font_delta=0):
    values = {
        'overlay_default_mode': overlay_default_mode,
        'overlay_font_delta': overlay_font_delta,
    }
    settings = MagicMock()
    settings.get.side_effect = lambda key, default=None: values.get(key, default)
    settings._values = values

    from ui.translation_box import TranslationBox

    box = TranslationBox(QRect(100, 100, 200, 80), box_id=1, settings=settings)
    return box, values


def test_subtitle_win_initially_none():
    box, _ = _make_box()
    assert box._subtitle_win is None
    assert box._subtitle_active is False
    assert box._subtitle_mode == 'off'


def test_show_subtitle_creates_win_and_shows():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('hello world')

    assert box._subtitle_win is not None
    assert box._subtitle_win.isVisible()
    assert box._subtitle_active is True


def test_hide_subtitle_hides_win():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('hello world')

    box.hide_subtitle()

    assert not box._subtitle_win.isVisible()
    assert box._subtitle_active is False


def test_overlay_mode_defaults_from_settings():
    box, _ = _make_box(overlay_default_mode='below')
    assert box._subtitle_mode == 'below'
    assert box._subtitle_active is False


def test_subtitle_position_below_box():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('below mode')

    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()
    assert sw.width() == box.width()


def test_overlay_mode_over_positions_overlay_inside_box():
    box, _ = _make_box()
    box.show()
    box.set_overlay_mode('over')
    box.show_subtitle('over mode')

    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y()
    assert sw.width() == box.width()
    assert sw.height() <= box.height()


def test_subtitle_follows_box_on_move():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('move test')

    box.move(300, 200)

    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()


def test_overlay_font_delta_updates_font_size():
    box, values = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('font test')
    initial_size = box._subtitle_win.font().pixelSize()

    values['overlay_font_delta'] = 4
    box.refresh_overlay_style()

    assert box._subtitle_win.font().pixelSize() > initial_size


def test_toggle_subtitle_cycles_modes():
    box, _ = _make_box()
    box.show()
    box._last_translation = 'cycle test'

    box._on_toggle_subtitle()
    assert box._subtitle_mode == 'over'
    assert box._subtitle_active is True

    box._on_toggle_subtitle()
    assert box._subtitle_mode == 'below'
    assert box._subtitle_active is True

    box._on_toggle_subtitle()
    assert box._subtitle_mode == 'off'
    assert box._subtitle_active is False


def test_close_event_destroys_subtitle_win():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('close test')

    assert box._subtitle_win is not None

    box.close()

    assert box._subtitle_win is None
