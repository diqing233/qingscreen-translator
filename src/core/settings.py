import json
import os
from typing import Any

DEFAULTS = {
    'temp_box_timeout': 3,
    'auto_translate_interval': 2,
    'target_language': 'zh-CN',
    'source_language': 'auto',
    'hotkey_select': 'alt+q',
    'hotkey_explain': 'alt+e',
    'hotkey_toggle_boxes': 'alt+w',
    'hotkey_mode_temp': 'alt+1',
    'hotkey_mode_fixed': 'alt+2',
    'hotkey_mode_multi': 'alt+3',
    'hotkey_mode_ai': 'alt+4',
    'result_bar_opacity': 0.85,
    'result_bar_position': 'right',
    'result_bar_size': 'default',
    'close_button_behavior': 'ask',
    'overlay_default_mode': 'off',
    'overlay_font_delta': 0,
    'para_split_enabled': True,
    'para_gap_ratio': 0.5,
    'skin': 'deep_space',
    'button_style_variant': 'calm',
    'translation_order': ['dictionary', 'bing', 'google', 'baidu', 'deepl', 'zhipu', 'siliconflow', 'moonshot', 'deepseek', 'openai', 'claude', 'sogou', 'youdao'],
    'enabled_backends': ['bing', 'google', 'zhipu'],
    'api_keys': {
        'baidu_appid': '',
        'baidu_key': '',
        'deepl_key': '',
        'zhipu_key': '',
        'siliconflow_key': '',
        'moonshot_key': '',
        'deepseek_key': '',
        'openai_key': '',
        'claude_key': '',
    }
}

class SettingsStore:
    def __init__(self, path: str = None):
        if path is None:
            app_dir = os.path.expanduser('~/.screen_translator')
            os.makedirs(app_dir, exist_ok=True)
            path = os.path.join(app_dir, 'settings.json')
        self._path = path
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def get_api_key(self, name: str) -> str:
        return self._data.get('api_keys', {}).get(name, '')

    def set_api_key(self, name: str, value: str):
        if 'api_keys' not in self._data:
            self._data['api_keys'] = {}
        self._data['api_keys'][name] = value
        self._save()
