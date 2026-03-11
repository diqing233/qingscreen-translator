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
    settings.set.side_effect = lambda key, value: values.__setitem__(key, value)
    settings._values = values

    from ui.translation_box import TranslationBox

    box = TranslationBox(QRect(100, 100, 200, 80), box_id=1, settings=settings)
    return box, values


def _set_paragraph_overlay_data(box):
    box._last_ocr_paragraphs = [
        {'text': 'para 1', 'rect': {'x': 10, 'y': 8, 'width': 70, 'height': 16}},
        {'text': 'para 2', 'rect': {'x': 20, 'y': 38, 'width': 90, 'height': 16}},
    ]
    box._last_paragraph_translations = ['第一段', '第二段']


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


def test_overlay_mode_over_without_paragraph_data_uses_single_fallback_bar():
    box, _ = _make_box()
    box.show()
    box.set_overlay_mode('over')
    box.show_subtitle('short text')

    sw = box._subtitle_win
    assert sw is not None
    assert sw.isVisible()
    assert box._subtitle_paragraph_wins == []


def test_overlay_mode_over_uses_paragraph_bars_when_data_exists():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')

    assert len(box._subtitle_paragraph_wins) == 2
    assert all(win.isVisible() for win in box._subtitle_paragraph_wins)
    assert box._subtitle_paragraph_wins[0].x() >= box.x() + 10
    assert box._subtitle_paragraph_wins[1].y() >= box.y() + 38


def test_overlay_mode_over_uses_dark_backdrop():
    box, _ = _make_box()
    box.show()
    box.set_overlay_mode('over')
    box.show_subtitle('short text')

    style = box._subtitle_win.styleSheet()
    assert 'background: rgba(6, 10, 16, 244);' in style
    assert 'border: 1px solid rgba(150, 190, 235, 110);' in style


def test_overlay_mode_below_uses_dark_backdrop():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('below mode')

    style = box._subtitle_win.styleSheet()
    assert 'background: rgba(6, 10, 16, 232);' in style
    assert 'border: 1px solid rgba(120, 165, 230, 90);' in style


def test_subtitle_follows_box_on_move():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('move test')

    box.move(300, 200)

    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()


def test_paragraph_subtitles_follow_box_on_move():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')

    box.move(300, 200)

    assert box._subtitle_paragraph_wins[0].x() >= 310
    assert box._subtitle_paragraph_wins[0].y() >= 208


def test_overlay_font_delta_updates_font_size():
    box, values = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('font test')
    initial_size = box._subtitle_win.font().pixelSize()

    values['overlay_font_delta'] = 4
    box.refresh_overlay_style()

    assert box._subtitle_win.font().pixelSize() > initial_size


def test_overlay_default_font_size_stays_compact_for_paragraph_boxes():
    box, _ = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('paragraph overlay')

    assert 12 <= box._subtitle_win.font().pixelSize() <= 18


def test_overlay_controls_live_in_translation_box_toolbar():
    box, _ = _make_box()
    layout = box._btn_bar.layout()

    assert layout.indexOf(box._btn_overlay_font_down) > layout.indexOf(box._btn_subtitle)
    assert layout.indexOf(box._btn_overlay_font_up) > layout.indexOf(box._btn_overlay_font_down)


def test_box_overlay_font_buttons_adjust_settings():
    box, values = _make_box()

    box._btn_overlay_font_up.click()
    _app.processEvents()
    assert values['overlay_font_delta'] == 1

    box._btn_overlay_font_down.click()
    _app.processEvents()
    assert values['overlay_font_delta'] == 0


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


def test_set_overlay_mode_emits_overlay_mode_changed_signal():
    box, _ = _make_box()
    seen = []
    box.overlay_mode_changed.connect(lambda current, mode: seen.append((current, mode)))

    box.set_overlay_mode('over')
    box.set_overlay_mode('below')

    assert seen == [(box, 'over'), (box, 'below')]


def test_close_event_destroys_subtitle_win():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('close test')

    assert box._subtitle_win is not None

    box.close()

    assert box._subtitle_win is None


def test_close_event_destroys_paragraph_subtitle_wins():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')

    assert len(box._subtitle_paragraph_wins) == 2

    box.close()

    assert box._subtitle_paragraph_wins == []
