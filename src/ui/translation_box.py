from PyQt5.QtCore import QPoint, QRect, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class TranslationBox(QWidget):
    translate_requested = pyqtSignal(object)
    close_requested = pyqtSignal(object)
    mode_changed = pyqtSignal(object, str)
    overlay_mode_changed = pyqtSignal(object, str)
    overlay_font_delta_changed = pyqtSignal(int)

    MODE_TEMP = "temp"
    MODE_FIXED = "fixed"

    OVERLAY_OFF = "off"
    OVERLAY_OVER = "over"
    OVERLAY_BELOW = "below"
    OVERLAY_CYCLE = [OVERLAY_OVER, OVERLAY_BELOW, OVERLAY_OFF]

    def __init__(self, rect: QRect, box_id: int, settings, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.region = rect
        self.settings = settings
        self.mode = self.MODE_TEMP
        self._drag_pos = QPoint()
        self._ocr_text = ""
        self._subtitle_win = None
        self._subtitle_paragraph_wins = []
        self._subtitle_active = False
        self._subtitle_mode = self._normalize_overlay_mode(
            self.settings.get("overlay_default_mode", self.OVERLAY_OFF)
        )
        self._last_translation = ""
        self._last_ocr_rows = []
        self._last_ocr_paragraphs = []
        self._last_paragraph_translations = []
        self._paragraph_translation_pending = False
        self._pending_paragraph_translations = []

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

        self._btn_translate = self._make_btn("译", "立即翻译", lambda: self.translate_requested.emit(self))
        self._btn_pin = self._make_btn("钉", "固定/取消固定", self._on_toggle_pin)
        self._btn_subtitle = self._make_btn("⊞", "覆盖翻译", self._on_toggle_subtitle)
        self._btn_overlay_font_down = self._make_btn(
            "A-",
            "减小覆盖译文字号",
            lambda: self._adjust_overlay_font_delta(-1),
            width=24,
        )
        self._btn_overlay_font_up = self._make_btn(
            "A+",
            "增大覆盖译文字号",
            lambda: self._adjust_overlay_font_delta(1),
            width=24,
        )
        self._btn_hide = self._make_btn("隐", "隐藏", self.hide)
        self._btn_close = self._make_btn("✕", "关闭", lambda: self.close_requested.emit(self))

        for btn in [
            self._btn_translate,
            self._btn_pin,
            self._btn_subtitle,
            self._btn_overlay_font_down,
            self._btn_overlay_font_up,
            self._btn_hide,
            self._btn_close,
        ]:
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        self._btn_bar.setVisible(False)
        layout.addWidget(self._btn_bar)

        self._ocr_label = QLabel("")
        self._ocr_label.setStyleSheet("color: rgba(220,220,220,160); font-size: 10px;")
        self._ocr_label.setWordWrap(True)
        layout.addWidget(self._ocr_label)
        layout.addStretch()

    def _make_btn(self, label, tooltip, callback, width=22):
        btn = QPushButton(label)
        btn.setToolTip(tooltip)
        btn.setFixedSize(width, 22)
        btn.setStyleSheet(
            """
            QPushButton {
                background: rgba(30,30,40,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,100,220); }
            """
        )
        btn.clicked.connect(callback)
        return btn

    def _normalize_overlay_mode(self, mode: str) -> str:
        if mode in {self.OVERLAY_OFF, self.OVERLAY_OVER, self.OVERLAY_BELOW}:
            return mode
        return self.OVERLAY_OFF

    def _current_overlay_font_size(self) -> int:
        base = max(12, min(18, int(self.height() * 0.18)))
        delta = int(self.settings.get("overlay_font_delta", 0))
        return max(10, min(28, base + delta))

    def _create_subtitle_win(self):
        win = QLabel()
        win.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        win.setAttribute(Qt.WA_TranslucentBackground)
        win.setWordWrap(True)
        return win

    def _ensure_single_subtitle_win(self):
        if self._subtitle_win is None:
            self._subtitle_win = self._create_subtitle_win()
        return self._subtitle_win

    def _sync_paragraph_subtitle_wins(self, target_count: int):
        while len(self._subtitle_paragraph_wins) < target_count:
            self._subtitle_paragraph_wins.append(self._create_subtitle_win())
        while len(self._subtitle_paragraph_wins) > target_count:
            win = self._subtitle_paragraph_wins.pop()
            win.close()

    def _all_subtitle_wins(self):
        wins = []
        if self._subtitle_win is not None:
            wins.append(self._subtitle_win)
        wins.extend(self._subtitle_paragraph_wins)
        return wins

    def _apply_font(self, win):
        font = win.font()
        font.setPixelSize(self._current_overlay_font_size())
        font.setBold(False)
        win.setFont(font)

    def _apply_single_subtitle_style(self):
        win = self._ensure_single_subtitle_win()
        self._apply_font(win)
        if self._subtitle_mode == self.OVERLAY_OVER:
            win.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            win.setStyleSheet(
                """
                QLabel {
                    background: rgba(6, 10, 16, 244);
                    color: rgb(240, 248, 255);
                    padding: 6px 10px 7px 10px;
                    border: 1px solid rgba(150, 190, 235, 110);
                    border-radius: 2px;
                }
                """
            )
            return

        win.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        win.setStyleSheet(
            """
            QLabel {
                background: rgba(6, 10, 16, 232);
                color: #f0f0f0;
                padding: 6px 12px;
                border: 1px solid rgba(120, 165, 230, 90);
                border-radius: 0px 0px 6px 6px;
            }
            """
        )

    def _apply_paragraph_subtitle_style(self, win):
        self._apply_font(win)
        win.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        win.setStyleSheet(
            """
            QLabel {
                background: rgba(6, 10, 16, 244);
                color: rgb(240, 248, 255);
                padding: 6px 10px 7px 10px;
                border: 1px solid rgba(150, 190, 235, 110);
                border-radius: 2px;
            }
            """
        )

    def _below_overlay_rect(self) -> QRect:
        return QRect(self.x(), self.y() + self.height(), self.width(), 0)

    def _over_fallback_bounds(self) -> QRect:
        left = 2
        top = 28
        right = 2
        bottom = 8
        return QRect(
            self.x() + left,
            self.y() + top,
            max(60, self.width() - left - right),
            max(20, self.height() - top - bottom),
        )

    def _paragraph_overlay_rect(self, paragraph):
        rect = paragraph.get("rect", {})
        x = self.x() + max(0, int(rect.get("x", 0)))
        y = self.y() + max(0, int(rect.get("y", 0)))
        width = max(80, int(rect.get("width", 0)))
        max_width = max(80, self.x() + self.width() - x)
        width = min(width, max_width)
        return QRect(x, y, width, max(20, int(rect.get("height", 0))))

    def _can_render_paragraph_subtitles(self) -> bool:
        return (
            self._subtitle_mode == self.OVERLAY_OVER
            and bool(self._last_ocr_paragraphs)
            and len(self._last_ocr_paragraphs) == len(self._last_paragraph_translations)
            and all(self._last_paragraph_translations)
        )

    def _layout_single_subtitle(self):
        win = self._ensure_single_subtitle_win()
        if self._subtitle_mode == self.OVERLAY_OVER:
            bounds = self._over_fallback_bounds()
            win.setMinimumSize(0, 0)
            win.setMaximumSize(bounds.width(), bounds.height())
            win.setFixedWidth(bounds.width())
            win.adjustSize()
            height = min(max(24, win.sizeHint().height()), bounds.height())
            win.resize(bounds.width(), height)
            win.move(bounds.x(), bounds.y())
            return

        rect = self._below_overlay_rect()
        win.setMinimumSize(0, 0)
        win.setMaximumSize(16777215, 16777215)
        win.setFixedWidth(rect.width())
        win.adjustSize()
        win.move(rect.x(), rect.y())

    def _layout_paragraph_subtitles(self):
        self._sync_paragraph_subtitle_wins(len(self._last_ocr_paragraphs))
        for paragraph, translated, win in zip(
            self._last_ocr_paragraphs,
            self._last_paragraph_translations,
            self._subtitle_paragraph_wins,
        ):
            self._apply_paragraph_subtitle_style(win)
            win.setText(translated)
            rect = self._paragraph_overlay_rect(paragraph)
            win.setMinimumSize(0, 0)
            win.setMaximumSize(rect.width(), self.height())
            win.setFixedWidth(rect.width())
            win.adjustSize()
            height = min(max(24, win.sizeHint().height()), self.height())
            win.resize(rect.width(), height)
            win.move(rect.x(), rect.y())

    def _show_single_subtitle(self, text: str):
        self._sync_paragraph_subtitle_wins(0)
        for win in self._subtitle_paragraph_wins:
            win.hide()
        win = self._ensure_single_subtitle_win()
        win.setText(text)
        self._apply_single_subtitle_style()
        self._layout_single_subtitle()
        win.show()
        win.raise_()

    def _show_paragraph_subtitles(self):
        if self._subtitle_win is not None:
            self._subtitle_win.hide()
        self._layout_paragraph_subtitles()
        for win in self._subtitle_paragraph_wins:
            win.show()
            win.raise_()

    def _hide_all_subtitles(self):
        for win in self._all_subtitle_wins():
            win.hide()

    def _close_all_subtitles(self):
        if self._subtitle_win is not None:
            self._subtitle_win.close()
            self._subtitle_win = None
        for win in self._subtitle_paragraph_wins:
            win.close()
        self._subtitle_paragraph_wins = []

    def _layout_subtitles(self):
        if self._subtitle_mode == self.OVERLAY_OVER and self._can_render_paragraph_subtitles():
            self._show_paragraph_subtitles()
            return
        if self._last_translation:
            self._show_single_subtitle(self._last_translation)

    def _update_subtitle_button(self):
        tips = {
            self.OVERLAY_OFF: "覆盖翻译：关闭，点击切到原文上",
            self.OVERLAY_OVER: "覆盖翻译：原文上，点击切到原文下方",
            self.OVERLAY_BELOW: "覆盖翻译：原文下方，点击关闭",
        }
        self._btn_subtitle.setToolTip(tips[self._subtitle_mode])

        if self._subtitle_mode == self.OVERLAY_OFF:
            self._btn_subtitle.setStyleSheet(
                """
                QPushButton {
                    background: rgba(30,30,40,180); color: white;
                    border: none; border-radius: 3px; font-size: 11px;
                }
                QPushButton:hover { background: rgba(70,70,100,220); }
                """
            )
            return

        self._btn_subtitle.setStyleSheet(
            """
            QPushButton {
                background: rgba(80,140,255,180); color: white;
                border: none; border-radius: 3px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(100,160,255,200); }
            """
        )

    def _on_toggle_pin(self):
        self.set_mode(self.MODE_FIXED if self.mode == self.MODE_TEMP else self.MODE_TEMP)

    def set_mode(self, mode: str):
        self.mode = mode
        self._btn_pin.setText("📍" if mode == self.MODE_FIXED else "钉")
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
            self.overlay_mode_changed.emit(self, self._subtitle_mode)
            return

        self._update_subtitle_button()
        self.overlay_mode_changed.emit(self, self._subtitle_mode)
        if self._subtitle_active and self._last_translation:
            self.show_subtitle(self._last_translation)

    def refresh_overlay_style(self):
        if self._subtitle_win is not None:
            self._apply_single_subtitle_style()
        for win in self._subtitle_paragraph_wins:
            self._apply_paragraph_subtitle_style(win)
        if self._subtitle_active:
            self._layout_subtitles()

    def _adjust_overlay_font_delta(self, delta: int):
        current = int(self.settings.get("overlay_font_delta", 0))
        value = max(-12, min(24, current + delta))
        self.settings.set("overlay_font_delta", value)
        self.refresh_overlay_style()
        self.overlay_font_delta_changed.emit(value)

    def set_ocr_text(self, text: str):
        self._ocr_text = text
        short = (text[:35] + "...") if len(text) > 35 else text
        self._ocr_label.setText(short)

    def start_dismiss_timer(self):
        if self.mode == self.MODE_TEMP:
            ms = self.settings.get("temp_box_timeout", 3) * 1000
            self._dismiss_timer.start(ms)

    def start_auto_translate(self):
        ms = self.settings.get("auto_translate_interval", 2) * 1000
        self._auto_timer.start(ms)

    def stop_auto_translate(self):
        self._auto_timer.stop()

    def show_subtitle(self, text: str):
        self._last_translation = text
        if self._subtitle_mode == self.OVERLAY_OFF or not text:
            return
        if self._can_render_paragraph_subtitles():
            self._show_paragraph_subtitles()
        else:
            self._show_single_subtitle(text)
        self._subtitle_active = True
        self._update_subtitle_button()

    def hide_subtitle(self):
        self._hide_all_subtitles()
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
        border_color = (
            QColor(80, 160, 255, 200)
            if self.mode == self.MODE_FIXED
            else QColor(220, 220, 255, 160)
        )
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
        if self._subtitle_active:
            self._layout_subtitles()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._subtitle_active:
            self.refresh_overlay_style()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._hide_all_subtitles()

    def showEvent(self, event):
        super().showEvent(event)
        if self._subtitle_active:
            self._layout_subtitles()

    def closeEvent(self, event):
        self._close_all_subtitles()
        super().closeEvent(event)
