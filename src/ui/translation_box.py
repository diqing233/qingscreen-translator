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
        self._subtitle_win = None
        self._subtitle_active = False
        self._last_translation = ''

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
        self._btn_subtitle = self._make_btn('⊞', '在框下方显示译文字幕', self._on_toggle_subtitle)
        self._btn_hide = self._make_btn('👁', '隐藏', self.hide)
        self._btn_close = self._make_btn('✕', '关闭', lambda: self.close_requested.emit(self))

        for btn in [self._btn_translate, self._btn_pin, self._btn_subtitle,
                    self._btn_hide, self._btn_close]:
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

    def _create_subtitle_win(self):
        win = QLabel()
        win.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        win.setAttribute(Qt.WA_TranslucentBackground)
        win.setWordWrap(True)
        win.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        win.setStyleSheet('''
            QLabel {
                background: rgba(15, 15, 24, 210);
                color: #f0f0f0;
                font-size: 13px;
                padding: 6px 12px;
                border-top: 1px solid rgba(80, 140, 255, 100);
                border-radius: 0px 0px 6px 6px;
            }
        ''')
        return win

    def _subtitle_geometry(self):
        """计算字幕窗口应在的位置（box 正下方，同宽）"""
        return (self.x(), self.y() + self.height(), self.width())

    def show_subtitle(self, text: str):
        """在框正下方显示译文字幕条。"""
        self._last_translation = text
        if self._subtitle_win is None:
            self._subtitle_win = self._create_subtitle_win()
        self._subtitle_win.setText(text)
        x, y, w = self._subtitle_geometry()
        self._subtitle_win.setFixedWidth(w)
        self._subtitle_win.adjustSize()
        self._subtitle_win.move(x, y)
        self._subtitle_win.show()
        self._subtitle_win.raise_()
        self._subtitle_active = True
        self._btn_subtitle.setStyleSheet('''
            QPushButton {
                background: rgba(80,140,255,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(100,160,255,200); }
        ''')

    def hide_subtitle(self):
        """隐藏译文字幕条。"""
        if self._subtitle_win is not None:
            self._subtitle_win.hide()
        self._subtitle_active = False
        self._btn_subtitle.setStyleSheet('''
            QPushButton {
                background: rgba(30,30,40,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,100,220); }
        ''')

    def _on_toggle_subtitle(self):
        if self._subtitle_active:
            self.hide_subtitle()
        elif self._last_translation:
            self.show_subtitle(self._last_translation)

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

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._subtitle_win is not None and self._subtitle_win.isVisible():
            x, y, w = self._subtitle_geometry()
            self._subtitle_win.move(x, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._subtitle_win is not None and self._subtitle_win.isVisible():
            x, y, w = self._subtitle_geometry()
            self._subtitle_win.setFixedWidth(w)
            self._subtitle_win.adjustSize()
            self._subtitle_win.move(x, y)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._subtitle_win is not None:
            self._subtitle_win.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self._subtitle_active and self._subtitle_win is not None:
            self._subtitle_win.show()

    def closeEvent(self, event):
        if self._subtitle_win is not None:
            self._subtitle_win.close()
            self._subtitle_win = None
        super().closeEvent(event)
