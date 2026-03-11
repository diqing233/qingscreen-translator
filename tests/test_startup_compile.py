import pathlib
import py_compile

import pytest


RESULT_BAR_PATH = pathlib.Path(__file__).resolve().parents[1] / "src" / "ui" / "result_bar.py"


def test_result_bar_module_compiles():
    try:
        py_compile.compile(str(RESULT_BAR_PATH), doraise=True)
    except py_compile.PyCompileError as exc:
        pytest.fail(f"result_bar.py should compile without syntax errors: {exc.msg}")
