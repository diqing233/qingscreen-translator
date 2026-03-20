import sys
import os
import logging
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.expanduser('~/.screen_translator')
os.makedirs(LOG_DIR, exist_ok=True)

def _build_log_handlers():
    handlers = [logging.StreamHandler()]
    warnings = []
    primary_log_path = os.path.join(LOG_DIR, 'app.log')

    try:
        handlers.append(logging.FileHandler(primary_log_path, encoding='utf-8'))
        return handlers, warnings
    except OSError as exc:
        warnings.append(f'无法写入日志文件 {primary_log_path}，将尝试使用临时日志文件: {exc}')

    fallback_dir = os.path.join(tempfile.gettempdir(), 'screen_translator')
    fallback_log_path = os.path.join(fallback_dir, f'app-{os.getpid()}.log')
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        handlers.append(logging.FileHandler(fallback_log_path, encoding='utf-8'))
        warnings.append(f'已切换到临时日志文件: {fallback_log_path}')
    except OSError as exc:
        warnings.append(f'临时日志文件也不可用，将只输出到控制台: {exc}')

    return handlers, warnings


_handlers, _startup_log_warnings = _build_log_handlers()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=_handlers,
)
logger = logging.getLogger(__name__)
for _warning in _startup_log_warnings:
    logger.warning(_warning)

# !! CRITICAL: onnxruntime must be loaded BEFORE any PyQt5 import.
# On Windows, Qt DLL initialization breaks onnxruntime (WinError 1114).
# ocr.engine has zero Qt imports – safe to import first.
from ocr.engine import prewarm
prewarm()

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase

# Must be set BEFORE QApplication is created, otherwise has no effect
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# PyInstaller 兼容：frozen 时资源在 sys._MEIPASS，开发时在项目根目录
_BASE_DIR = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
_FONTS_DIR = os.path.join(_BASE_DIR, 'assets', 'fonts')

def _register_fonts():
    """Register bundled font files with Qt's font database."""
    font_files = [
        'JetBrainsMono-Regular.ttf',
        'Nunito-Regular.ttf',
        'Orbitron-Regular.ttf',
        'Phosphor.ttf',
        'Phosphor-Light.ttf',
        'Phosphor-Bold.ttf',
    ]
    for fname in font_files:
        path = os.path.normpath(os.path.join(_FONTS_DIR, fname))
        if os.path.exists(path):
            fid = QFontDatabase.addApplicationFont(path)
            if fid < 0:
                logger.warning('字体注册失败: %s', path)
        else:
            logger.warning('字体文件不存在: %s', path)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    _register_fonts()

    try:
        from core.controller import CoreController
        controller = CoreController(app)
        controller.start()
    except Exception as e:
        logger.exception('启动失败')
        QMessageBox.critical(None, '启动错误', f'ScreenTranslator 启动失败:\n{e}')
        sys.exit(1)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
