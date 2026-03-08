from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import pyqtSignal


class SystemTray(QSystemTrayIcon):
    select_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    history_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(self._make_icon())
        self.setToolTip('ScreenTranslator - 屏幕翻译')
        self._build_menu()
        self.activated.connect(self._on_activated)

    def _make_icon(self):
        px = QPixmap(16, 16)
        px.fill(QColor(70, 130, 240))
        return QIcon(px)

    def _build_menu(self):
        menu = QMenu()
        actions = [
            ('📷 框选翻译  Alt+Q', self.select_triggered),
            None,
            ('🕐 翻译历史', self.history_triggered),
            ('⚙ 设置', self.settings_triggered),
            None,
            ('退出', self.quit_triggered),
        ]
        for item in actions:
            if item is None:
                menu.addSeparator()
            else:
                label, sig = item
                act = QAction(label, menu)
                act.triggered.connect(sig.emit)
                menu.addAction(act)
        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.select_triggered.emit()
