from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor, QFont


class SelectionOverlay(QWidget):
    selection_made = pyqtSignal(QRect)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._start = QPoint()
        self._end = QPoint()
        self._drawing = False
        self._setup_window()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setCursor(QCursor(Qt.CrossCursor))

    def show_overlay(self):
        self._drawing = False
        self._start = QPoint()
        self._end = QPoint()
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self._drawing = True

    def mouseMoveEvent(self, event):
        if self._drawing:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing:
            self._drawing = False
            self._end = event.pos()
            self.hide()
            rect = QRect(self._start, self._end).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.selection_made.emit(rect)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._drawing = False
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 50))

        if self._drawing and not self._start.isNull():
            rect = QRect(self._start, self._end).normalized()
            # 清除选区遮罩
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            # 红色虚线边框
            pen = QPen(QColor(255, 80, 80), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            # 尺寸提示
            font = QFont()
            font.setPixelSize(12)
            painter.setFont(font)
            painter.setPen(QColor(255, 80, 80))
            painter.drawText(rect.x() + 4, rect.y() - 6,
                             f'{rect.width()} × {rect.height()}')
