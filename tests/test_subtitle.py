import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtCore import QPoint, QRect, Qt
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


def _has_opaque_pixel(widget):
    image = widget.grab().toImage()
    for y in range(image.height()):
        for x in range(image.width()):
            if image.pixelColor(x, y).alpha() > 0:
                return True
    return False


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

    sw = box._subtitle_inbox_win
    assert sw is not None
    assert sw.isVisible()
    assert sw.parent() is box
    assert box._subtitle_paragraph_wins == []


def test_overlay_mode_over_uses_paragraph_bars_when_data_exists():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')

    assert len(box._subtitle_paragraph_wins) == 2
    assert all(win.isVisible() for win in box._subtitle_paragraph_wins)
    assert all(win.parent() is box for win in box._subtitle_paragraph_wins)
    assert box._subtitle_paragraph_wins[0].x() >= 10
    assert box._subtitle_paragraph_wins[1].y() >= 38


def test_paragraph_overlays_stay_below_toolbar_safe_area():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')
    _app.processEvents()

    safe_top = box._btn_bar.sizeHint().height() + 6
    first_rect = box._subtitle_paragraph_wins[0].geometry()
    second_rect = box._subtitle_paragraph_wins[1].geometry()

    assert first_rect.y() >= safe_top
    assert not first_rect.intersects(box._btn_bar.geometry())
    assert first_rect.bottom() < second_rect.top()


def test_overlay_mode_over_uses_dark_backdrop():
    box, _ = _make_box()
    box.show()
    box.set_overlay_mode('over')
    box.show_subtitle('short text')

    style = box._subtitle_inbox_win.styleSheet()
    assert 'background: rgba(6, 10, 16, 244);' in style
    assert 'border: 1px solid rgba(150, 190, 235, 110);' in style


def test_overlay_mode_below_uses_dark_backdrop():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('below mode')

    style = box._subtitle_win.styleSheet()
    assert 'background: rgba(6, 10, 16, 232);' in style
    assert 'border: 1px solid rgba(120, 165, 230, 90);' in style


def test_single_overlay_window_is_mouse_transparent():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('hover passthrough')

    assert box._subtitle_win.testAttribute(Qt.WA_TransparentForMouseEvents)


def test_paragraph_overlay_windows_are_mouse_transparent():
    box, _ = _make_box()
    box.show()
    _set_paragraph_overlay_data(box)
    box.set_overlay_mode('over')
    box.show_subtitle('full translation')

    assert all(win.testAttribute(Qt.WA_TransparentForMouseEvents) for win in box._subtitle_paragraph_wins)


def test_overlay_window_grab_contains_visible_backdrop_pixels():
    box, _ = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('over mode')
    _app.processEvents()

    assert _has_opaque_pixel(box._subtitle_inbox_win)


def test_toolbar_visibility_uses_original_box_geometry():
    box, _ = _make_box()
    box.show()
    box.set_overlay_mode('over')
    box.show_subtitle('hover text')

    box._refresh_toolbar_visibility(QPoint(box.x() + 10, box.y() + 35))
    assert box._btn_bar.isVisible()

    box._refresh_toolbar_visibility(QPoint(box.x() - 10, box.y() - 10))
    assert not box._btn_bar.isVisible()


def test_below_overlay_area_outside_box_does_not_keep_toolbar_visible():
    box, _ = _make_box(overlay_default_mode='below')
    box.show()
    box.show_subtitle('below mode')

    box._refresh_toolbar_visibility(QPoint(box.x() + 20, box.y() + box.height() + 10))

    assert not box._btn_bar.isVisible()


def test_pin_button_locks_current_box_position():
    box, _ = _make_box()
    box.show()
    initial_pos = box.pos()

    press_event = MagicMock()
    press_event.button.return_value = Qt.LeftButton
    press_event.globalPos.return_value = QPoint(box.x() + 10, box.y() + 10)

    move_event = MagicMock()
    move_event.buttons.return_value = Qt.LeftButton
    move_event.globalPos.return_value = QPoint(box.x() + 80, box.y() + 60)

    box._on_toggle_pin()
    box.mousePressEvent(press_event)
    box.mouseMoveEvent(move_event)

    assert getattr(box, '_position_locked', False) is True
    assert box.pos() == initial_pos


def test_locked_temp_box_does_not_emit_close_on_dismiss_timeout():
    box, _ = _make_box()
    box.show()
    box.set_mode('temp')
    closed = []
    box.close_requested.connect(lambda current: closed.append(current))

    box._on_toggle_pin()
    box._on_dismiss_timeout()

    assert closed == []


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

    top_left = box._subtitle_paragraph_wins[0].mapToGlobal(QPoint(0, 0))
    assert top_left.x() >= 310
    assert top_left.y() >= 208


def test_overlay_font_delta_updates_font_size():
    box, values = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('font test')
    initial_size = box._subtitle_inbox_win.font().pixelSize()

    values['overlay_font_delta'] = 4
    box.refresh_overlay_style()

    assert box._subtitle_inbox_win.font().pixelSize() > initial_size


def test_overlay_default_font_size_stays_compact_for_paragraph_boxes():
    box, _ = _make_box(overlay_default_mode='over')
    box.show()
    box.show_subtitle('paragraph overlay')

    assert 12 <= box._subtitle_inbox_win.font().pixelSize() <= 18


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
