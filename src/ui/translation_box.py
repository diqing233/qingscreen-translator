from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QFont


class TranslationBox(QWidget):
    translate_requested = pyqtSignal(object)
    close_requested = pyqtSignal(object)
    mode_changed = pyqtSignal(object, str)

    MODE_TEMP = 'temp'
    MODE_FIXED = 'fixed'

    def __init__(self, rect: QRect, box_id: int, settings, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.region = rect
        self.settings = settings
        self.mode = self.MODE_TEMP
        self._drag_pos = QPoint()
        self._ocr_text = ''
        self._overlay_label = None

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(lambda: self.translate_requested.emit(self))

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_dismiss_timeout)

        self._setup_ui()
        self._setup_window(rect)

    def _setup_window(self, rect: QRect):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # Qt.Tool 窗口不是前台窗口，WA_AlwaysShowToolTips 让悬停时立即显示 tooltip
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.setMinimumSize(80, 50)
        self.setGeometry(rect)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # 控制按钮（悬停显示）
        self._btn_bar = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)

        self._btn_translate = self._make_btn('🔄', '立即翻译', lambda: self.translate_requested.emit(self))
        self._btn_pin = self._make_btn('📌', '固定/取消固定', self._on_toggle_pin)
        self._btn_hide = self._make_btn('👁', '隐藏', self.hide)
        self._btn_close = self._make_btn('✕', '关闭', lambda: self.close_requested.emit(self))

        for btn in [self._btn_translate, self._btn_pin, self._btn_hide, self._btn_close]:
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        self._btn_bar.setVisible(False)
        layout.addWidget(self._btn_bar)

        self._ocr_label = QLabel('')
        self._ocr_label.setStyleSheet('color: rgba(220,220,220,160); font-size: 10px;')
        self._ocr_label.setWordWrap(True)
        layout.addWidget(self._ocr_label)
        layout.addStretch()

    def _make_btn(self, icon, tooltip, callback):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(22, 22)
        btn.setStyleSheet('''
            QPushButton {
                background: rgba(30,30,40,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,100,220); }
        ''')
        btn.clicked.connect(callback)
        return btn

    def _on_toggle_pin(self):
        self.set_mode(self.MODE_FIXED if self.mode == self.MODE_TEMP else self.MODE_TEMP)

    def set_mode(self, mode: str):
        self.mode = mode
        self._btn_pin.setText('📍' if mode == self.MODE_FIXED else '📌')
        if mode == self.MODE_FIXED:
            self._dismiss_timer.stop()
        else:
            self._auto_timer.stop()
        self.mode_changed.emit(self, mode)
        self.update()

    def set_ocr_text(self, text: str):
        self._ocr_text = text
        short = (text[:35] + '…') if len(text) > 35 else text
        self._ocr_label.setText(short)

    def start_dismiss_timer(self):
        if self.mode == self.MODE_TEMP:
            ms = self.settings.get('temp_box_timeout', 3) * 1000
            self._dismiss_timer.start(ms)

    def start_auto_translate(self):
        ms = self.settings.get('auto_translate_interval', 2) * 1000
        self._auto_timer.start(ms)

    def stop_auto_translate(self):
        self._auto_timer.stop()

    def show_translation_overlay(self, text: str):
        """在框内用半透明遮罩覆盖原文区域，显示译文。"""
        if self._overlay_label is None:
            self._overlay_label = QLabel(self)
            self._overlay_label.setAlignment(Qt.AlignCenter)
            self._overlay_label.setWordWrap(True)
            self._overlay_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self._overlay_label.setStyleSheet('''
                QLabel {
                    background: rgba(15, 15, 20, 210);
                    color: #f0f0f0;
                    font-size: 13px;
                    padding: 8px;
                    border-radius: 4px;
                }
            ''')
        self._overlay_label.setText(text)
        self._overlay_label.setGeometry(0, 0, self.width(), self.height())
        self._overlay_label.raise_()
        self._overlay_label.show()

    def hide_translation_overlay(self):
        """隐藏覆盖译文遮罩。"""
        if self._overlay_label is not None:
            self._overlay_label.hide()

    def _on_dismiss_timeout(self):
        if self.mode == self.MODE_TEMP:
            self.close_requested.emit(self)

    def enterEvent(self, event):
        self._btn_bar.setVisible(True)

    def leaveEvent(self, event):
        self._btn_bar.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # alpha=4 让整个窗口接收鼠标事件（Windows 分层窗口中 alpha=0 区域为穿透）
        painter.fillRect(self.rect(), QColor(0, 0, 0, 4))
        border_color = QColor(80, 160, 255, 200) if self.mode == self.MODE_FIXED else QColor(220, 220, 255, 160)
        pen = QPen(border_color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
            self.region = QRect(new_pos.x(), new_pos.y(), self.width(), self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._overlay_label is not None and self._overlay_label.isVisible():
            self._overlay_label.setGeometry(0, 0, self.width(), self.height())
