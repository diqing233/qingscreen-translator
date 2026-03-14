import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import json, tempfile, pytest
from core.settings import SettingsStore

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

def test_default_enabled_backends_exclude_bing():
    store = make_store()
    assert 'bing' not in store.get('enabled_backends')

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
    import tempfile, os
    from core.settings import SettingsStore
    with tempfile.TemporaryDirectory() as d:
        s = SettingsStore(os.path.join(d, 'settings.json'))
        assert s.get('para_split_enabled') is True
        assert s.get('para_gap_ratio') == 0.5
