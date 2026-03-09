import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOG_DIR = os.path.expanduser('~/.screen_translator')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(LOG_DIR, 'app.log'), encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

# !! CRITICAL: onnxruntime must be loaded BEFORE any PyQt5 import.
# On Windows, Qt DLL initialization breaks onnxruntime (WinError 1114).
# ocr.engine has zero Qt imports – safe to import first.
from ocr.engine import prewarm
prewarm()

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# Must be set BEFORE QApplication is created, otherwise has no effect
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

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
