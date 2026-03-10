import os
import sys
import tempfile
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.settings import SettingsStore

_app = QApplication.instance() or QApplication(sys.argv)


def make_controller():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.app = MagicMock()
    ctrl.settings = MagicMock()
    ctrl.result_bar = MagicMock()
    ctrl.tray = MagicMock()
    ctrl._ask_close_behavior = MagicMock()
    ctrl._is_tray_available = MagicMock(return_value=True)
    ctrl._warn_tray_unavailable = MagicMock()
    return ctrl


def test_close_request_hides_to_tray_when_behavior_is_tray():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'tray'

    CoreController._handle_result_bar_close(ctrl)

    ctrl.result_bar.hide.assert_called_once()
    ctrl.app.quit.assert_not_called()


def test_close_request_quits_when_behavior_is_quit():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'quit'

    CoreController._handle_result_bar_close(ctrl)

    ctrl.app.quit.assert_called_once()
    ctrl.result_bar.hide.assert_not_called()


def test_close_request_asks_and_remembers_tray_choice():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior.return_value = ('tray', True)

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_called_once_with('close_button_behavior', 'tray')
    ctrl.result_bar.hide.assert_called_once()


def test_close_request_asks_without_remembering_keeps_ask_setting():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior.return_value = ('tray', False)

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_not_called()
    ctrl.result_bar.hide.assert_called_once()


def test_close_request_asks_and_remembers_quit_choice():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior.return_value = ('quit', True)

    CoreController._handle_result_bar_close(ctrl)

    ctrl.settings.set.assert_called_once_with('close_button_behavior', 'quit')
    ctrl.app.quit.assert_called_once()


def test_close_request_cancel_does_nothing():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'ask'
    ctrl._ask_close_behavior.return_value = (None, False)

    CoreController._handle_result_bar_close(ctrl)

    ctrl.result_bar.hide.assert_not_called()
    ctrl.app.quit.assert_not_called()
    ctrl.settings.set.assert_not_called()


def test_restore_main_window_shows_and_activates_result_bar():
    from core.controller import CoreController

    ctrl = make_controller()

    CoreController._restore_main_window(ctrl)

    ctrl.result_bar.show.assert_called_once()
    ctrl.result_bar.raise_.assert_called_once()
    ctrl.result_bar.activateWindow.assert_called_once()


def test_tray_behavior_falls_back_to_quit_when_system_tray_unavailable():
    from core.controller import CoreController

    ctrl = make_controller()
    ctrl.settings.get.return_value = 'tray'
    ctrl._is_tray_available.return_value = False

    CoreController._handle_result_bar_close(ctrl)

    ctrl._warn_tray_unavailable.assert_called_once()
    ctrl.app.quit.assert_called_once()


def test_tray_menu_contains_show_main_action():
    from ui.tray import SystemTray

    tray = SystemTray()
    labels = [action.text() for action in tray.contextMenu().actions()]

    assert '显示主窗口' in labels


def test_settings_window_loads_and_saves_close_button_behavior():
    from ui.settings_window import SettingsWindow

    temp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    temp.close()
    store = SettingsStore(temp.name)
    store.set('close_button_behavior', 'tray')

    win = SettingsWindow(store)
    assert win._combo_close_behavior.currentData() == 'tray'

    idx = win._combo_close_behavior.findData('quit')
    win._combo_close_behavior.setCurrentIndex(idx)
    win._save()

    reloaded = SettingsStore(temp.name)
    assert reloaded.get('close_button_behavior') == 'quit'
