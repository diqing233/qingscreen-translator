import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    from core.controller import CoreController
    controller = CoreController(app)
    controller.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
