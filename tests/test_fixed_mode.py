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
