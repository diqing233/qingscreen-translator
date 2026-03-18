import logging
import re
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLabel, QPushButton,
                              QHBoxLayout, QVBoxLayout, QApplication,
                              QSizePolicy, QMenu, QAction, QTextEdit,
                              QScrollArea, QFrame, QSplitter)
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QSize, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont, QPainter, QPen, QColor, QIcon, QPixmap, QPolygonF
from ui.theme import get_skin, make_menu_qss, make_container_qss, make_scrollbar_qss

logger = logging.getLogger(__name__)

# ── 数据常量 ─────────────────────────────────────────────────────

DEFAULT_W, DEFAULT_H = 640, 140

BOX_MODE_ORDER = ['fixed', 'temp', 'multi']
BOX_MODE_META = {
    'temp': ('临时', '临时翻译：框选后立即翻译，N 秒后自动消失'),
    'fixed': ('固定', '固定翻译：框保留在屏幕上，可手动或自动翻译'),
    'multi': ('多框', '多框翻译：可在屏幕上放置多个独立翻译框'),
    'ai': ('AI框', 'AI 框选：框选后直接进行 AI 解释，不走翻译'),
}

OVERLAY_MODE_ORDER = ['over', 'over_para', 'below', 'off']
OVERLAY_MODE_META = {
    'off': '覆盖翻译：关闭',
    'over': '覆盖翻译：显示在原文上（整体）',
    'over_para': '覆盖翻译：显示在原文上（分段）',
    'below': '覆盖翻译：显示在原文下方',
}

BOX_MODES = [
    ('temp',  '临时', '临时翻译：框选后立即翻译，N秒后自动消失'),
    ('fixed', '固定', '固定翻译：框保留在屏幕上，可手动或自动翻译'),
    ('multi', '多框', '多框翻译：可在屏幕上放置多个独立翻译框'),
    ('ai',    'AI框', 'AI框选：框选后直接AI科普，无需翻译'),
]

SOURCE_LANGS = [
    ('auto', 'AUTO', '自动检测'),
    ('zh',   '中',   '中文'),
    ('en',   'EN',   'English'),
    ('ja',   'JA',   '日本語'),
    ('ko',   'KO',   '한국어'),
    ('fr',   'FR',   'Français'),
    ('de',   'DE',   'Deutsch'),
    ('es',   'ES',   'Español'),
    ('ru',   'RU',   'Русский'),
]

TARGET_LANGS = [
    ('zh-CN', '简中', '简体中文'),
    ('zh-TW', '繁中', '繁体中文'),
    ('en',    'EN',   'English'),
    ('ja',    'JA',   '日本語'),
    ('ko',    'KO',   '한국어'),
    ('fr',    'FR',   'Français'),
    ('de',    'DE',   'Deutsch'),
    ('es',    'ES',   'Español'),
    ('ru',    'RU',   'Русский'),
]

_TOOLBAR_BUTTON_H = 22
_TOOLBAR_ICON_W = 22
_SMALL_TOOLBAR_BUTTON_W = 26
_BUTTON_RADIUS = 5

# ── Shared neutral button base metrics (applied to all helper styles) ───
# All non-primary buttons share these metrics for consistent visual rhythm.
_BTN_H          = _TOOLBAR_BUTTON_H   # 22 px
_BTN_RADIUS     = _BUTTON_RADIUS      # 5 px
_BTN_PADDING    = '0 8px'             # horizontal padding
_BTN_BORDER_PX  = 1                   # border weight in px


# ── 任务栏最小化代理窗口 ─────────────────────────────────────────

class _MinimizeProxy(QMainWindow):
    """最小化时出现在任务栏的占位窗口。
    QMainWindow 天然拥有任务栏按钮，无需 ctypes 或 flag 技巧。
    用户点击任务栏按钮恢复时，自动调用 result_bar._restore_from_taskbar()。
    """
    def __init__(self, result_bar):
        super().__init__()
        self._result_bar = result_bar
        self.setWindowTitle('ScreenTranslator')
        px = QPixmap(16, 16)
        px.fill(QColor(70, 130, 240))
        self.setWindowIcon(QIcon(px))
        self.resize(1, 1)

    def changeEvent(self, event):
        super().changeEvent(event)
        if (event.type() == QEvent.WindowStateChange
                and self._result_bar._minimized
                and not (self.windowState() & Qt.WindowMinimized)):
            self.hide()
            self._result_bar._restore_from_taskbar()


class _ResetSizeBtn(QPushButton):
    """恢复默认大小按钮，用 QPainter 绘制圆形刷新箭头"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon_color = QColor(160, 160, 185, 200)

    def set_icon_color(self, color: QColor):
        self._icon_color = color
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)  # 先绘制背景/边框（来自 stylesheet）
        import math

        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) / 2.0 - 4.5

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        col = QColor(self._icon_color)
        if not self.isEnabled():
            col.setAlpha(80)

        pen = QPen(col, 1.6)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        # 圆弧：从 80° 开始，顺时针扫 300°，结束于 140°（缺口在顶部）
        p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), 80 * 16, -300 * 16)

        # 箭头在 140° 处，指向顺时针方向
        end_rad = math.radians(140.0)
        ex = cx + r * math.cos(end_rad)
        ey = cy - r * math.sin(end_rad)
        tx = math.sin(end_rad)   # 顺时针切线 x
        ty = -math.cos(end_rad)  # 顺时针切线 y

        al = r * 0.48  # 箭头长度
        aw = r * 0.32  # 箭头半宽
        bx, by = ex - tx * al, ey - ty * al
        px2, py2 = -ty, tx  # 垂直方向

        p.setBrush(col)
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([
            QPointF(ex, ey),
            QPointF(bx + px2 * aw, by + py2 * aw),
            QPointF(bx - px2 * aw, by - py2 * aw),
        ]))
        p.end()


# ── 滑动切换控件 ──────────────────────────────────────────────────

class TranslateToggle(QWidget):
    """两段式滑动切换：点击 ↔ 自动"""
    toggled = pyqtSignal(bool)  # True = auto

    W, H = 84, 22

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto = False
        self._skin = None   # 由外部调用 set_skin() 注入
        self.setFixedSize(self.W, self.H)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('点击切换：手动点击翻译 / 自动持续翻译')

    def set_skin(self, skin: dict):
        self._skin = skin
        self.update()

    def set_auto(self, v: bool):
        self._auto = v
        self.update()

    def sizeHint(self):
        return QSize(self.W, self.H)

    def paintEvent(self, event):
        s = self._skin or {}
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h // 2
        mid = w // 2

        # Track background — slightly more visible border for clarity
        track_border = QColor(*s.get('toggle_track_border', (255, 255, 255, 40)))
        track_bg = QColor(*s.get('toggle_track', (29, 31, 41, 228)))
        p.setPen(QPen(track_border, 1))
        p.setBrush(track_bg)
        p.drawRoundedRect(0, 0, w - 1, h - 1, r, r)

        # Active pill — calmer hues: use theme colors but keep alpha moderate
        pill_x = mid if self._auto else 0
        auto_c  = s.get('toggle_auto',   (72, 158,  96, 210))
        manual_c = s.get('toggle_manual', (76, 122, 218, 210))
        pill_color = QColor(*auto_c) if self._auto else QColor(*manual_c)
        p.setBrush(pill_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(pill_x + 1, 1, mid - 2, h - 2, r - 1, r - 1)

        # Divider — more visible than before for clear segmentation
        p.setPen(QPen(QColor(255, 255, 255, 28), 1))
        p.drawLine(mid, 4, mid, h - 5)

        # Text labels — clearer contrast: active side bright, inactive side dim
        f = p.font()
        f.setPixelSize(12)
        p.setFont(f)

        txt_bright = QColor(255, 255, 255, 240)   # active side label
        txt_dim    = QColor(255, 255, 255,  90)    # inactive side label (dimmer for separation)
        p.setPen(txt_dim if self._auto else txt_bright)
        p.drawText(0, 0, mid, h, Qt.AlignCenter, '点击')

        p.setPen(txt_bright if self._auto else txt_dim)
        p.drawText(mid, 0, mid, h, Qt.AlignCenter, '自动')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._auto = not self._auto
            self.update()
            self.toggled.emit(self._auto)


# ── 左右分割按钮 ─────────────────────────────────────────────────

class _SplitButton(QWidget):
    """左侧点击 → left_clicked，右侧点击 → right_clicked，中间一条竖线分隔。"""
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()

    _RIGHT_W = 20  # 右侧箭头区域固定宽度

    def __init__(self, left_label: str, parent=None):
        super().__init__(parent)
        self._left_label = left_label
        self._arrow = '▼'
        self._active = False
        self._hover_left = False
        self._hover_right = False
        self._skin = None   # 由外部调用 set_skin() 注入
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(_TOOLBAR_BUTTON_H)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        f = self.font()
        f.setPixelSize(12)
        self.setFont(f)

    def set_skin(self, skin: dict):
        self._skin = skin
        self.update()

    def sizeHint(self):
        left_w = self.fontMetrics().horizontalAdvance(self._left_label) + 16
        return QSize(left_w + self._RIGHT_W + 1, _TOOLBAR_BUTTON_H)

    def set_arrow(self, up: bool):
        self._arrow = '▲' if up else '▼'
        self._active = bool(up)
        self.update()

    def _divider_x(self) -> int:
        return self.width() - self._RIGHT_W

    def paintEvent(self, event):
        s = self._skin or {}
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        div_x = self._divider_x()
        enabled = self.isEnabled()
        fade = 0.45 if not enabled else 1.0

        def a(v):
            return int(v * fade)

        # Active state: mild lift using btn_hover/btn_active_border — mirrors
        # the softened _action_btn_style(active=True) treatment.
        if self._active:
            # Use the hover background (mild lift) + a slightly raised border
            _ab = s.get('split_active_bg', (70, 74, 92, 204))   # slightly lighter than idle
            _ac = s.get('split_active_border', (142, 165, 220, 72))
            background = QColor(_ab[0], _ab[1], _ab[2], a(_ab[3]))
            border = QColor(_ac[0], _ac[1], _ac[2], a(_ac[3]))
        else:
            _sb = s.get('split_bg', (58, 60, 74, 192))
            _sc = s.get('split_border', (255, 255, 255, 20))
            background = QColor(_sb[0], _sb[1], _sb[2], a(_sb[3]))
            border = QColor(_sc[0], _sc[1], _sc[2], a(_sc[3]))
        _tc = s.get('split_text', (236, 239, 247, 236))
        text_color = QColor(_tc[0], _tc[1], _tc[2], _tc[3] if self._active else a(_tc[3]))
        hover_fill = QColor(255, 255, 255, 16 if self._active else 12)

        painter.setPen(QPen(border, 1))
        painter.setBrush(background)
        painter.drawRoundedRect(0, 0, w - 1, h - 1, _BUTTON_RADIUS, _BUTTON_RADIUS)

        if enabled and self._hover_left:
            painter.save()
            painter.setClipRect(QRect(0, 0, div_x, h))
            painter.setPen(Qt.NoPen)
            painter.setBrush(hover_fill)
            painter.drawRoundedRect(0, 0, w - 1, h - 1, _BUTTON_RADIUS, _BUTTON_RADIUS)
            painter.restore()
        elif enabled and self._hover_right:
            painter.save()
            painter.setClipRect(QRect(div_x, 0, w - div_x, h))
            painter.setPen(Qt.NoPen)
            painter.setBrush(hover_fill)
            painter.drawRoundedRect(0, 0, w - 1, h - 1, _BUTTON_RADIUS, _BUTTON_RADIUS)
            painter.restore()

        painter.setPen(QPen(QColor(255, 255, 255, a(32)), 1))
        painter.drawLine(div_x, 3, div_x, h - 4)

        painter.setPen(
            QColor(255, 255, 255, 230) if (enabled and self._hover_left) else text_color
        )
        painter.drawText(QRect(0, 0, div_x, h), Qt.AlignCenter, self._left_label)

        painter.setPen(
            QColor(255, 255, 255, 230) if (enabled and self._hover_right) else text_color
        )
        painter.drawText(QRect(div_x, 0, w - div_x, h), Qt.AlignCenter, self._arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            if event.x() < self._divider_x():
                self.left_clicked.emit()
            else:
                self.right_clicked.emit()

    def mouseMoveEvent(self, event):
        div_x = self._divider_x()
        x = event.x()
        new_left, new_right = x < div_x, x >= div_x
        if new_left != self._hover_left or new_right != self._hover_right:
            self._hover_left, self._hover_right = new_left, new_right
            self.update()

    def leaveEvent(self, event):
        self._hover_left = self._hover_right = False
        self.update()


# ── 主结果条 ─────────────────────────────────────────────────────

class ResultBar(QWidget):
    start_selection_requested = pyqtSignal()
    stop_clear_requested      = pyqtSignal()
    explain_requested         = pyqtSignal(str)
    retranslate_requested     = pyqtSignal(str)
    history_requested         = pyqtSignal()
    settings_requested        = pyqtSignal()
    close_requested           = pyqtSignal()
    overlay_requested         = pyqtSignal(str, str)   # mode, current translated text
    box_mode_changed          = pyqtSignal(str)   # 'temp'|'fixed'|'multi'|'ai'
    translate_mode_changed    = pyqtSignal(str)   # 'manual'|'auto'
    target_language_changed   = pyqtSignal(str)
    source_language_changed   = pyqtSignal(str)
    overlay_font_delta_changed = pyqtSignal(int)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._current_result = None
        self._source_expanded = False
        self._explain_expanded = False
        self._source_dirty = False
        self._synced_source_text = ''
        self._syncing_source_editor = False
        self._minimized = False
        self._drag_pos = QPoint()
        self._box_mode = 'fixed'
        self._overlay_mode = self.settings.get('overlay_default_mode', 'off')
        self._para_mode: bool = bool(self.settings.get('para_split_enabled', False))
        self._show_para_numbers: bool = False
        self._translation_busy = False
        self._translate_mode = 'manual'
        self._hidden_to_tray = False
        self._manual_size = False   # True once user manually resizes
        self._in_adjust = False     # True while adjustSize() is running
        self._resizing = False      # True while dragging bottom-right to resize
        self._resize_start_global = QPoint()
        self._resize_start_size = QSize()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._save_geometry)
        self._setup_window()
        self._setup_ui()
        self._position_window()
        self._update_source_button()
        self._update_ai_button()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)  # 保证 tooltip 在 Tool 窗口中可见
        self.setMinimumWidth(280)
        self.setMinimumHeight(60)
        self.resize(DEFAULT_W, DEFAULT_H)
        self._manual_size = True     # 防止 adjustSize() 在启动时压缩默认尺寸

    @property
    def _skin(self) -> dict:
        """返回当前皮肤字典（从 settings 读取）。"""
        return get_skin(
            self.settings.get('skin', 'deep_space'),
            self.settings.get('button_style_variant', 'calm'),
        )

    def _get_bg_alpha(self) -> int:
        return max(30, min(255, int(self.settings.get('result_bar_opacity', 0.85) * 255)))

    def _apply_opacity(self):
        alpha = self._get_bg_alpha()
        self._container.setStyleSheet(make_container_qss(self._skin, alpha))

    def _position_window(self):
        screen = QApplication.primaryScreen().geometry()
        cx = screen.center().x()
        pos = self.settings.get('result_bar_position', 'top')
        self._smart_adjust()
        w, h = self.width(), self.height()
        if pos == 'top':
            self.move(cx - w // 2, 10)
        elif pos == 'bottom':
            self.move(cx - w // 2, screen.height() - h - 50)
        elif pos == 'left':
            self.move(10, screen.center().y() - h // 2)
        elif pos == 'right':
            self.move(screen.width() - w - 10, screen.center().y() - h // 2)
        elif pos == 'center':
            self.move(screen.center().x() - w // 2, screen.center().y() - h // 2)
        elif pos == 'last':
            lx = self.settings.get('result_bar_last_x', None)
            ly = self.settings.get('result_bar_last_y', None)
            lw = self.settings.get('result_bar_last_w', None)
            lh = self.settings.get('result_bar_last_h', None)
            if lx is not None and ly is not None:
                if lw and lh:
                    self.resize(lw, lh)
                self.move(lx, ly)
                return
            self.move(cx - w // 2, 10)  # fallback
        else:
            self.move(cx - w // 2, 10)

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._container = QWidget()
        self._container.setObjectName('ct')
        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(10, 7, 10, 4)
        cl.setSpacing(4)
        self._apply_opacity()

        # ── 工具栏（可横向滚动）──────────────────────────────────
        self._tb_widget = QWidget()
        self._tb_widget.setStyleSheet('background: transparent;')
        self._tb_layout = QHBoxLayout(self._tb_widget)
        tb = self._tb_layout
        tb.setSpacing(4)
        tb.setContentsMargins(0, 0, 0, 0)

        # ▶ 播放按钮（等同 Alt+Q 框选）
        self._btn_play = QPushButton('▶')
        self._btn_play.setToolTip('开始框选翻译（同 Alt+Q）\n按住拖动框选区域，按 ESC 取消')
        self._btn_play.setFixedSize(26, 22)
        self._btn_play.setStyleSheet(self._play_btn_style())
        self._btn_play.clicked.connect(self.start_selection_requested.emit)
        tb.addWidget(self._btn_play)
        tb.addSpacing(4)

        self._btn_stop_clear = QPushButton('')
        self._btn_stop_clear.setFixedSize(22, 22)
        self._btn_stop_clear.clicked.connect(self.stop_clear_requested.emit)
        tb.addWidget(self._btn_stop_clear)
        tb.addSpacing(4)

        # ↺ 恢复默认大小按钮（手绘圆形箭头）
        self._btn_reset_size = _ResetSizeBtn()
        self._btn_reset_size.setToolTip('恢复结果条默认大小')
        self._btn_reset_size.setFixedSize(22, 22)
        self._btn_reset_size.setStyleSheet(self._neutral_small_btn_style())
        self._btn_reset_size.set_icon_color(self._muted_qcolor())
        self._btn_reset_size.clicked.connect(self._reset_size)
        tb.addWidget(self._btn_reset_size)
        tb.addSpacing(4)

        # 左侧模式按钮
        self._btn_box_mode_cycle = self._mode_btn(*BOX_MODE_META['fixed'], 'fixed')
        self._btn_box_mode_cycle.clicked.disconnect()
        self._btn_box_mode_cycle.clicked.connect(self._cycle_box_mode)
        tb.addWidget(self._btn_box_mode_cycle)

        self._btn_ai_mode = self._mode_btn(*BOX_MODE_META['ai'], 'ai')
        tb.addWidget(self._btn_ai_mode)

        tb.addSpacing(6)

        # 源语言下拉按钮
        src_code = self.settings.get('source_language', 'auto')
        src_label = next((s for c, s, _ in SOURCE_LANGS if c == src_code), 'AUTO')
        self._btn_src_lang = QPushButton(f'{src_label} ▾')
        self._btn_src_lang.setToolTip('源语言（点击切换）')
        self._btn_src_lang.setFixedHeight(_TOOLBAR_BUTTON_H)
        self._btn_src_lang.setStyleSheet(self._lang_btn_style())
        self._btn_src_lang.clicked.connect(self._show_src_lang_menu)
        tb.addWidget(self._btn_src_lang)

        # 箭头分隔
        arrow = QLabel('→')
        arrow.setStyleSheet('color: rgba(120,120,140,180); font-size: 12px;')
        tb.addWidget(arrow)

        # 目标语言下拉按钮
        tgt_code = self.settings.get('target_language', 'zh-CN')
        tgt_label = next((s for c, s, _ in TARGET_LANGS if c == tgt_code), '简中')
        self._btn_tgt_lang = QPushButton(f'{tgt_label} ▾')
        self._btn_tgt_lang.setToolTip('目标翻译语言（点击切换）')
        self._btn_tgt_lang.setFixedHeight(_TOOLBAR_BUTTON_H)
        self._btn_tgt_lang.setStyleSheet(self._lang_btn_style())
        self._btn_tgt_lang.clicked.connect(self._show_tgt_lang_menu)
        tb.addWidget(self._btn_tgt_lang)

        tb.addSpacing(6)

        # 复制译文（工具栏快捷区）
        self._btn_copy_trans = self._icon_btn('', '复制译文到剪贴板', self._copy)
        self._btn_copy_trans.setIcon(self._mk_icon(self._draw_copy))
        self._btn_copy_trans.setIconSize(QSize(14, 14))
        tb.addWidget(self._btn_copy_trans)

        tb.addSpacing(6)

        # 覆盖按钮（放在工具栏内，随内容滚动）
        self._btn_overlay = self._icon_btn('⊞', '覆盖译文到原文区域', self._on_overlay)
        tb.addWidget(self._btn_overlay)
        self._btn_overlay_font_down = self._small_toolbar_btn(
            'A-', '减小覆盖译文字号', lambda: self._adjust_overlay_font_delta(-1)
        )
        tb.addWidget(self._btn_overlay_font_down)
        self._btn_overlay_font_up = self._small_toolbar_btn(
            'A+', '增大覆盖译文字号', lambda: self._adjust_overlay_font_delta(1)
        )
        tb.addWidget(self._btn_overlay_font_up)
        self._btn_overlay_close = self._small_toolbar_btn(
            '✕', '关闭覆盖翻译', lambda: self.set_overlay_mode('off')
        )
        tb.addWidget(self._btn_overlay_close)

        tb.addSpacing(6)

        # 滑动切换：仅固定/多框模式显示
        self._toggle = TranslateToggle()
        self._toggle.set_skin(self._skin)
        self._toggle.toggled.connect(self._on_toggle_changed)
        self._toggle.setVisible(self._box_mode != 'temp')
        tb.addWidget(self._toggle)

        tb.addStretch()

        # 右侧图标按钮（固定在滚动区外，不随工具栏内容滚动）
        self._btn_history  = self._icon_btn('', '翻译历史 (History)', self.history_requested.emit)
        self._btn_history.setIcon(self._mk_icon(self._draw_clock, 18))
        self._btn_history.setIconSize(QSize(18, 18))
        self._btn_settings = self._icon_btn('⚙', '设置 (Settings)', self.settings_requested.emit)
        self._btn_minimize = self._icon_btn('─', '最小化/展开', self._toggle_minimize)
        self._btn_close    = self._icon_btn('✕', '关闭主窗口', self.close_requested.emit)

        self._tb_scroll = QScrollArea()
        self._tb_scroll.setWidget(self._tb_widget)
        self._tb_scroll.setWidgetResizable(False)
        self._tb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tb_scroll.setFrameShape(QFrame.NoFrame)
        self._tb_scroll.setFixedHeight(26)
        self._tb_scroll.setStyleSheet(self._tb_scroll_style())
        _tb_row = QHBoxLayout()
        _tb_row.setContentsMargins(0, 0, 0, 0)
        _tb_row.setSpacing(2)
        _tb_row.addWidget(self._tb_scroll, 1)
        for b in [self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close]:
            _tb_row.addWidget(b)
        cl.addLayout(_tb_row)
        self.set_stop_clear_busy(False)
        self._refresh_overlay_button()
        self._detach_overlay_controls()
        self._toggle.setVisible(self._box_mode != 'temp')
        self._refresh_toolbar_layout()
        self._set_active_mode_btn(self._box_mode)

        # 分隔线
        self._sep = QWidget()
        self._sep.setFixedHeight(1)
        self._sep.setStyleSheet(f'background: {self._skin.get("sep_color", "rgba(255,255,255,18)")};')
        cl.addWidget(self._sep)

        # ── 主体 ──────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        self._content_splitter = QSplitter(Qt.Vertical)
        self._content_splitter.setChildrenCollapsible(False)
        self._content_splitter.setHandleWidth(6)
        self._content_splitter.setStyleSheet(f'''
            QSplitter::handle:vertical {{
                background: {self._skin.get('sep_color', 'rgba(255,255,255,18)')};
                margin: 1px 0;
            }}
        ''')

        self._translation_panel = QWidget()
        self._translation_panel.setMinimumHeight(40)
        self._translation_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        translation_layout = QVBoxLayout(self._translation_panel)
        translation_layout.setContentsMargins(0, 0, 0, 0)
        translation_layout.setSpacing(0)

        self._lbl_translation = QTextEdit()
        self._lbl_translation.setReadOnly(True)
        self._lbl_translation.setPlainText('等待翻译...')
        self._update_translation_height()
        f = QFont()
        f.setPixelSize(14)
        self._lbl_translation.setFont(f)
        self._lbl_translation.setMinimumHeight(40)
        self._lbl_translation.setMinimumWidth(0)   # 防止 QTextEdit 撑宽结果条
        self._lbl_translation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_translation.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._lbl_translation.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._lbl_translation.setStyleSheet(self._translation_text_style())
        translation_layout.addWidget(self._lbl_translation)
        self._content_splitter.addWidget(self._translation_panel)

        self._details_actions_widget = QWidget()
        self._details_actions_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        ar = QHBoxLayout(self._details_actions_widget)
        ar.setContentsMargins(0, 0, 0, 0)
        ar.setSpacing(5)
        self._btn_source   = self._action_btn('原文 ▼', '展开/收起原始识别文字', self._toggle_source)
        self._btn_copy_src = self._action_btn('📋 原文', '复制原始识别文字到剪贴板', self._copy_source)
        self._btn_copy_src.setText('原文')
        self._btn_copy_src.setIcon(self._mk_icon(self._draw_copy))
        self._btn_copy_src.setIconSize(QSize(14, 14))
        self._lbl_backend = QLabel('')
        self._lbl_backend.setStyleSheet('color: rgba(100,200,120,180); font-size: 10px;')
        self._resize_hint_lbl = QLabel('拖拽右下角调整大小 ⋱')
        self._resize_hint_lbl.setStyleSheet(
            f'color: {self._skin.get("text_muted", "rgba(160,160,185,190)")}; font-size: 10px; padding: 0;'
        )
        self._resize_hint_lbl.setToolTip('拖拽此处（右下角 20px 范围）调整窗口大小')
        ar.addWidget(self._btn_source)
        ar.addWidget(self._btn_copy_src)
        self._btn_retranslate = self._action_btn('翻译', '使用当前原文内容重新翻译', self._on_retranslate)
        self._btn_retranslate.setEnabled(False)
        ar.addWidget(self._btn_retranslate)
        self._btn_ai = _SplitButton('💬 AI科普')
        self._btn_ai.set_skin(self._skin)
        self._btn_ai.left_clicked.connect(self._on_explain)
        self._btn_ai.right_clicked.connect(self._toggle_explain_section)
        ar.addWidget(self._btn_ai)
        self._btn_para_num = self._action_btn('[#]', '显示/隐藏段落编号', self._toggle_para_numbers)
        self._btn_para_num.setText('段落')
        self._btn_para_num.setIcon(self._mk_icon(self._draw_paragraph))
        self._btn_para_num.setIconSize(QSize(14, 14))
        ar.addWidget(self._btn_para_num)
        ar.addStretch()
        ar.addWidget(self._lbl_backend)
        ar.addSpacing(8)
        ar.addWidget(self._resize_hint_lbl)
        translation_layout.addWidget(self._details_actions_widget)

        # ── AI科普加载提示（在原文按钮下方，不覆盖译文）─────────
        # ── AI科普区（运行后显示在原文按钮下方）─────────────────
        self._source_panel = QWidget()
        self._source_panel.setVisible(False)
        self._source_panel.setMinimumHeight(72)
        self._source_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        src_layout = QVBoxLayout(self._source_panel)
        src_layout.setContentsMargins(0, 0, 0, 0)
        src_layout.setSpacing(4)
        self._source_editor = QTextEdit()
        self._source_editor.setAcceptRichText(False)
        self._source_editor.setMinimumHeight(72)
        self._source_editor.setMinimumWidth(0)
        self._source_editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._source_editor.setPlaceholderText('可在这里输入或修改要翻译的内容')
        self._source_editor.setStyleSheet(self._source_editor_style())
        self._source_editor.textChanged.connect(self._on_source_text_changed)
        src_layout.addWidget(self._source_editor)
        self._explain_panel = QWidget()
        self._explain_panel.setVisible(False)
        self._explain_panel.setMinimumHeight(40)
        self._explain_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        explain_layout = QVBoxLayout(self._explain_panel)
        explain_layout.setContentsMargins(0, 0, 0, 0)
        explain_layout.setSpacing(4)
        self._explain_loading_label = QLabel('💡 AI 科普中...')
        self._explain_loading_label.setStyleSheet(
            'color: rgba(230,220,130,200); font-size: 11px; padding: 2px 4px;'
        )
        self._explain_loading_label.setVisible(False)
        explain_layout.addWidget(self._explain_loading_label)
        self._explain_text = QTextEdit()
        self._explain_text.setReadOnly(True)
        self._explain_text.setMinimumHeight(40)
        self._explain_text.setMinimumWidth(0)
        self._explain_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._explain_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._explain_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._explain_text.setVisible(False)
        self._explain_text.setStyleSheet(self._explain_text_style())
        explain_layout.addWidget(self._explain_text)

        bl.addWidget(self._content_splitter, 1)

        cl.addWidget(self._body)

        outer.addWidget(self._container)

    # ── 按钮工厂 ──────────────────────────────────────────────────

    def _mode_btn(self, label: str, tip: str, key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setToolTip(tip)
        btn.setCheckable(True)
        btn.setFixedHeight(_TOOLBAR_BUTTON_H)
        btn.setMinimumWidth(36)
        btn.setStyleSheet(self._mode_btn_style(False))
        btn.clicked.connect(lambda _, k=key: self._on_mode_btn_click(k))
        return btn

    def _solid_button_style(
        self,
        *,
        background: str,
        color: str,
        border: str,
        hover_background: str,
        hover_color: str = 'white',
        pressed_background: str = None,
        disabled_background: str = None,
        disabled_color: str = 'rgba(170,174,190,130)',
        radius: int = _BUTTON_RADIUS,
        padding: str = '0 8px',
        font_size: int = 12,
        font_weight: int = 500,
    ) -> str:
        pressed_background = pressed_background or hover_background
        disabled_background = disabled_background or background
        return f'''
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
            QPushButton:disabled {{
                background: {disabled_background};
                color: {disabled_color};
                border: 1px solid rgba(255,255,255,10);
            }}
        '''

    def _play_btn_style(self) -> str:
        s = self._skin
        return self._solid_button_style(
            background=s['btn_primary_bg'],
            color='white',
            border=s['btn_primary_border'],
            hover_background=s['btn_primary_hover'],
            padding='0 6px',
            font_size=int(s.get('button_font_size_toolbar', 12)),
            font_weight=700,
        )

    def _neutral_small_btn_style(self) -> str:
        s = self._skin
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s.get('text_muted', s['btn_fg']),
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            padding='0 4px',
            font_size=15,
        )

    def _action_btn_style(self, active: bool = False) -> str:
        """Style for action-row helper buttons (_btn_source, _btn_para_num, etc.).

        When active=True the button shows a *mild lift* (slightly lighter
        border/background) rather than a high-emphasis CTA fill.  Strong
        accent colours are reserved for true mode buttons (_mode_btn_style).
        """
        s = self._skin
        if active:
            # Mild active lift: step up border opacity, slightly lighter bg.
            # We deliberately avoid btn_active_bg here so expand-buttons don't
            # look like primary CTA buttons when open.
            return self._solid_button_style(
                background=s['btn_hover'],
                color=s['btn_fg'],
                border=s.get('btn_active_border', s['btn_border']),
                hover_background=s['btn_hover'],
                padding=_BTN_PADDING,
                font_size=int(s.get('button_font_size_action', 12)),
                font_weight=int(s.get('button_font_weight', 600)),
                radius=_BTN_RADIUS,
            )
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s['btn_fg'],
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            padding=_BTN_PADDING,
            font_size=int(s.get('button_font_size_action', 12)),
            font_weight=int(s.get('button_font_weight', 600)),
            radius=_BTN_RADIUS,
        )

    def _small_toolbar_btn(self, label: str, tip: str, callback) -> QPushButton:
        btn = QPushButton(label)
        btn.setToolTip(tip)
        btn.setFixedSize(_SMALL_TOOLBAR_BUTTON_W, _TOOLBAR_BUTTON_H)
        btn.setStyleSheet(self._small_toolbar_btn_style())
        btn.clicked.connect(callback)
        return btn

    def _small_toolbar_btn_style(self) -> str:
        """Compact toolbar buttons (overlay A+/A-/✕).
        Uses the shared neutral base radius and border weight.
        """
        s = self._skin
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s['btn_fg'],
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            padding='0 6px',
            font_size=int(s.get('button_font_size_compact', 12)),
            font_weight=600,
            radius=_BTN_RADIUS,
        )

    def _mode_btn_style(self, active: bool) -> str:
        """Style for true mode-toggle buttons (_btn_box_mode_cycle, _btn_ai_mode).

        Active state uses the highest-contrast accent (blue/green) to signal
        the current operating mode.  This is the only non-primary button
        category that uses a strong filled active treatment.
        """
        s = self._skin
        if active:
            return self._solid_button_style(
                background=s['btn_mode_active_bg'],
                color='white',
                border=s['btn_mode_active_border'],
                hover_background=s['btn_mode_active_hover'],
                padding=_BTN_PADDING,
                font_size=int(s.get('button_font_size_toolbar', 12)),
                font_weight=600,
                radius=_BTN_RADIUS,
            )
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s['btn_fg'],
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            padding=_BTN_PADDING,
            font_size=int(s.get('button_font_size_toolbar', 12)),
            font_weight=500,
            radius=_BTN_RADIUS,
        )

    def _lang_btn_style(self) -> str:
        """Language selector dropdown buttons.
        Neutral styling consistent with other toolbar helpers.
        """
        s = self._skin
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s['btn_fg'],
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            hover_color=s.get('text', 'white'),
            padding='0 10px',
            font_size=int(s.get('button_font_size_toolbar', 12)),
            radius=_BTN_RADIUS,
        )

    def _icon_btn_style(self) -> str:
        """Top-toolbar icon-only buttons (copy, history, settings, minimize, close).

        These stay fully transparent by default (ghost) and show only a faint
        background on hover — intentionally *more subtle* than action-row
        buttons.  We share the same border-radius constant for pixel consistency.
        """
        s = self._skin
        muted = s.get('text_muted', 'rgba(166,170,186,204)')
        r = _BTN_RADIUS
        return f'''
            QPushButton {{ background: transparent; color: {muted};
                          border: none; font-size: 13px; border-radius: {r}px; }}
            QPushButton:hover {{ color: {s.get('text', 'white')}; background: rgba(255,255,255,12);
                                border-radius: {r}px; }}
            QPushButton:pressed {{ background: rgba(255,255,255,18); border-radius: {r}px; }}
        '''

    def _icon_btn(self, icon: str, tip: str, cb) -> QPushButton:
        b = QPushButton(icon)
        b.setToolTip(tip)
        b.setFixedSize(_TOOLBAR_ICON_W, _TOOLBAR_BUTTON_H)
        b.setStyleSheet(self._icon_btn_style())
        b.clicked.connect(cb)
        return b

    def _action_btn(self, label: str, tip: str, cb) -> QPushButton:
        b = QPushButton(label)
        b.setToolTip(tip)
        b.setFixedHeight(_TOOLBAR_BUTTON_H)
        b.setStyleSheet(self._action_btn_style(False))
        b.clicked.connect(cb)
        return b

    # ── 线条图标工厂 ──────────────────────────────────────────────

    def _muted_qcolor(self) -> QColor:
        raw = self._skin.get('button_icon_stroke', self._skin.get('text_muted', ''))
        if raw.startswith('#'):
            return QColor(raw)
        m = re.match(r'rgba?\s*\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s]+(\d+))?\s*\)', raw)
        if m:
            a = int(m.group(4)) if m.group(4) else 255
            return QColor(int(m.group(1)), int(m.group(2)), int(m.group(3)), a)
        return QColor(185, 192, 215, 200)

    def _mk_icon(self, draw_fn, size: int = 14) -> QIcon:
        color = self._muted_qcolor()
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(color, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        draw_fn(p, size)
        p.end()
        return QIcon(pm)

    @staticmethod
    def _draw_copy(p: QPainter, s: int):
        # 后页（右上）
        p.drawRect(int(s*0.32), int(s*0.02), int(s*0.60), int(s*0.65))
        # 前页（左下）
        p.drawRect(int(s*0.08), int(s*0.33), int(s*0.60), int(s*0.65))

    @staticmethod
    def _draw_broom(p: QPainter, s: int):
        # 扫帚柄（对角线）
        p.drawLine(int(s*0.82), int(s*0.05), int(s*0.38), int(s*0.52))
        # 绑扎处（横杆）
        p.drawLine(int(s*0.18), int(s*0.56), int(s*0.52), int(s*0.44))
        # 三根刷毛
        p.drawLine(int(s*0.18), int(s*0.56), int(s*0.04), int(s*0.95))
        p.drawLine(int(s*0.32), int(s*0.52), int(s*0.30), int(s*0.95))
        p.drawLine(int(s*0.52), int(s*0.44), int(s*0.60), int(s*0.92))

    @staticmethod
    def _draw_clock(p: QPainter, s: int):
        import math
        r = int(s * 0.41)
        cx, cy = s // 2, s // 2
        p.drawEllipse(cx - r, cy - r, 2*r, 2*r)
        # 4 个刻度（12/3/6/9 点位置）
        tick_outer = r
        tick_inner = int(r * 0.72)
        for angle_deg in (0, 90, 180, 270):
            rad = math.radians(angle_deg - 90)
            x1 = cx + int(tick_outer * math.cos(rad))
            y1 = cy + int(tick_outer * math.sin(rad))
            x2 = cx + int(tick_inner * math.cos(rad))
            y2 = cy + int(tick_inner * math.sin(rad))
            p.drawLine(x1, y1, x2, y2)
        # 时针（指向 10 点）
        p.drawLine(cx, cy, cx - int(r*0.45), cy - int(r*0.55))
        # 分针（指向 12 点）
        p.drawLine(cx, cy, cx, cy - int(r*0.72))

    @staticmethod
    def _draw_square(p: QPainter, s: int):
        # 绘制填充的正方形（用于停止/清空按钮）
        margin = int(s * 0.25)
        p.setBrush(p.pen().color())  # 使用当前画笔颜色填充
        p.drawRect(margin, margin, s - 2*margin, s - 2*margin)

    @staticmethod
    def _draw_paragraph(p: QPainter, s: int):
        line_x = int(s * 0.18)
        line_w = int(s * 0.52)
        for idx, y in enumerate((0.20, 0.44, 0.68)):
            p.drawLine(line_x, int(s * y), line_x + line_w, int(s * y))
            if idx < 2:
                p.drawLine(int(s * 0.82), int(s * y), int(s * 0.92), int(s * y))

    def _tb_scroll_style(self) -> str:
        s = self._skin
        return f'''
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:horizontal {{
                background: {s.get('scrollbar_bg', 'rgba(255,255,255,8)')}; height: 4px; border-radius: 2px; margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {s.get('scrollbar_handle', 'rgba(255,255,255,50)')}; border-radius: 2px; min-width: 20px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        '''

    def _translation_text_style(self) -> str:
        s = self._skin
        sb = make_scrollbar_qss(s)
        return f'''
            QTextEdit {{
                color: {s.get('text', '#f0f0f0')}; background: transparent; border: none;
                padding: 0; margin: 0;
            }}
            {sb}
        '''

    def _source_editor_style(self) -> str:
        s = self._skin
        sb = make_scrollbar_qss(s)
        bg = s.get('source_editor_bg', 'rgba(255,255,255,6)')
        border = s.get('source_editor_border', 'rgba(255,255,255,18)')
        text = s.get('source_editor_text', 'rgba(225,225,235,230)')
        return f'''
            QTextEdit {{
                color: {text}; background: {bg};
                border: 1px solid {border}; border-radius: 6px;
                padding: 6px;
            }}
            {sb}
        '''

    def _explain_text_style(self) -> str:
        s = self._skin
        sb = make_scrollbar_qss(s)
        bg = s.get('explain_bg', 'rgba(255,240,100,10)')
        text = s.get('explain_text', 'rgba(230,220,140,230)')
        return f'''
            QTextEdit {{
                color: {text}; font-size: 12px;
                background: {bg}; border: none;
                padding: 4px; border-radius: 4px;
            }}
            {sb}
        '''

    def _update_lang_button_widths(self):
        for btn in (self._btn_src_lang, self._btn_tgt_lang):
            min_width = max(btn.sizeHint().width(), btn.fontMetrics().horizontalAdvance(btn.text()) + 20)
            btn.setMinimumWidth(min_width)

    def _stop_clear_btn_style(self, busy: bool) -> str:
        s = self._skin
        if busy:
            return self._solid_button_style(
                background=s['btn_stop_bg'],
                color='white',
                border=s['btn_stop_border'],
                hover_background=s['btn_stop_hover'],
                padding='0 8px',
                font_size=int(s.get('button_font_size_toolbar', 12)),
                font_weight=700,
            )
        return self._solid_button_style(
            background=s['btn_bg'],
            color=s['btn_fg'],
            border=s['btn_border'],
            hover_background=s['btn_hover'],
            padding='0 8px',
            font_size=int(s.get('button_font_size_toolbar', 12)),
            font_weight=600,
        )

    def _refresh_toolbar_layout(self):
        self._update_lang_button_widths()
        self._tb_widget.adjustSize()
        self._tb_widget.setFixedSize(self._tb_widget.sizeHint())

    def _detach_overlay_controls(self):
        for name in ('_btn_overlay', '_btn_overlay_font_down', '_btn_overlay_font_up', '_btn_overlay_close'):
            if not hasattr(self, name):
                continue
            btn = getattr(self, name)
            self._tb_layout.removeWidget(btn)
            btn.hide()
            btn.setParent(None)
            delattr(self, name)

    def set_stop_clear_busy(self, busy: bool):
        self._translation_busy = busy
        self._btn_stop_clear.setToolTip('停止或清空当前翻译内容')
        self._btn_stop_clear.setText('')
        self._btn_stop_clear.setIcon(self._mk_icon(self._draw_square))
        self._btn_stop_clear.setIconSize(QSize(14, 14))
        self._btn_stop_clear.setStyleSheet(self._stop_clear_btn_style(busy))

    # ── 语言下拉菜单 ──────────────────────────────────────────────

    def _show_src_lang_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(make_menu_qss(self._skin))
        current = self.settings.get('source_language', 'auto')
        for code, short, full in SOURCE_LANGS:
            act = QAction(f'{short}  {full}', self)
            act.setData(code)
            act.setCheckable(True)
            act.setChecked(code == current)
            menu.addAction(act)
        chosen = menu.exec_(self._btn_src_lang.mapToGlobal(
            self._btn_src_lang.rect().bottomLeft()))
        if chosen:
            code = chosen.data()
            short = next(s for c, s, _ in SOURCE_LANGS if c == code)
            self.settings.set('source_language', code)
            self._btn_src_lang.setText(f'{short} ▾')
            self._refresh_toolbar_layout()
            self.source_language_changed.emit(code)

    def _show_tgt_lang_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(make_menu_qss(self._skin))
        current = self.settings.get('target_language', 'zh-CN')
        for code, short, full in TARGET_LANGS:
            act = QAction(f'{short}  {full}', self)
            act.setData(code)
            act.setCheckable(True)
            act.setChecked(code == current)
            menu.addAction(act)
        chosen = menu.exec_(self._btn_tgt_lang.mapToGlobal(
            self._btn_tgt_lang.rect().bottomLeft()))
        if chosen:
            code = chosen.data()
            short = next(s for c, s, _ in TARGET_LANGS if c == code)
            self.settings.set('target_language', code)
            self._btn_tgt_lang.setText(f'{short} ▾')
            self._refresh_toolbar_layout()
            self.target_language_changed.emit(code)

    # ── 模式切换 ──────────────────────────────────────────────────

    def _set_active_mode_btn(self, key: str):
        cycle_active = key in BOX_MODE_ORDER
        self._btn_box_mode_cycle.setChecked(cycle_active)
        self._btn_box_mode_cycle.setStyleSheet(self._mode_btn_style(cycle_active))
        if cycle_active:
            self._btn_box_mode_cycle.setText(BOX_MODE_META[key][0])

        ai_active = key == 'ai'
        self._btn_ai_mode.setChecked(ai_active)
        self._btn_ai_mode.setStyleSheet(self._mode_btn_style(ai_active))

    def _on_mode_btn_click(self, key: str):
        # 切换到 AI 框前记录当前模式，以便退出时恢复
        if key == 'ai' and self._box_mode != 'ai':
            self._prev_box_mode = self._box_mode
        self._box_mode = key
        self._set_active_mode_btn(key)
        self._toggle.setVisible(key != 'temp')
        self._refresh_toolbar_layout()
        self.box_mode_changed.emit(key)
        self._smart_adjust()

    def _cycle_box_mode(self):
        # AI 框模式特殊处理：点击返回到进入 AI 框之前的模式
        if self._box_mode == 'ai':
            prev_mode = getattr(self, '_prev_box_mode', 'fixed')
            self._on_mode_btn_click(prev_mode)
            return

        try:
            index = BOX_MODE_ORDER.index(self._box_mode)
        except ValueError:
            index = -1
        self._on_mode_btn_click(BOX_MODE_ORDER[(index + 1) % len(BOX_MODE_ORDER)])

    def _on_toggle_changed(self, is_auto: bool):
        self._translate_mode = 'auto' if is_auto else 'manual'
        self.translate_mode_changed.emit(self._translate_mode)

    # ── public API ────────────────────────────────────────────────

    def _smart_adjust(self):
        """调整窗口大小适配内容；若用户已手动调整过大小则保持不变。"""
        if not self._manual_size:
            self._in_adjust = True
            self.adjustSize()
            self._in_adjust = False

    def current_source_text(self) -> str:
        return self._source_editor.toPlainText().strip()

    def _panel_size_hint_height(self, panel: QWidget) -> int:
        layout = panel.layout()
        if layout is not None:
            layout.activate()
            return layout.sizeHint().height()
        return panel.sizeHint().height()

    def _sync_text_edit_height(self, widget: QTextEdit, *, min_height: int, max_height: int) -> int:
        viewport_width = widget.viewport().width()
        if viewport_width <= 0:
            viewport_width = max(120, self.width() - 40)
        doc = widget.document().clone()
        doc.setTextWidth(viewport_width)
        doc.adjustSize()
        target = int(doc.size().height()) + 10
        del doc
        target = max(min_height, min(max_height, target))
        return target

    def _preferred_translation_panel_height(self) -> int:
        return self._sync_text_edit_height(self._lbl_translation, min_height=72, max_height=9999)

    def _preferred_source_panel_height(self) -> int:
        return self._sync_text_edit_height(self._source_editor, min_height=96, max_height=9999)

    def _preferred_explain_panel_height(self) -> int:
        height = 0
        if self._explain_loading_label.isVisible():
            height += self._explain_loading_label.sizeHint().height()
        if self._explain_text.isVisible():
            if height:
                height += self._explain_panel.layout().spacing()
            height += self._sync_text_edit_height(self._explain_text, min_height=72, max_height=140)
        return max(96, height)

    def _content_splitter_index(self, panel: QWidget) -> int:
        for index in range(self._content_splitter.count()):
            if self._content_splitter.widget(index) is panel:
                return index
        return -1

    def _panel_in_content_splitter(self, panel: QWidget) -> bool:
        return self._content_splitter_index(panel) >= 0

    def _insert_content_panel(self, panel: QWidget, index: int):
        current_index = self._content_splitter_index(panel)
        if current_index >= 0:
            if current_index != index:
                panel.setParent(None)
                self._content_splitter.insertWidget(index, panel)
        else:
            self._content_splitter.insertWidget(index, panel)
        panel.setVisible(True)

    def _remove_content_panel(self, panel: QWidget):
        if self._panel_in_content_splitter(panel):
            panel.setVisible(False)
            panel.setParent(None)

    def _current_panel_height(self, panel: QWidget, preferred_height: int) -> int:
        if self._panel_in_content_splitter(panel) and panel.height() > 0:
            return panel.height()
        return preferred_height

    def _apply_splitter_sizes(self, *, translation_height=None, source_height=None, explain_height=None):
        if translation_height is None:
            translation_height = self._current_panel_height(
                self._translation_panel,
                self._preferred_translation_panel_height(),
            )

        if source_height is None:
            source_height = (
                self._current_panel_height(self._source_panel, self._preferred_source_panel_height())
                if self._panel_in_content_splitter(self._source_panel)
                else 0
            )
        sizes = [max(72, int(translation_height))]
        if self._panel_in_content_splitter(self._source_panel):
            sizes.append(max(96, int(source_height)))

        if self._panel_in_content_splitter(self._explain_panel):
            if explain_height is None:
                explain_height = self._current_panel_height(
                    self._explain_panel,
                    self._preferred_explain_panel_height(),
                )
            sizes.append(max(96, int(explain_height)))

        self._content_splitter.setSizes(sizes)

    def _update_translation_height(self):
        self._preferred_translation_panel_height()

    def _update_explain_height(self):
        self._preferred_explain_panel_height()

    def _set_source_text(self, text: str, *, mark_clean: bool):
        self._syncing_source_editor = True
        self._source_editor.setPlainText(text or '')
        self._syncing_source_editor = False
        if mark_clean:
            self._synced_source_text = (text or '').strip()
        self._source_dirty = self.current_source_text() != self._synced_source_text
        self._update_retranslate_button()

    def _update_retranslate_button(self):
        current_text = self.current_source_text()
        self._btn_retranslate.setEnabled(
            bool(current_text) and current_text != self._synced_source_text
        )

    def _resize_preserving_top(self, target_height: int):
        target_height = max(self.minimumHeight(), target_height)
        if target_height == self.height():
            return
        current_pos = self.pos()
        self._in_adjust = True
        self.resize(self.width(), target_height)
        self._in_adjust = False
        self.move(current_pos)

    def _toggle_panel(self, panel: QWidget, visible: bool):
        preferred_height = (
            self._preferred_source_panel_height()
            if panel is self._source_panel
            else self._preferred_explain_panel_height()
        )
        translation_height = self._current_panel_height(
            self._translation_panel,
            self._preferred_translation_panel_height(),
        )
        source_height = (
            self._current_panel_height(self._source_panel, self._preferred_source_panel_height())
            if self._panel_in_content_splitter(self._source_panel)
            else 0
        )
        explain_height = (
            self._current_panel_height(self._explain_panel, self._preferred_explain_panel_height())
            if self._panel_in_content_splitter(self._explain_panel)
            else 0
        )

        if visible:
            already_visible = self._panel_in_content_splitter(panel)
            if panel is self._source_panel:
                self._insert_content_panel(self._source_panel, 1)
                source_height = max(source_height, preferred_height)
            else:
                explain_index = 2 if self._panel_in_content_splitter(self._source_panel) else 1
                self._insert_content_panel(self._explain_panel, explain_index)
                explain_height = max(explain_height, preferred_height)
            if not already_visible:
                self._resize_preserving_top(self.height() + preferred_height + self._content_splitter.handleWidth())
        else:
            if not self._panel_in_content_splitter(panel):
                return
            current_height = self._current_panel_height(panel, preferred_height)
            self._remove_content_panel(panel)
            if panel is self._source_panel:
                source_height = 0
            else:
                explain_height = 0
            self._resize_preserving_top(
                max(self.minimumHeight(), self.height() - current_height - self._content_splitter.handleWidth())
            )

        self._apply_splitter_sizes(
            translation_height=translation_height,
            source_height=source_height,
            explain_height=explain_height,
        )

    def _update_source_button(self):
        self._btn_source.setText('原文 ▲' if self._source_expanded else '原文 ▼')
        self._btn_source.setStyleSheet(self._action_btn_style(self._source_expanded))

    def _update_ai_button(self):
        self._btn_ai.set_arrow(self._explain_expanded)

    def _on_source_text_changed(self):
        if not self._syncing_source_editor:
            self._source_dirty = self.current_source_text() != self._synced_source_text
        self._update_retranslate_button()

    def _save_geometry(self):
        """将当前位置和尺寸写入 settings，供"上次位置"选项使用。"""
        self.settings.set('result_bar_last_x', self.x())
        self.settings.set('result_bar_last_y', self.y())
        self.settings.set('result_bar_last_w', self.width())
        self.settings.set('result_bar_last_h', self.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._in_adjust:
            # 用户通过拖拽手柄改变了大小
            self._manual_size = True
            self._save_timer.start()
            # 重新分配：翻译/原文贴内容，AI 科普填充剩余
            self._apply_splitter_sizes()

    def showEvent(self, event):
        super().showEvent(event)
        # Recompute once the widget is visible so the toolbar width reflects
        # the final visible controls and avoids an initial stale geometry.
        self._refresh_toolbar_layout()
        self._update_translation_height()
        self._update_explain_height()
        self._apply_splitter_sizes()

    def enterEvent(self, event):
        self.raise_()
        super().enterEvent(event)

    def refresh_opacity(self):
        self._apply_opacity()

    def apply_skin(self):
        """皮肤改变后重新应用所有 UI 样式。"""
        s = self._skin
        # 容器
        self._apply_opacity()
        # 分隔线 & 分割器
        self._sep.setStyleSheet(f'background: {s.get("sep_color", "rgba(255,255,255,18)")};')
        self._content_splitter.setStyleSheet(f'''
            QSplitter::handle:vertical {{
                background: {s.get("sep_color", "rgba(255,255,255,18)")};
                margin: 1px 0;
            }}
        ''')
        # 工具栏滚动区
        self._tb_scroll.setStyleSheet(self._tb_scroll_style())
        # 播放按钮
        self._btn_play.setStyleSheet(self._play_btn_style())
        self._btn_reset_size.setStyleSheet(self._neutral_small_btn_style())
        self._btn_reset_size.set_icon_color(self._muted_qcolor())
        # 模式按钮（从当前状态重建）
        self._set_active_mode_btn(self._box_mode)
        # 语言按钮
        self._btn_src_lang.setStyleSheet(self._lang_btn_style())
        self._btn_tgt_lang.setStyleSheet(self._lang_btn_style())
        # 停止/清空按钮
        self._btn_stop_clear.setStyleSheet(self._stop_clear_btn_style(self._translation_busy))
        # 各种动作按钮
        for btn in (self._btn_source, self._btn_copy_src,
                    self._btn_retranslate, self._btn_para_num):
            btn.setStyleSheet(self._action_btn_style(False))
        self._btn_source.setStyleSheet(self._action_btn_style(self._source_expanded))
        self._btn_para_num.setStyleSheet(self._action_btn_style(self._show_para_numbers))
        # 小工具栏按钮（覆盖相关）
        for name in ('_btn_overlay_font_down', '_btn_overlay_font_up', '_btn_overlay_close',
                     '_btn_overlay'):
            btn = getattr(self, name, None)
            if btn is not None:
                btn.setStyleSheet(self._small_toolbar_btn_style())
        # 图标按钮
        for btn in (self._btn_copy_trans, self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close):
            btn.setStyleSheet(self._icon_btn_style())
        # 线条图标随皮肤重绘
        self._btn_copy_trans.setIcon(self._mk_icon(self._draw_copy))
        self._btn_copy_src.setIcon(self._mk_icon(self._draw_copy))
        self._btn_history.setIcon(self._mk_icon(self._draw_clock, 18))
        self._btn_history.setIconSize(QSize(18, 18))
        self._btn_para_num.setIcon(self._mk_icon(self._draw_paragraph))
        self._btn_stop_clear.setIcon(self._mk_icon(self._draw_square))
        self._btn_stop_clear.setIconSize(QSize(14, 14))
        # TranslateToggle
        self._toggle.set_skin(s)
        # SplitButton (AI科普)
        self._btn_ai.set_skin(s)
        # 文本区域
        self._lbl_translation.setStyleSheet(self._translation_text_style())
        self._source_editor.setStyleSheet(self._source_editor_style())
        self._explain_text.setStyleSheet(self._explain_text_style())
        # 辅助标签
        muted = s.get('text_muted', 'rgba(160,160,185,190)')
        self._resize_hint_lbl.setStyleSheet(f'color: {muted}; font-size: 10px; padding: 0;')

    def apply_settings(self):
        """设置保存后立刻应用位置和大小。"""
        size_pref = self.settings.get('result_bar_size', 'default')
        if size_pref == 'default':
            self._manual_size = False
            self.resize(DEFAULT_W, DEFAULT_H)
            self._manual_size = True
        self.set_overlay_mode(self.settings.get('overlay_default_mode', 'off'))
        self._position_window()

    def mark_hidden_to_tray(self, hidden: bool):
        self._hidden_to_tray = hidden

    def update_mode_tooltips(self, hk_temp: str, hk_fixed: str, hk_multi: str, hk_ai: str = 'alt+4'):
        hints = {
            'temp':  f'临时翻译：框选后立即翻译，N秒后消失  [{hk_temp}]',
            'fixed': f'固定翻译：框保留，可手动或自动翻译  [{hk_fixed}]',
            'multi': f'多框翻译：可放置多个翻译框  [{hk_multi}]',
            'ai':    f'AI框选：框选后直接AI科普，无需翻译  [{hk_ai}]',
        }
        for key, btn in self._mode_btns.items():
            btn.setToolTip(hints.get(key, ''))

    def show_multi_results(self, results: list):
        """多框模式：把各框译文合并展示，用分隔线隔开。"""
        if not results:
            self._lbl_translation.setPlainText('等待翻译...')
            self._lbl_backend.setText('')
            self._smart_adjust()
            return
        parts = []
        for i, r in enumerate(results, 1):
            trans   = r.get('translated', '')
            backend = r.get('backend', '')
            parts.append(f'[{i}] {trans}  \u3000{backend}')
        self._lbl_translation.setPlainText('\n─────\n'.join(parts))
        self._lbl_backend.setText('')
        if not self.isVisible() and not self._hidden_to_tray:
            self.show()
        self._smart_adjust()

    def show_explain_loading(self):
        """AI科普加载中：在原文按钮下方显示提示，不覆盖译文区。"""
        self._lbl_explain_loading.setVisible(True)
        self._smart_adjust()

    def show_explain(self, text: str):
        self._lbl_explain_loading.setVisible(False)
        self._lbl_explain.setPlainText(text)
        self._lbl_explain.setVisible(True)
        self._btn_explain_hdr.setText('💡 AI科普 ▲')
        self._btn_explain_hdr.setVisible(True)
        self._smart_adjust()

    def show_ocr_text(self, text: str):
        """OCR 识别完成后立即填入原文；翻译期间用户可点「原文」查看。"""
        self._set_source_text(text, mark_clean=True)

    def show_loading(self, msg: str = '翻译中...'):
        self._lbl_translation.setPlainText(msg)
        self._update_translation_height()
        self._lbl_backend.setText('')
        self._apply_splitter_sizes()
        if not self.isVisible() and not self._hidden_to_tray:
            self.show()

    def show_error(self, msg: str):
        self._lbl_translation.setPlainText(f'⚠ {msg}')
        if not self.isVisible() and not self._hidden_to_tray:
            self.show()

    # ── private slots ─────────────────────────────────────────────

    def _toggle_source(self):
        self._source_expanded = not self._source_expanded
        self._lbl_source.setVisible(self._source_expanded)
        self._btn_source.setText('原文 ▲' if self._source_expanded else '原文 ▼')
        self._smart_adjust()

    def _toggle_explain_section(self):
        vis = not self._lbl_explain.isVisible()
        self._lbl_explain.setVisible(vis)
        self._btn_explain_hdr.setText('💡 AI科普 ▲' if vis else '💡 AI科普 ▼')
        self._smart_adjust()

    def _copy(self):
        if self._current_result:
            QApplication.clipboard().setText(self._current_result.get('translated', ''))

    def _copy_source(self):
        if self._current_result:
            QApplication.clipboard().setText(self._current_result.get('original', ''))

    def _reset_size(self):
        self._manual_size = False
        self.resize(DEFAULT_W, DEFAULT_H)
        self._manual_size = True
        self._apply_splitter_sizes()

    def _refresh_overlay_button(self):
        if not hasattr(self, '_btn_overlay'):
            return
        self._btn_overlay.setToolTip(OVERLAY_MODE_META.get(self._overlay_mode, OVERLAY_MODE_META['off']))

        # 控制覆盖相关按钮的显示
        overlay_active = self._overlay_mode != 'off'
        if hasattr(self, '_btn_overlay_font_down'):
            self._btn_overlay_font_down.setVisible(overlay_active)
        if hasattr(self, '_btn_overlay_font_up'):
            self._btn_overlay_font_up.setVisible(overlay_active)
        if hasattr(self, '_btn_overlay_close'):
            self._btn_overlay_close.setVisible(overlay_active)

        if self._overlay_mode == 'off':
            self._btn_overlay.setStyleSheet('''
                QPushButton { background: transparent; color: rgba(160,160,180,200);
                              border: none; font-size: 12px; }
                QPushButton:hover { color: white; background: rgba(255,255,255,15);
                                    border-radius: 3px; }
            ''')
            return
        self._btn_overlay.setStyleSheet('''
            QPushButton { background: rgba(80,140,255,180); color: white;
                          border: none; font-size: 12px; border-radius: 3px; }
            QPushButton:hover { color: white; background: rgba(100,160,255,200); }
        ''')

    def set_overlay_mode(self, mode: str, emit_signal: bool = False):
        if mode not in OVERLAY_MODE_ORDER:
            mode = 'off'
        self._overlay_mode = mode
        self._refresh_overlay_button()
        if emit_signal:
            text = ''
            if self._current_result:
                text = self._current_result.get('translated', '')
            self.overlay_requested.emit(self._overlay_mode, text)

    def _adjust_overlay_font_delta(self, delta: int):
        value = int(self.settings.get('overlay_font_delta', 0)) + delta
        self.settings.set('overlay_font_delta', value)
        self.overlay_font_delta_changed.emit(value)

    def _on_overlay(self):
        index = OVERLAY_MODE_ORDER.index(self._overlay_mode)
        self.set_overlay_mode(OVERLAY_MODE_ORDER[(index + 1) % len(OVERLAY_MODE_ORDER)])
        text = ''
        if self._current_result:
            text = self._current_result.get('translated', '')
        self.overlay_requested.emit(self._overlay_mode, text)

    def clear_current_content(self):
        self._current_result = None
        self._source_expanded = False
        self._explain_expanded = False
        self._source_dirty = False
        self._synced_source_text = ''
        self._lbl_translation.setPlainText('等待翻译...')
        self._lbl_backend.setText('')
        self._set_source_text('', mark_clean=True)
        self._update_translation_height()
        self._toggle_panel(self._source_panel, False)
        self._update_source_button()
        self._explain_loading_label.setVisible(False)
        self._explain_text.clear()
        self._explain_text.setVisible(False)
        self._update_explain_height()
        self._toggle_panel(self._explain_panel, False)
        self._update_ai_button()
        self._apply_splitter_sizes()
        self._smart_adjust()

    def show_result(self, result: dict):
        self._current_result = result
        self._explain_loading_label.setVisible(False)
        self._explain_text.clear()
        self._explain_text.setVisible(False)
        if self._explain_expanded or self._explain_panel.isVisible():
            self._toggle_panel(self._explain_panel, False)
        self._explain_expanded = False
        self._update_ai_button()

        paras = result.get('paragraphs', [])
        if self._para_mode and paras:
            self._lbl_translation.setPlainText(self._format_para_text(paras, 'translation'))
            if not self._source_dirty or not self.current_source_text():
                self._set_source_text(self._format_para_text(paras, 'text'), mark_clean=True)
        elif paras:
            self._lbl_translation.setPlainText('\n'.join(p['translation'] for p in paras))
            if not self._source_dirty or not self.current_source_text():
                self._set_source_text('\n'.join(p['text'] for p in paras), mark_clean=True)
        else:
            self._lbl_translation.setPlainText(result.get('translated', ''))
            if not self._source_dirty or not self.current_source_text():
                self._set_source_text(result.get('original', ''), mark_clean=True)
        self._update_translation_height()
        if self._source_expanded:
            self._toggle_panel(self._source_panel, True)
        else:
            self._apply_splitter_sizes()
        self._lbl_backend.setText(f"来源: {result.get('backend', '')}")

        src = result.get('source_lang', '')
        if src:
            src_short = next((s for c, s, _ in SOURCE_LANGS
                              if c == src.lower() or c == src.lower().split('-')[0]), src.upper())
            self._btn_src_lang.setText(f'{src_short} ▾')
            self._refresh_toolbar_layout()

        if not self.isVisible() and not self._hidden_to_tray:
            self.show()
        self._smart_adjust()

    def show_explain_loading(self):
        self._explain_expanded = True
        self._explain_loading_label.setVisible(True)
        self._explain_text.clear()
        self._explain_text.setVisible(False)
        self._update_explain_height()
        self._toggle_panel(self._explain_panel, True)
        self._update_ai_button()

    def show_explain(self, text: str):
        self._explain_expanded = True
        self._explain_loading_label.setVisible(False)
        self._explain_text.setPlainText(text)
        self._explain_text.setVisible(True)
        self._update_explain_height()
        self._toggle_panel(self._explain_panel, True)
        self._update_ai_button()

    def _format_para_text(self, paragraphs: list, key: str) -> str:
        if self._show_para_numbers:
            return "\n".join(f"[{i+1}] {p[key]}" for i, p in enumerate(paragraphs))
        return "\n".join(p[key] for p in paragraphs)

    def _toggle_para_numbers(self):
        self._show_para_numbers = not self._show_para_numbers
        self._btn_para_num.setStyleSheet(self._action_btn_style(self._show_para_numbers))
        if self._current_result:
            self.show_result(self._current_result)

    def sync_para_mode_from_settings(self):
        self._para_mode = bool(self.settings.get('para_split_enabled', False))
        if self._current_result:
            self.show_result(self._current_result)

    def _toggle_source(self):
        self._source_expanded = not self._source_expanded
        self._toggle_panel(self._source_panel, self._source_expanded)
        self._update_source_button()

    def _toggle_explain_section(self):
        loading_visible = not self._explain_loading_label.isHidden()
        has_text = bool(self._explain_text.toPlainText())
        vis = not self._explain_expanded
        self._explain_expanded = vis
        self._explain_loading_label.setVisible(vis and loading_visible and not has_text)
        self._explain_text.setVisible(vis and has_text)
        self._update_explain_height()
        self._toggle_panel(self._explain_panel, vis)
        self._update_ai_button()

    def _copy_source(self):
        text = self.current_source_text()
        if text:
            QApplication.clipboard().setText(text)

    def _on_retranslate(self):
        text = self.current_source_text()
        if not text or text == self._synced_source_text:
            return
        self._synced_source_text = text
        self._source_dirty = False
        self._update_retranslate_button()
        self.retranslate_requested.emit(text)

    def _on_explain(self):
        text = self.current_source_text()
        if not text and self._current_result is None:
            self.start_selection_requested.emit()
            return
        if text:
            self.show_explain_loading()
            self.explain_requested.emit(text)

    def _toggle_minimize(self):
        if not self._minimized:
            self._minimized = True
            self._btn_minimize.setText('□')
            self._pre_minimize_size = self.size()
            self._pre_minimize_pos  = self.pos()
            self.hide()
            # 用标准 QMainWindow 代理任务栏图标，天然支持最小化/恢复
            if not hasattr(self, '_proxy') or self._proxy is None:
                self._proxy = _MinimizeProxy(self)
            self._proxy.showMinimized()
        else:
            self._restore_from_taskbar()

    def _restore_from_taskbar(self):
        self._minimized = False
        self._btn_minimize.setText('─')
        if hasattr(self, '_proxy') and self._proxy:
            self._proxy.hide()
        if hasattr(self, '_pre_minimize_size'):
            self._in_adjust = True
            self.resize(self._pre_minimize_size)
            self._in_adjust = False
        if hasattr(self, '_pre_minimize_pos'):
            self.move(self._pre_minimize_pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def changeEvent(self, event):
        super().changeEvent(event)

    # ── drag / resize ─────────────────────────────────────────────

    _RESIZE_ZONE = 20  # 距右下角多少 px 内视为 resize 区域

    def _near_resize_corner(self, pos) -> bool:
        return (pos.x() >= self.width() - self._RESIZE_ZONE and
                pos.y() >= self.height() - self._RESIZE_ZONE)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._near_resize_corner(event.pos()):
                self._resizing = True
                self._resize_start_global = event.globalPos()
                self._resize_start_size = self.size()
                self._drag_pos = QPoint()
            else:
                self._resizing = False
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self._resizing:
                delta = event.globalPos() - self._resize_start_global
                new_w = max(self.minimumWidth(),  self._resize_start_size.width()  + delta.x())
                new_h = max(self.minimumHeight(), self._resize_start_size.height() + delta.y())
                self.resize(new_w, new_h)
            elif not self._drag_pos.isNull():
                self.move(event.globalPos() - self._drag_pos)
                self._save_timer.start()
        else:
            # 悬停时在调整区域显示对角线光标
            if self._near_resize_corner(event.pos()):
                self.setCursor(Qt.SizeFDiagCursor)
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resizing = False

    def apply_settings(self):
        size_pref = self.settings.get('result_bar_size', 'default')
        if size_pref == 'default':
            self._manual_size = False
            self.resize(DEFAULT_W, DEFAULT_H)
            self._manual_size = True
        self.set_overlay_mode(self.settings.get('overlay_default_mode', 'off'))
        self._position_window()

    def update_mode_tooltips(self, hk_temp: str, hk_fixed: str, hk_multi: str, hk_ai: str = 'alt+4'):
        current_label = BOX_MODE_META.get(self._box_mode, BOX_MODE_META['temp'])[0]
        self._btn_box_mode_cycle.setToolTip(
            f'框模式循环切换（当前：{current_label}）'
            f' [固定 {hk_fixed} / 临时 {hk_temp} / 多框 {hk_multi}]'
        )
        self._btn_ai_mode.setToolTip(f'{BOX_MODE_META["ai"][1]}  [{hk_ai}]')
