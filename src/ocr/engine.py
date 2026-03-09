"""RapidOCR singleton – zero PyQt5 imports.

This module must be imported and prewarm() called BEFORE any PyQt5 module
is imported. On Windows, loading Qt DLLs first causes onnxruntime's
pybind11 DLL to fail initialization (WinError 1114).
"""
import logging

logger = logging.getLogger(__name__)

_engine = None


def prewarm():
    """Initialize RapidOCR engine in the main thread, before Qt is loaded."""
    global _engine
    try:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
        logger.info('RapidOCR 引擎预热完成')
    except Exception as e:
        logger.warning(f'RapidOCR 预热失败，将不可用: {e}')


def get_engine():
    return _engine
