import logging
import pathlib
import runpy
import sys
import types

import pytest


MAIN_PATH = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


def test_main_module_handles_locked_log_file(monkeypatch):
    fake_engine = types.ModuleType("ocr.engine")
    fake_engine.prewarm = lambda: None
    fake_ocr = types.ModuleType("ocr")
    fake_ocr.engine = fake_engine

    monkeypatch.setitem(sys.modules, "ocr", fake_ocr)
    monkeypatch.setitem(sys.modules, "ocr.engine", fake_engine)
    monkeypatch.setattr(logging, "FileHandler", lambda *args, **kwargs: (_ for _ in ()).throw(PermissionError("locked")))

    try:
        runpy.run_path(str(MAIN_PATH), run_name="screen_translator_main_test")
    except PermissionError as exc:
        pytest.fail(f"main.py should fall back when app.log is unavailable: {exc}")
