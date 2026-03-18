import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import json, tempfile, pytest
from PyQt5.QtWidgets import QApplication
from core.settings import SettingsStore

_app = QApplication.instance() or QApplication(sys.argv)

def make_store():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    return SettingsStore(f.name)

def test_default_values():
    store = make_store()
    assert store.get('temp_box_timeout') == 3
    assert store.get('auto_translate_interval') == 2
    assert store.get('target_language') == 'zh-CN'
    assert store.get('hotkey_select') == 'alt+q'
    assert store.get('hotkey_explain') == 'alt+e'
    assert isinstance(store.get('translation_order'), list)

def test_default_enabled_backends_include_bing():
    store = make_store()
    assert 'bing' in store.get('enabled_backends')

def test_set_and_persist():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('temp_box_timeout', 5)
    store2 = SettingsStore(f.name)
    assert store2.get('temp_box_timeout') == 5

def test_get_nonexistent_returns_default():
    store = make_store()
    assert store.get('nonexistent', 'fallback') == 'fallback'

def test_api_key():
    store = make_store()
    store.set_api_key('deepseek_key', 'sk-test123')
    assert store.get_api_key('deepseek_key') == 'sk-test123'

def test_default_close_button_behavior_is_ask():
    store = make_store()
    assert store.get('close_button_behavior') == 'ask'

def test_default_overlay_settings():
    store = make_store()
    assert store.get('overlay_default_mode') == 'off'
    assert store.get('overlay_font_delta') == 0

def test_close_button_behavior_persists():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('close_button_behavior', 'tray')
    store2 = SettingsStore(f.name)
    assert store2.get('close_button_behavior') == 'tray'

def test_overlay_settings_persist():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('overlay_default_mode', 'below')
    store.set('overlay_font_delta', 3)
    store2 = SettingsStore(f.name)
    assert store2.get('overlay_default_mode') == 'below'
    assert store2.get('overlay_font_delta') == 3

def test_para_split_defaults():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    s = SettingsStore(f.name)
    assert s.get('para_split_enabled') is True
    assert s.get('para_gap_ratio') == 0.5

def test_default_button_style_variant_is_calm():
    store = make_store()
    assert store.get('button_style_variant') == 'calm'

def test_button_style_variant_persists():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('button_style_variant', 'semantic')
    store2 = SettingsStore(f.name)
    assert store2.get('button_style_variant') == 'semantic'


def get_button_style_variant_buttons(win):
    buttons = getattr(win, '_button_style_variant_buttons', None)
    assert buttons is not None
    assert set(buttons.keys()) == {'calm', 'semantic'}
    return buttons


def test_settings_window_loads_saved_button_style_variant():
    from ui.settings_window import SettingsWindow

    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('button_style_variant', 'semantic')

    win = SettingsWindow(store)
    buttons = get_button_style_variant_buttons(win)

    assert buttons['semantic'].isChecked()
    assert not buttons['calm'].isChecked()


def test_settings_window_saves_button_style_variant():
    from ui.settings_window import SettingsWindow

    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)

    win = SettingsWindow(store)
    buttons = get_button_style_variant_buttons(win)
    buttons['semantic'].setChecked(True)
    win._save()

    reloaded = SettingsStore(f.name)
    assert reloaded.get('button_style_variant') == 'semantic'


def test_settings_window_reset_defaults_restores_calm_button_style_variant():
    from ui.settings_window import SettingsWindow

    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('button_style_variant', 'semantic')

    win = SettingsWindow(store)
    buttons = get_button_style_variant_buttons(win)
    assert buttons['semantic'].isChecked()

    win._reset_defaults()

    assert buttons['calm'].isChecked()
    assert not buttons['semantic'].isChecked()


def test_settings_window_skin_selector_contains_all_13_skins():
    """皮肤选择器必须包含 list_skins() 返回的全部 13 个皮肤 ID。"""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from ui.settings_window import SettingsWindow
    from ui.theme import list_skins

    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    win = SettingsWindow(store)

    expected = set(list_skins())
    actual = set(win._skin_cards.keys())
    assert actual == expected, f"缺少皮肤: {expected - actual}, 多余皮肤: {actual - expected}"


def test_skin_kawaii_persists():
    """保存 skin='kawaii' 后重新加载应返回 'kawaii'。"""
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    store = SettingsStore(f.name)
    store.set('skin', 'kawaii')
    store2 = SettingsStore(f.name)
    assert store2.get('skin') == 'kawaii'
