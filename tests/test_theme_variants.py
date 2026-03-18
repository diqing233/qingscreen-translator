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
