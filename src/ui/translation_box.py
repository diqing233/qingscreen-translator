import re

from PyQt5.QtCore import QPoint, QRect, QSize, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from ui.theme import get_skin

_RESIZE_MARGIN = 8
_RESIZE_CURSORS = {
    'nw': Qt.SizeFDiagCursor, 'ne': Qt.SizeBDiagCursor,
    'sw': Qt.SizeBDiagCursor, 'se': Qt.SizeFDiagCursor,
    'n':  Qt.SizeVerCursor,   's':  Qt.SizeVerCursor,
    'w':  Qt.SizeHorCursor,   'e':  Qt.SizeHorCursor,
}
_BUTTON_HEIGHT = 22
_BUTTON_RADIUS = 5
_BTN_PADDING   = "0 8px"


class _SubtitleWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._style_sheet = ""
        self._bg_color = QColor(6, 10, 16, 232)
        self._border_color = QColor(120, 165, 230, 90)
        self._radius = 6

        self._label = QLabel(self)
        self._label.setWordWrap(True)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._label.setStyleSheet("QLabel { background: transparent; border: none; color: #f0f0f0; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(0)
        layout.addWidget(self._label)

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def set_surface_style(
        self,
        *,
        style_sheet: str,
        bg_color: QColor,
        text_color: QColor,
        border_color: QColor,
        radius: int,
        margins,
        alignment: int,
    ):
        self._style_sheet = style_sheet
        self._bg_color = QColor(bg_color)
        self._border_color = QColor(border_color)
        self._radius = radius
        self.layout().setContentsMargins(*margins)
        self._label.setAlignment(alignment)
        self._label.setStyleSheet(
            f"QLabel {{ background: transparent; border: none; color: {text_color.name()}; }}"
        )
        self.updateGeometry()
        self.update()

    def setText(self, text: str):
        self._label.setText(text)
        self.updateGeometry()

    def text(self) -> str:
        return self._label.text()

    def setWordWrap(self, enabled: bool):
        self._label.setWordWrap(enabled)

    def setAlignment(self, alignment: int):
        self._label.setAlignment(alignment)

    def font(self):
        return self._label.font()

    def setFont(self, font):
        self._label.setFont(font)
        super().setFont(font)
        self.updateGeometry()

    def styleSheet(self) -> str:
        return self._style_sheet

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QPen(self._border_color, 1))
        painter.setBrush(self._bg_color)
        painter.drawRoundedRect(rect, self._radius, self._radius)
        super().paintEvent(event)


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
    OVERLAY_OVER_PARA = "over_para"
    OVERLAY_BELOW = "below"
    OVERLAY_CYCLE = [OVERLAY_OVER, OVERLAY_OVER_PARA, OVERLAY_BELOW, OVERLAY_OFF]

    def __init__(self, rect: QRect, box_id: int, settings, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.region = rect
        self.settings = settings
        self.mode = self.MODE_TEMP
        self._drag_pos = QPoint()
        self._ocr_text = ""
        self._subtitle_win = None
        self._subtitle_inbox_win = None
        self._subtitle_paragraph_wins = []
        self._subtitle_active = False
        self._position_locked = False
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

        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(50)
        self._hover_timer.timeout.connect(self._refresh_toolbar_visibility)

        self._resize_dir = ''
        self._resize_start_global = QPoint()
        self._resize_start_geom = QRect()

        self._setup_ui()
        self._setup_window(rect)
        self._update_pin_button()
        self._update_subtitle_button()

    def _setup_window(self, rect: QRect):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)
        self.setMouseTracking(True)
        self.setGeometry(rect)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        # 左上角主按钮栏
        self._btn_bar = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)

        self._btn_translate = self._make_btn("译", "立即翻译", lambda: self.translate_requested.emit(self), tone="primary")
        self._btn_pin = self._make_btn("钉", "固定/取消固定", self._on_toggle_pin)
        self._btn_pin.setText("")
        self._btn_pin.setIcon(self._ph_icon('icon_pin'))
        self._btn_pin.setIconSize(QSize(int(self._skin.get('icon_size_toolbar', 16)), int(self._skin.get('icon_size_toolbar', 16))))
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
        self._btn_overlay_close = self._make_btn(
            "✕",
            "关闭覆盖翻译",
            lambda: self.set_overlay_mode(self.OVERLAY_OFF),
            width=24,
            tone="danger",
        )

        for btn in [
            self._btn_translate,
            self._btn_pin,
            self._btn_subtitle,
            self._btn_overlay_font_down,
            self._btn_overlay_font_up,
            self._btn_overlay_close,
        ]:
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        self._btn_bar.setVisible(False)

        # 初始隐藏覆盖相关按钮
        self._btn_overlay_font_down.setVisible(False)
        self._btn_overlay_font_up.setVisible(False)
        self._btn_overlay_close.setVisible(False)

        layout.addWidget(self._btn_bar)

        # 右上角关闭按钮组
        self._corner_bar = QWidget(self)
        corner_layout = QHBoxLayout(self._corner_bar)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(2)

        self._btn_hide = self._make_btn("隐", "隐藏", self.hide)
        self._btn_close = self._make_btn("✕", "关闭", lambda: self.close_requested.emit(self), tone="danger")

        corner_layout.addWidget(self._btn_hide)
        corner_layout.addWidget(self._btn_close)
        self._corner_bar.setVisible(False)
        self._corner_bar.raise_()

        self._ocr_label = QLabel("")
        self._ocr_label.setStyleSheet(
            f"color: {self._skin.get('text_ocr', 'rgba(220,220,220,160)')}; font-size: 10px;"
        )
        self._ocr_label.setWordWrap(True)
        layout.addWidget(self._ocr_label)
        layout.addStretch()

    def _button_style(
        self,
        *,
        background,
        color,
        border,
        hover_background,
        hover_color="white",
        pressed_background=None,
        radius=_BUTTON_RADIUS,
        padding=_BTN_PADDING,
        font_size=None,
        font_weight=500,
    ):
        pressed_background = pressed_background or hover_background
        if font_size is None:
            font_size = int(self._skin.get('button_font_size_compact', 12))
        return f"""
            QPushButton {{
                background: {background};
                color: {color};
                border: 1px solid {border};
                border-radius: {radius}px;
                padding: {padding};
                font-size: {font_size}px;
                font-weight: {font_weight};
            }}
            QPushButton:hover {{
                background: {hover_background};
                color: {hover_color};
            }}
            QPushButton:pressed {{
                background: {pressed_background};
                color: {hover_color};
            }}
        """

    def _icon_color(self, *, active: bool = False) -> QColor:
        token = 'button_icon_active_stroke' if active else 'button_icon_stroke'
        raw = self._skin.get(token, self._skin.get('text_muted', 'rgba(220,220,220,220)'))
        if raw.startswith('#'):
            return QColor(raw)
        match = re.match(r'rgba?\s*\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s]+(\d+))?\s*\)', raw)
        if match:
            alpha = int(match.group(4)) if match.group(4) else 255
            return QColor(int(match.group(1)), int(match.group(2)), int(match.group(3)), alpha)
        return QColor(220, 220, 220, 220)

    def _make_icon(self, draw_fn, *, active: bool = False) -> QIcon:
        size = int(self._skin.get('button_icon_size_toolbar', 14))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(self._icon_color(active=active), 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        draw_fn(painter, size)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _draw_pin(painter: QPainter, size: int):
        """45度斜插图钉：实心圆帽 + 颈杆 + 肩横杆 + 针杆，帽朝左上针尖朝右下。"""
        s = size
        painter.save()
        painter.translate(s / 2.0, s / 2.0)
        painter.rotate(-45)
        painter.translate(-s / 2.0, -s / 2.0)
        cx = s // 2
        # 实心圆帽
        hr = int(s * 0.18)
        hy = int(s * 0.28)
        painter.setBrush(painter.pen().color())
        painter.drawEllipse(cx - hr, hy - hr, hr * 2, hr * 2)
        painter.setBrush(Qt.NoBrush)
        # 颈杆
        painter.drawLine(cx, hy + hr, cx, int(s * 0.52))
        # 肩横杆
        painter.drawLine(int(cx - s * 0.15), int(s * 0.52), int(cx + s * 0.15), int(s * 0.52))
        # 针杆
        painter.drawLine(cx, int(s * 0.52), cx, int(s * 0.84))
        painter.restore()

    @property
    def _skin(self) -> dict:
        return get_skin(
            self.settings.get('skin', 'deep_space'),
            self.settings.get('button_style_variant', 'calm'),
            font_set=self.settings.get('font_set', None),
            icon_set=self.settings.get('icon_set', None),
        )

    def _ph_icon(self, codepoint_key: str, *, active: bool = False) -> QIcon:
        """Render a Phosphor font character as a QIcon."""
        from PyQt5.QtGui import QFont
        s = self._skin
        size = int(s.get('icon_size_toolbar', 16))
        icon_font_name = s.get('icon_font', 'Phosphor')
        char = s.get(codepoint_key, '')
        if not char:
            return QIcon()
        color = self._icon_color(active=active)
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        font = QFont(icon_font_name)
        font.setPixelSize(size)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, char)
        painter.end()
        return QIcon(pm)

    def _apply_button_style(self, btn, *, active=False, tone=None):
        s = self._skin
        tone = tone or btn.property("tone") or "neutral"
        if tone == "primary":
            btn.setStyleSheet(
                self._button_style(
                    background=s['btn_primary_bg'],
                    color="white",
                    border=s['btn_primary_border'],
                    hover_background=s['btn_primary_hover'],
                    font_weight=600,
                )
            )
            return
        if tone == "danger":
            btn.setStyleSheet(
                self._button_style(
                    background=s['btn_danger_bg'],
                    color="white",
                    border=s['btn_danger_border'],
                    hover_background=s['btn_danger_hover'],
                    font_weight=600,
                )
            )
            return
        if active:
            btn.setStyleSheet(
                self._button_style(
                    background=s['btn_active_bg'],
                    color=s['btn_active_fg'],
                    border=s['btn_active_border'],
                    hover_background=s['btn_active_hover'],
                )
            )
            return
        btn.setStyleSheet(
            self._button_style(
                background=s['btn_bg'],
                color=s['btn_fg'],
                border=s['btn_border'],
                hover_background=s['btn_hover'],
            )
        )

    def _make_btn(self, label, tooltip, callback, width=22, tone="neutral"):
        btn = QPushButton(label)
        btn.setToolTip(tooltip)
        btn.setFixedSize(width, _BUTTON_HEIGHT)
        btn.setProperty("tone", tone)
        self._apply_button_style(btn, tone=tone)
        btn.clicked.connect(callback)
        return btn

    def _normalize_overlay_mode(self, mode: str) -> str:
        if mode in {self.OVERLAY_OFF, self.OVERLAY_OVER, self.OVERLAY_OVER_PARA, self.OVERLAY_BELOW}:
            return mode
        return self.OVERLAY_OFF

    def _current_overlay_font_size(self) -> int:
        base = max(12, min(18, int(self.height() * 0.18)))
        delta = int(self.settings.get("overlay_font_delta", 0))
        return max(10, min(28, base + delta))

    def _create_detached_subtitle_win(self):
        win = _SubtitleWindow()
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        if hasattr(Qt, "WindowTransparentForInput"):
            flags |= Qt.WindowTransparentForInput
        win.setWindowFlags(flags)
        win.setWordWrap(True)
        return win

    def _create_inbox_subtitle_win(self):
        win = _SubtitleWindow(self)
        win.setWordWrap(True)
        win.hide()
        return win

    def _ensure_single_subtitle_win(self):
        if self._subtitle_win is None:
            self._subtitle_win = self._create_detached_subtitle_win()
        return self._subtitle_win

    def _ensure_single_inbox_subtitle_win(self):
        if self._subtitle_inbox_win is None:
            self._subtitle_inbox_win = self._create_inbox_subtitle_win()
        return self._subtitle_inbox_win

    def _sync_paragraph_subtitle_wins(self, target_count: int):
        while len(self._subtitle_paragraph_wins) < target_count:
            self._subtitle_paragraph_wins.append(self._create_inbox_subtitle_win())
        while len(self._subtitle_paragraph_wins) > target_count:
            win = self._subtitle_paragraph_wins.pop()
            win.close()

    def _all_subtitle_wins(self):
        wins = []
        if self._subtitle_win is not None:
            wins.append(self._subtitle_win)
        if self._subtitle_inbox_win is not None:
            wins.append(self._subtitle_inbox_win)
        wins.extend(self._subtitle_paragraph_wins)
        return wins

    def _apply_font(self, win):
        font = win.font()
        font.setPixelSize(self._current_overlay_font_size())
        font.setBold(False)
        win.setFont(font)

    def _apply_over_subtitle_style(self, win):
        self._apply_font(win)
        s = self._skin
        bg = QColor(*s.get('overlay_bg', (6, 10, 16, 244)))
        text = QColor(s.get('overlay_text', '#f0f8ff'))
        border = QColor(*s.get('overlay_border', (150, 190, 235, 110)))
        win.set_surface_style(
            style_sheet=f"""
            QLabel {{
                background: rgba({bg.red()}, {bg.green()}, {bg.blue()}, {bg.alpha()});
                color: {s.get('overlay_text', '#f0f8ff')};
                padding: 6px 10px 7px 10px;
                border: 1px solid rgba({border.red()}, {border.green()}, {border.blue()}, {border.alpha()});
                border-radius: 2px;
            }}
            """,
            bg_color=bg,
            text_color=text,
            border_color=border,
            radius=2,
            margins=(10, 6, 10, 7),
            alignment=Qt.AlignLeft | Qt.AlignTop,
        )

    def _apply_below_subtitle_style(self, win):
        self._apply_font(win)
        s = self._skin
        bg = QColor(*s.get('overlay_below_bg', (6, 10, 16, 232)))
        text = QColor(s.get('overlay_below_text', '#f0f0f0'))
        border = QColor(*s.get('overlay_below_border', (120, 165, 230, 90)))
        win.set_surface_style(
            style_sheet=f"""
            QLabel {{
                background: rgba({bg.red()}, {bg.green()}, {bg.blue()}, {bg.alpha()});
                color: {s.get('overlay_below_text', '#f0f0f0')};
                padding: 6px 12px;
                border: 1px solid rgba({border.red()}, {border.green()}, {border.blue()}, {border.alpha()});
                border-radius: 0px 0px 6px 6px;
            }}
            """,
            bg_color=bg,
            text_color=text,
            border_color=border,
            radius=6,
            margins=(12, 6, 12, 6),
            alignment=Qt.AlignLeft | Qt.AlignVCenter,
        )

    def _apply_paragraph_subtitle_style(self, win):
        self._apply_over_subtitle_style(win)

    def _below_overlay_rect(self) -> QRect:
        return QRect(self.x(), self.y() + self.height(), self.width(), 0)

    def _toolbar_safe_top(self) -> int:
        layout = self.layout()
        top_margin = layout.contentsMargins().top() if layout is not None else 6
        spacing = layout.spacing() if layout is not None else 2
        return max(28, top_margin + self._btn_bar.sizeHint().height() + spacing)

    def _raise_toolbar(self):
        self._btn_bar.raise_()
        self._corner_bar.raise_()

    def _position_corner_bar(self):
        self._corner_bar.adjustSize()
        w = self._corner_bar.sizeHint().width()
        h = self._corner_bar.sizeHint().height()
        x = self.width() - w - 6
        self._corner_bar.setGeometry(x, 6, w, h)

    def _over_fallback_rect(self) -> QRect:
        left = 2
        top = self._toolbar_safe_top()
        right = 2
        bottom = 8
        return QRect(
            left,
            top,
            max(60, self.width() - left - right),
            max(20, self.height() - top - bottom),
        )

    def _paragraph_overlay_rect(self, paragraph):
        rect = paragraph.get("rect", {})
        x = max(0, int(rect.get("x", 0)))
        y = max(0, int(rect.get("y", 0)))
        width = max(80, int(rect.get("width", 0)))
        max_width = max(80, self.width() - x)
        width = min(width, max_width)
        return QRect(x, y, width, max(20, int(rect.get("height", 0))))

    def _can_render_paragraph_subtitles(self) -> bool:
        return (
            self._subtitle_mode == self.OVERLAY_OVER_PARA
            and bool(self._last_ocr_paragraphs)
            and len(self._last_ocr_paragraphs) == len(self._last_paragraph_translations)
            and all(self._last_paragraph_translations)
        )

    def _layout_single_detached_subtitle(self):
        win = self._ensure_single_subtitle_win()
        rect = self._below_overlay_rect()
        win.setMinimumSize(0, 0)
        win.setMaximumSize(16777215, 16777215)
        win.setFixedWidth(rect.width())
        win.adjustSize()
        win.move(rect.x(), rect.y())

    def _layout_single_inbox_subtitle(self):
        win = self._ensure_single_inbox_subtitle_win()
        bounds = self._over_fallback_rect()
        available_height = max(24, self.height() - bounds.y() - 4)
        win.setMinimumSize(0, 0)
        win.setMaximumSize(bounds.width(), available_height)
        win.setFixedWidth(bounds.width())
        win.adjustSize()
        height = min(max(24, win.sizeHint().height()), available_height)
        win.setGeometry(bounds.x(), bounds.y(), bounds.width(), height)

    def _layout_paragraph_subtitles(self):
        self._sync_paragraph_subtitle_wins(len(self._last_ocr_paragraphs))
        next_top = self._toolbar_safe_top()
        min_height = 18
        paragraph_spacing = 2
        for paragraph, translated, win in zip(
            self._last_ocr_paragraphs,
            self._last_paragraph_translations,
            self._subtitle_paragraph_wins,
        ):
            self._apply_paragraph_subtitle_style(win)
            win.setText(translated)
            rect = self._paragraph_overlay_rect(paragraph)
            top = max(rect.y(), next_top)
            max_top = max(self._toolbar_safe_top(), self.height() - min_height)
            top = min(top, max_top)
            available_height = max(min_height, self.height() - top)
            win.setMinimumSize(0, 0)
            win.setMaximumSize(rect.width(), available_height)
            win.setFixedWidth(rect.width())
            win.adjustSize()
            height = min(max(min_height, win.sizeHint().height()), available_height)
            win.setGeometry(rect.x(), top, rect.width(), height)
            next_top = top + height + paragraph_spacing

    def _show_single_subtitle(self, text: str):
        self._sync_paragraph_subtitle_wins(0)
        for win in self._subtitle_paragraph_wins:
            win.hide()

        if self._subtitle_mode in (self.OVERLAY_OVER, self.OVERLAY_OVER_PARA):
            if self._subtitle_win is not None:
                self._subtitle_win.hide()
            win = self._ensure_single_inbox_subtitle_win()
            win.setText(text)
            self._apply_over_subtitle_style(win)
            self._layout_single_inbox_subtitle()
            win.show()
            win.raise_()
            self._raise_toolbar()
            return

        if self._subtitle_inbox_win is not None:
            self._subtitle_inbox_win.hide()
        win = self._ensure_single_subtitle_win()
        win.setText(text)
        self._apply_below_subtitle_style(win)
        self._layout_single_detached_subtitle()
        win.show()
        win.raise_()

    def _show_paragraph_subtitles(self):
        if self._subtitle_win is not None:
            self._subtitle_win.hide()
        if self._subtitle_inbox_win is not None:
            self._subtitle_inbox_win.hide()
        self._layout_paragraph_subtitles()
        for win in self._subtitle_paragraph_wins:
            win.show()
            win.raise_()
        self._raise_toolbar()

    def _hide_all_subtitles(self):
        for win in self._all_subtitle_wins():
            win.hide()

    def _close_all_subtitles(self):
        if self._subtitle_win is not None:
            self._subtitle_win.close()
            self._subtitle_win = None
        if self._subtitle_inbox_win is not None:
            self._subtitle_inbox_win.close()
            self._subtitle_inbox_win = None
        for win in self._subtitle_paragraph_wins:
            win.close()
        self._subtitle_paragraph_wins = []

    def _layout_subtitles(self):
        if self._subtitle_mode == self.OVERLAY_OVER_PARA and self._can_render_paragraph_subtitles():
            self._show_paragraph_subtitles()
            return
        if self._last_translation:
            self._show_single_subtitle(self._last_translation)

    def _update_subtitle_button(self):
        tips = {
            self.OVERLAY_OFF: "覆盖翻译：关闭，点击切到原文上（整体）",
            self.OVERLAY_OVER: "覆盖翻译：原文上（整体），点击切到分段",
            self.OVERLAY_OVER_PARA: "覆盖翻译：原文上（分段），点击切到原文下方",
            self.OVERLAY_BELOW: "覆盖翻译：原文下方，点击关闭",
        }
        self._btn_subtitle.setToolTip(tips.get(self._subtitle_mode, tips[self.OVERLAY_OFF]))

        # 控制覆盖相关按钮的显示
        overlay_active = self._subtitle_mode != self.OVERLAY_OFF
        self._btn_overlay_font_down.setVisible(overlay_active)
        self._btn_overlay_font_up.setVisible(overlay_active)
        self._btn_overlay_close.setVisible(overlay_active)

        self._apply_button_style(self._btn_subtitle, active=self._subtitle_mode != self.OVERLAY_OFF)

    def _update_pin_button(self):
        icon_size = int(self._skin.get('icon_size_toolbar', 16))
        self._btn_pin.setText("")
        self._btn_pin.setIcon(self._ph_icon('icon_unpin' if self._position_locked else 'icon_pin', active=self._position_locked))
        self._btn_pin.setIconSize(QSize(icon_size, icon_size))
        self._apply_button_style(self._btn_pin, active=self._position_locked)

    def _on_toggle_pin(self):
        self.set_position_locked(not self._position_locked)

    def set_position_locked(self, locked: bool):
        self._position_locked = bool(locked)
        self._drag_pos = QPoint()
        if self._position_locked:
            self._dismiss_timer.stop()
        elif self.mode == self.MODE_TEMP and self.isVisible():
            self.start_dismiss_timer()
        self._update_pin_button()
        self.update()

    def set_mode(self, mode: str):
        self.mode = mode
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
            self._apply_below_subtitle_style(self._subtitle_win)
        if self._subtitle_inbox_win is not None:
            self._apply_over_subtitle_style(self._subtitle_inbox_win)
        for win in self._subtitle_paragraph_wins:
            self._apply_paragraph_subtitle_style(win)
        if self._subtitle_active:
            self._layout_subtitles()

    def apply_skin(self):
        """皮肤改变后重新应用所有样式。"""
        s = self._skin
        # 按钮
        for btn in [self._btn_translate, self._btn_pin, self._btn_subtitle,
                    self._btn_overlay_font_down, self._btn_overlay_font_up, self._btn_overlay_close,
                    self._btn_hide]:
            self._apply_button_style(btn)
        self._apply_button_style(self._btn_close, tone='danger')
        self._apply_button_style(self._btn_translate, tone='primary')
        self._update_pin_button()
        self._update_subtitle_button()
        # OCR 标签
        self._ocr_label.setStyleSheet(
            f"color: {s.get('text_ocr', 'rgba(220,220,220,160)')}; font-size: 10px;"
        )
        # 边框重绘
        self.update()
        # 覆盖字幕
        self.refresh_overlay_style()

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
        if self.mode == self.MODE_TEMP and not self._position_locked:
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
        if self.mode == self.MODE_TEMP and not self._position_locked:
            self.close_requested.emit(self)

    def _box_global_rect(self) -> QRect:
        return QRect(self.x(), self.y(), self.width(), self.height())

    def _refresh_toolbar_visibility(self, global_pos=None):
        if global_pos is None:
            global_pos = QCursor.pos()
        visible = self.isVisible() and self._box_global_rect().contains(global_pos)
        self._btn_bar.setVisible(visible)
        self._corner_bar.setVisible(visible)
        if visible:
            self._raise_toolbar()
            self._position_corner_bar()

    def _can_resize(self) -> bool:
        return self.mode == self.MODE_FIXED or self._position_locked

    def _resize_direction(self, pos: QPoint) -> str:
        if not self._can_resize():
            return ''
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        m = _RESIZE_MARGIN
        left   = x < m
        right  = x > w - m
        top    = y < m
        bottom = y > h - m
        if top and left:     return 'nw'
        if top and right:    return 'ne'
        if bottom and left:  return 'sw'
        if bottom and right: return 'se'
        if left:   return 'w'
        if right:  return 'e'
        if top:    return 'n'
        if bottom: return 's'
        return ''

    def _do_resize(self, global_pos: QPoint):
        dx = global_pos.x() - self._resize_start_global.x()
        dy = global_pos.y() - self._resize_start_global.y()
        geom = QRect(self._resize_start_geom)
        d = self._resize_dir
        min_w, min_h = self.minimumWidth(), self.minimumHeight()
        if 'e' in d:
            geom.setRight(max(geom.left() + min_w, geom.right() + dx))
        if 's' in d:
            geom.setBottom(max(geom.top() + min_h, geom.bottom() + dy))
        if 'w' in d:
            geom.setLeft(min(geom.right() - min_w, geom.left() + dx))
        if 'n' in d:
            geom.setTop(min(geom.bottom() - min_h, geom.top() + dy))
        self.setGeometry(geom)
        self.region = geom

    def enterEvent(self, event):
        self.raise_()
        self._refresh_toolbar_visibility()

    def leaveEvent(self, event):
        self._refresh_toolbar_visibility()

    def paintEvent(self, event):
        s = self._skin
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        fill = QColor(*s.get('box_fill', (0, 0, 0, 4)))
        painter.fillRect(self.rect(), fill)
        if self.mode == self.MODE_FIXED or self._position_locked:
            bc = s.get('box_border_fixed', (80, 160, 255, 200))
        else:
            bc = s.get('box_border_temp', (220, 220, 255, 160))
        border_color = QColor(*bc)
        pen = QPen(border_color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            direction = self._resize_direction(event.pos())
            if direction:
                self._resize_dir = direction
                self._resize_start_global = event.globalPos()
                self._resize_start_geom = self.geometry()
                self._drag_pos = QPoint()
                return
            if self._position_locked:
                self._drag_pos = QPoint()
                return
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        else:
            self._resize_dir = ''

    def mouseMoveEvent(self, event):
        self._refresh_toolbar_visibility(event.globalPos())
        if self._resize_dir:
            self._do_resize(event.globalPos())
            return
        direction = self._resize_direction(event.pos())
        if direction:
            self.setCursor(QCursor(_RESIZE_CURSORS[direction]))
        else:
            self.unsetCursor()
        if self._position_locked:
            return
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
            self.region = QRect(new_pos.x(), new_pos.y(), self.width(), self.height())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_dir = ''
            self._drag_pos = QPoint()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._refresh_toolbar_visibility()
        if self._subtitle_active:
            self._layout_subtitles()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_corner_bar()
        self._refresh_toolbar_visibility()
        if self._subtitle_active:
            self.refresh_overlay_style()

    def hideEvent(self, event):
        super().hideEvent(event)
        self._hover_timer.stop()
        self._btn_bar.setVisible(False)
        self._corner_bar.setVisible(False)
        self._hide_all_subtitles()

    def showEvent(self, event):
        super().showEvent(event)
        self._hover_timer.start()
        self._refresh_toolbar_visibility()
        if self._subtitle_active:
            self._layout_subtitles()

    def closeEvent(self, event):
        self._hover_timer.stop()
        self._close_all_subtitles()
        super().closeEvent(event)
