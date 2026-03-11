# tests/test_fixed_mode.py
import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_box(mode='temp'):
    box = MagicMock()
    box.mode = mode
    return box


def test_switching_to_fixed_stops_existing_temp_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}

    box1 = _make_box('temp')
    box2 = _make_box('temp')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_box_mode_changed('fixed')

    box1.set_mode.assert_called_once_with('fixed')
    box2.set_mode.assert_called_once_with('fixed')


def test_switching_to_temp_does_not_change_existing_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'fixed'
    ctrl._multi_results = {}

    box1 = _make_box('fixed')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1}

    ctrl._on_box_mode_changed('temp')

    box1.set_mode.assert_not_called()


def test_translate_done_refreshes_active_subtitle():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'below'
    box._subtitle_active = True
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('ni hao')


def test_translate_done_refreshes_current_overlay_mode():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'over'
    box._subtitle_active = False
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('ni hao')


def test_translate_done_no_subtitle_refresh_when_overlay_disabled():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'off'
    box._subtitle_active = False
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_not_called()


def test_translate_done_stores_last_translation_even_when_overlay_disabled():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'off'
    box._subtitle_active = False
    box._pending_auto = False
    box._last_translation = ''

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    assert box._last_translation == 'ni hao'


def test_refresh_overlay_font_styles_updates_all_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    box1 = MagicMock()
    box2 = MagicMock()
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._refresh_overlay_font_styles()

    box1.refresh_overlay_style.assert_called_once_with()
    box2.refresh_overlay_style.assert_called_once_with()


def test_refresh_overlay_font_styles_ignores_boxes_without_refresh_method():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)

    box1 = MagicMock()
    box2 = object()
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._refresh_overlay_font_styles()

    box1.refresh_overlay_style.assert_called_once_with()


def test_controller_defaults_to_fixed_box_mode(monkeypatch):
    import core.history
    import core.settings
    from core.controller import CoreController

    monkeypatch.setattr(core.settings, 'SettingsStore', lambda: MagicMock())
    monkeypatch.setattr(core.history, 'HistoryDB', lambda: MagicMock())

    ctrl = CoreController(_app)

    assert ctrl._box_mode == 'fixed'
