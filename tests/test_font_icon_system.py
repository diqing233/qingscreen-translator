"""Tests for font + icon system (FONT_SETS, ICON_SETS, campus skin, settings)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui import theme


# ── FONT_SETS ──────────────────────────────────────────────────────

def test_font_sets_exist():
    assert hasattr(theme, 'FONT_SETS')
    assert set(theme.FONT_SETS.keys()) == {'sans', 'mono', 'rounded', 'serif', 'display'}


def test_font_set_has_required_tokens():
    required = {
        'font_family', 'font_size_translation', 'font_size_ui',
        'font_size_small', 'font_weight_translation', 'font_weight_ui',
    }
    for name, fs in theme.FONT_SETS.items():
        missing = required - set(fs.keys())
        assert not missing, f'font_set {name!r} missing tokens: {missing}'


def test_font_set_composition_adds_tokens():
    skin = theme.get_skin('deep_space', font_set='mono')
    assert 'font_family' in skin
    assert 'JetBrains Mono' in skin['font_family']


def test_font_set_override_does_not_mutate_base_skin():
    original = dict(theme.SKINS['deep_space'])
    theme.get_skin('deep_space', font_set='display')
    assert theme.SKINS['deep_space'] == original


# ── ICON_SETS ──────────────────────────────────────────────────────

def test_icon_sets_exist():
    assert hasattr(theme, 'ICON_SETS')
    assert set(theme.ICON_SETS.keys()) == {'phosphor-light', 'phosphor-regular', 'phosphor-bold'}


def test_icon_set_has_required_tokens():
    required = {
        'icon_font', 'icon_weight', 'icon_size_toolbar', 'icon_size_action',
        'icon_copy', 'icon_close', 'icon_translate', 'icon_ai',
        'icon_pin', 'icon_unpin', 'icon_expand', 'icon_collapse',
        'icon_font_up', 'icon_font_down', 'icon_settings', 'icon_history',
    }
    for name, ic in theme.ICON_SETS.items():
        missing = required - set(ic.keys())
        assert not missing, f'icon_set {name!r} missing tokens: {missing}'


def test_icon_set_composition_adds_tokens():
    skin = theme.get_skin('matrix', icon_set='phosphor-bold')
    assert skin['icon_font'] == 'Phosphor-Bold'
    assert skin['icon_weight'] == 'bold'
    assert 'icon_copy' in skin


def test_icon_set_codepoints_are_nonempty():
    for name, ic in theme.ICON_SETS.items():
        for key in ('icon_copy', 'icon_close', 'icon_pin', 'icon_settings'):
            assert ic[key], f'icon_set {name!r} has empty codepoint for {key!r}'


# ── campus 皮肤 ────────────────────────────────────────────────────

def test_campus_skin_exists():
    assert 'campus' in theme.SKINS
    assert 'campus' in theme.list_skins()


def test_campus_skin_tokens():
    skin = theme.get_skin('campus')
    assert skin['dark'] == False
    assert skin['bg_rgb'] == (240, 248, 255)
    assert '80,144,240' in skin['btn_primary_bg']
    assert skin['swatch'] == ('#f0f8ff', '#5090f0', '#ffb43c')


def test_campus_skin_has_63_color_tokens():
    """campus 皮肤应包含与 coral 相同数量的颜色 token。"""
    coral_keys = set(theme.SKINS['coral'].keys()) - {'default_font_set', 'default_icon_set'}
    campus_keys = set(theme.SKINS['campus'].keys()) - {'default_font_set', 'default_icon_set'}
    assert coral_keys == campus_keys


# ── 皮肤默认字体/图标集 ────────────────────────────────────────────

def test_all_skins_have_default_font_set():
    for sid in theme.list_skins():
        assert 'default_font_set' in theme.SKINS[sid], f'{sid} missing default_font_set'
        assert theme.SKINS[sid]['default_font_set'] in theme.FONT_SETS


def test_all_skins_have_default_icon_set():
    for sid in theme.list_skins():
        assert 'default_icon_set' in theme.SKINS[sid], f'{sid} missing default_icon_set'
        assert theme.SKINS[sid]['default_icon_set'] in theme.ICON_SETS


def test_skin_default_font_set_mapping():
    assert theme.SKINS['matrix']['default_font_set'] == 'mono'
    assert theme.SKINS['kawaii']['default_font_set'] == 'rounded'
    assert theme.SKINS['cyberpunk']['default_font_set'] == 'display'
    assert theme.SKINS['ink']['default_font_set'] == 'serif'
    assert theme.SKINS['deep_space']['default_font_set'] == 'sans'


def test_skin_default_icon_set_mapping():
    assert theme.SKINS['ink']['default_icon_set'] == 'phosphor-light'
    assert theme.SKINS['minimal']['default_icon_set'] == 'phosphor-light'
    assert theme.SKINS['matrix']['default_icon_set'] == 'phosphor-bold'
    assert theme.SKINS['deep_space']['default_icon_set'] == 'phosphor-regular'


# ── get_skin() 四层组合 ────────────────────────────────────────────

def test_get_skin_layer_order():
    """icon_set 层应覆盖 font_set 层，button_style_variant 层最后。"""
    skin = theme.get_skin('deep_space', 'calm', font_set='mono', icon_set='phosphor-bold')
    assert 'JetBrains Mono' in skin['font_family']
    assert skin['icon_font'] == 'Phosphor-Bold'
    assert skin['button_style_variant'] == 'calm'


def test_get_skin_font_set_none_uses_skin_default():
    skin = theme.get_skin('matrix', font_set=None)
    assert 'JetBrains Mono' in skin['font_family']


def test_get_skin_icon_set_none_uses_skin_default():
    skin = theme.get_skin('ink', icon_set=None)
    assert skin['icon_font'] == 'Phosphor-Light'


def test_get_skin_does_not_mutate_skins_dict():
    original_text = theme.SKINS['rose']['text']
    theme.get_skin('rose', 'semantic', font_set='display', icon_set='phosphor-bold')
    assert theme.SKINS['rose']['text'] == original_text


# ── settings 序列化 ────────────────────────────────────────────────

def test_settings_defaults_include_font_and_icon_set():
    from core.settings import DEFAULTS
    assert 'font_set' in DEFAULTS
    assert 'icon_set' in DEFAULTS
    assert DEFAULTS['font_set'] is None
    assert DEFAULTS['icon_set'] is None


def test_result_bar_skin_has_font_tokens():
    """所有皮肤的 font_family 和 font_size_translation 必须存在且类型正确。"""
    for sid in theme.list_skins():
        skin = theme.get_skin(sid)
        assert 'font_family' in skin
        assert 'font_size_translation' in skin
        assert isinstance(skin['font_size_translation'], int)


def test_icon_codepoints_are_nonempty_strings():
    """所有图标 codepoint 必须是非空字符串。"""
    icon_codepoint_keys = [
        'icon_copy', 'icon_close', 'icon_translate', 'icon_ai',
        'icon_pin', 'icon_unpin', 'icon_expand', 'icon_collapse',
        'icon_font_up', 'icon_font_down', 'icon_settings', 'icon_history',
        'icon_paragraph', 'icon_broom', 'icon_square',
    ]
    for set_name, ic in theme.ICON_SETS.items():
        for key in icon_codepoint_keys:
            val = ic.get(key, '')
            assert isinstance(val, str) and len(val) > 0, \
                f"ICON_SETS['{set_name}']['{key}'] is empty"


def test_font_family_strings_are_nonempty():
    """所有字体集的 font_family 必须是非空字符串。"""
    for name, fs in theme.FONT_SETS.items():
        assert isinstance(fs['font_family'], str)
        assert len(fs['font_family']) > 0
