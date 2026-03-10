# tests/test_fixed_mode.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication

_app = QApplication.instance() or QApplication(sys.argv)

def _make_box(mode='temp'):
    box = MagicMock()
    box.mode = mode
    return box

def test_switching_to_fixed_stops_existing_temp_boxes():
    """切换到固定模式时，已存在的临时框应该被改为 fixed（停止 dismiss timer）"""
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
    """切换回临时模式时，不强制改变已有框的模式"""
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
    """翻译完成时，若字幕已激活，应刷新字幕内容"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_active = True
    box._pending_auto = False

    result = {'original': 'hello', 'translated': '你好', 'source_lang': 'en',
              'target_lang': 'zh-CN', 'backend': 'google'}
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('你好')

def test_translate_done_no_subtitle_refresh_when_inactive():
    """字幕未激活时，翻译完成不调用 show_subtitle"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_active = False
    box._pending_auto = False

    result = {'original': 'hello', 'translated': '你好', 'source_lang': 'en',
              'target_lang': 'zh-CN', 'backend': 'google'}
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_not_called()

def test_overlay_requested_shows_all_when_none_active():
    """无字幕激活时，全局切换应对所有框调用 show_subtitle，传入 text 参数（无 _multi_results 时）"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {}

    box1 = MagicMock()
    box1._subtitle_active = False
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('译文')

    box1.show_subtitle.assert_called_once_with('译文')
    box2.show_subtitle.assert_called_once_with('译文')

def test_overlay_requested_uses_multi_results_when_available():
    """多框模式下，show_subtitle 应使用各框自己的 _multi_results 译文"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {1: {'translated': '框一译文'}, 2: {'translated': '框二译文'}}

    box1 = MagicMock()
    box1._subtitle_active = False
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('fallback')

    box1.show_subtitle.assert_called_once_with('框一译文')
    box2.show_subtitle.assert_called_once_with('框二译文')

def test_overlay_requested_hides_all_when_any_active():
    """有字幕激活时，全局切换应对所有框调用 hide_subtitle"""
    from core.controller import CoreController
    ctrl = CoreController.__new__(CoreController)
    ctrl._multi_results = {}

    box1 = MagicMock()
    box1._subtitle_active = True
    box1.box_id = 1
    box2 = MagicMock()
    box2._subtitle_active = False
    box2.box_id = 2
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_overlay_requested('译文')

    box1.hide_subtitle.assert_called_once()
    box2.hide_subtitle.assert_called_once()
