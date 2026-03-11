from PyQt5.QtCore import QPoint, QRect, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class TranslationBox(QWidget):
    translate_requested = pyqtSignal(object)
    close_requested = pyqtSignal(object)
    mode_changed = pyqtSignal(object, str)

    MODE_TEMP = 'temp'
    MODE_FIXED = 'fixed'

    OVERLAY_OFF = 'off'
    OVERLAY_OVER = 'over'
    OVERLAY_BELOW = 'below'
    OVERLAY_CYCLE = [OVERLAY_OVER, OVERLAY_BELOW, OVERLAY_OFF]

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
        self._subtitle_mode = self._normalize_overlay_mode(
            self.settings.get('overlay_default_mode', self.OVERLAY_OFF)
        )
        self._last_translation = ''

        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(lambda: self.translate_requested.emit(self))

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_dismiss_timeout)

        self._setup_ui()
        self._setup_window(rect)
        self._update_subtitle_button()

    def _setup_window(self, rect: QRect):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.setMinimumSize(80, 50)
        self.setGeometry(rect)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        self._btn_bar = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)

        self._btn_translate = self._make_btn('译', '立即翻译', lambda: self.translate_requested.emit(self))
        self._btn_pin = self._make_btn('📌', '固定/取消固定', self._on_toggle_pin)
        self._btn_subtitle = self._make_btn('⊞', '覆盖翻译', self._on_toggle_subtitle)
        self._btn_hide = self._make_btn('隐', '隐藏', self.hide)
        self._btn_close = self._make_btn('✕', '关闭', lambda: self.close_requested.emit(self))

        for btn in [self._btn_translate, self._btn_pin, self._btn_subtitle, self._btn_hide, self._btn_close]:
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

    def _normalize_overlay_mode(self, mode: str) -> str:
        if mode in {self.OVERLAY_OFF, self.OVERLAY_OVER, self.OVERLAY_BELOW}:
            return mode
        return self.OVERLAY_OFF

    def _current_overlay_font_size(self) -> int:
        base = max(12, min(36, int(self.height() * 0.32)))
        delta = int(self.settings.get('overlay_font_delta', 0))
        return max(10, min(48, base + delta))

    def _create_subtitle_win(self):
        win = QLabel()
        win.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        win.setAttribute(Qt.WA_TranslucentBackground)
        win.setWordWrap(True)
        return win

    def _overlay_rect(self) -> QRect:
        if self._subtitle_mode == self.OVERLAY_OVER:
            return QRect(self.x(), self.y(), self.width(), self.height())
        return QRect(self.x(), self.y() + self.height(), self.width(), 0)

    def _apply_subtitle_style(self):
        if self._subtitle_win is None:
            return

        font = self._subtitle_win.font()
        font.setPixelSize(self._current_overlay_font_size())
        self._subtitle_win.setFont(font)

        if self._subtitle_mode == self.OVERLAY_OVER:
            self._subtitle_win.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self._subtitle_win.setStyleSheet('''
                QLabel {
                    background: rgba(12, 12, 18, 170);
                    color: #f0f0f0;
                    padding: 4px 6px;
                    border: 1px solid rgba(80, 140, 255, 70);
                    border-radius: 4px;
                }
            ''')
        else:
            self._subtitle_win.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._subtitle_win.setStyleSheet('''
                QLabel {
                    background: rgba(15, 15, 24, 210);
                    color: #f0f0f0;
                    padding: 6px 12px;
                    border-top: 1px solid rgba(80, 140, 255, 100);
                    border-radius: 0px 0px 6px 6px;
                }
            ''')

    def _layout_subtitle(self):
        if self._subtitle_win is None:
            return

        rect = self._overlay_rect()
        if self._subtitle_mode == self.OVERLAY_OVER:
            self._subtitle_win.setMinimumSize(rect.width(), rect.height())
            self._subtitle_win.setMaximumSize(rect.width(), rect.height())
            self._subtitle_win.resize(rect.width(), rect.height())
            self._subtitle_win.move(rect.x(), rect.y())
            return

        self._subtitle_win.setMinimumSize(0, 0)
        self._subtitle_win.setMaximumSize(16777215, 16777215)
        self._subtitle_win.setFixedWidth(rect.width())
        self._subtitle_win.adjustSize()
        self._subtitle_win.move(rect.x(), rect.y())

    def _update_subtitle_button(self):
        next_mode = self.OVERLAY_CYCLE[0]
        if self._subtitle_mode == self.OVERLAY_OVER:
            next_mode = self.OVERLAY_BELOW
        elif self._subtitle_mode == self.OVERLAY_BELOW:
            next_mode = self.OVERLAY_OFF

        tips = {
            self.OVERLAY_OFF: '覆盖翻译：关闭，点击切到原文上',
            self.OVERLAY_OVER: '覆盖翻译：原文上，点击切到原文下方',
            self.OVERLAY_BELOW: '覆盖翻译：原文下方，点击关闭',
        }
        self._btn_subtitle.setToolTip(tips[self._subtitle_mode])

        if self._subtitle_mode == self.OVERLAY_OFF:
            self._btn_subtitle.setStyleSheet('''
                QPushButton {
                    background: rgba(30,30,40,180); color: white;
                    border: none; border-radius: 3px; font-size: 11px;
                }
                QPushButton:hover { background: rgba(70,70,100,220); }
            ''')
            return

        self._btn_subtitle.setStyleSheet('''
            QPushButton {
                background: rgba(80,140,255,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(100,160,255,200); }
        ''')

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

    def set_overlay_mode(self, mode: str):
        self._subtitle_mode = self._normalize_overlay_mode(mode)
        if self._subtitle_mode == self.OVERLAY_OFF:
            self.hide_subtitle()
        else:
            self._update_subtitle_button()
            if self._subtitle_active and self._last_translation:
                self.show_subtitle(self._last_translation)

    def refresh_overlay_style(self):
        if self._subtitle_win is None:
            return
        self._apply_subtitle_style()
        if self._subtitle_active:
            self._layout_subtitle()

    def set_ocr_text(self, text: str):
        self._ocr_text = text
        short = (text[:35] + '...') if len(text) > 35 else text
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

    def show_subtitle(self, text: str):
        self._last_translation = text
        if self._subtitle_mode == self.OVERLAY_OFF:
            return
        if self._subtitle_win is None:
            self._subtitle_win = self._create_subtitle_win()
        self._subtitle_win.setText(text)
        self._apply_subtitle_style()
        self._layout_subtitle()
        self._subtitle_win.show()
        self._subtitle_win.raise_()
        self._subtitle_active = True
        self._update_subtitle_button()

    def hide_subtitle(self):
        if self._subtitle_win is not None:
            self._subtitle_win.hide()
        self._subtitle_active = False
        self._update_subtitle_button()

    def _on_toggle_subtitle(self):
        try:
            index = self.OVERLAY_CYCLE.index(self._subtitle_mode)
        except ValueError:
            index = len(self.OVERLAY_CYCLE) - 1
        self.set_overlay_mode(self.OVERLAY_CYCLE[(index + 1) % len(self.OVERLAY_CYCLE)])
        if self._subtitle_mode != self.OVERLAY_OFF and self._last_translation:
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
        if self._subtitle_win is not None and self._subtitle_active:
            self._layout_subtitle()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._subtitle_win is not None and self._subtitle_active:
            self.refresh_overlay_style()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._subtitle_win is not None:
            self._subtitle_win.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self._subtitle_active and self._subtitle_win is not None:
            self._layout_subtitle()
            self._subtitle_win.show()

    def closeEvent(self, event):
        if self._subtitle_win is not None:
            self._subtitle_win.close()
            self._subtitle_win = None
        super().closeEvent(event)
