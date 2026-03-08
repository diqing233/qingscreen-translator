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

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

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
