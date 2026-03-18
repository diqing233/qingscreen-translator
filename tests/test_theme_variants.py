import inspect
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui import theme


def get_composed_skin(name: str, button_style_variant: str):
    signature = inspect.signature(theme.get_skin)
    if 'button_style_variant' not in signature.parameters:
        pytest.fail('get_skin should accept a button_style_variant parameter')
    return theme.get_skin(name, button_style_variant=button_style_variant)


def test_button_style_variants_keep_base_skin_tokens():
    semantic = get_composed_skin('rose', 'semantic')

    assert semantic['bg_rgb'] == theme.SKINS['rose']['bg_rgb']
    assert semantic['text'] == theme.SKINS['rose']['text']
    assert semantic['swatch'] == theme.SKINS['rose']['swatch']


def test_button_style_variants_override_button_tokens_without_mutating_base_skin():
    original_primary = theme.SKINS['deep_space']['btn_primary_bg']
    calm = get_composed_skin('deep_space', 'calm')
    semantic = get_composed_skin('deep_space', 'semantic')

    assert calm['btn_primary_bg'] != semantic['btn_primary_bg']
    assert theme.SKINS['deep_space']['btn_primary_bg'] == original_primary


def test_unknown_button_style_variant_falls_back_to_calm():
    calm = get_composed_skin('matrix', 'calm')
    fallback = get_composed_skin('matrix', 'unknown-variant')

    assert fallback == calm


def test_minimal_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('minimal')

    assert skin['dark'] == False
    assert skin['bg_rgb'] == (248, 249, 250)
    assert '26,26,46' in skin['btn_primary_bg']


def test_coral_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('coral')

    assert skin['dark'] == False
    assert skin['bg_rgb'] == (255, 245, 230)
    assert '232,96,26' in skin['btn_primary_bg']


def test_minimal_in_list_skins():
    assert 'minimal' in theme.list_skins()


def test_coral_in_list_skins():
    assert 'coral' in theme.list_skins()


def test_forest_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('forest')

    assert skin['dark'] == True
    assert skin['bg_rgb'] == (26, 46, 26)
    assert '76,175,80' in skin['btn_primary_bg']


def test_retro_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('retro')

    assert skin['dark'] == True
    assert skin['bg_rgb'] == (42, 26, 8)
    assert '200,134,10' in skin['btn_primary_bg']


def test_forest_in_list_skins():
    assert 'forest' in theme.list_skins()


def test_retro_in_list_skins():
    assert 'retro' in theme.list_skins()


def test_cyberpunk_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('cyberpunk')

    assert skin['dark'] == True
    assert skin['bg_rgb'] == (10, 0, 24)
    assert skin['text'] == '#ff00ff'


def test_ink_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('ink')

    assert skin['dark'] == False
    assert skin['bg_rgb'] == (245, 240, 232)
    assert skin['text'] == '#2c1a00'


def test_mint_skin_exists_and_has_correct_tokens():
    skin = theme.get_skin('mint')

    assert skin['dark'] == False
    assert skin['bg_rgb'] == (232, 250, 244)
    assert '0,137,123' in skin['btn_primary_bg']


def test_cyberpunk_in_list_skins():
    assert 'cyberpunk' in theme.list_skins()


def test_ink_in_list_skins():
    assert 'ink' in theme.list_skins()


def test_mint_in_list_skins():
    assert 'mint' in theme.list_skins()
