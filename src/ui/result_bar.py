import logging
from PyQt5.QtWidgets import (QWidget, QMainWindow, QLabel, QPushButton,
                              QHBoxLayout, QVBoxLayout, QApplication,
                              QSizePolicy, QMenu, QAction, QTextEdit,
                              QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QPoint, QSize, pyqtSignal, QTimer, QEvent
from PyQt5.QtGui import QFont, QPainter, QColor, QIcon, QPixmap

logger = logging.getLogger(__name__)

# ── 数据常量 ─────────────────────────────────────────────────────

DEFAULT_W, DEFAULT_H = 760, 140

BOX_MODE_ORDER = ['temp', 'fixed', 'multi']
BOX_MODE_META = {
    'temp': ('临时', '临时翻译：框选后立即翻译，N 秒后自动消失'),
    'fixed': ('固定', '固定翻译：框保留在屏幕上，可手动或自动翻译'),
    'multi': ('多框', '多框翻译：可在屏幕上放置多个独立翻译框'),
    'ai': ('AI框', 'AI 框选：框选后直接进行 AI 解释，不走翻译'),
}

OVERLAY_MODE_ORDER = ['off', 'over', 'below']
OVERLAY_MODE_META = {
    'off': '覆盖翻译：关闭',
    'over': '覆盖翻译：显示在原文上',
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

DARK_MENU_STYLE = '''
QMenu {
    background: rgba(22, 22, 32, 240);
    color: rgba(200, 200, 215, 230);
    border: 1px solid rgba(255,255,255,30);
    border-radius: 6px;
    padding: 4px 2px;
    font-size: 11px;
}
QMenu::item { padding: 5px 18px; border-radius: 3px; }
QMenu::item:selected { background: rgba(80,130,255,180); color: white; }
QMenu::item:checked { font-weight: bold; color: rgba(120,200,255,255); }
'''


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


# ── 滑动切换控件 ──────────────────────────────────────────────────

class TranslateToggle(QWidget):
    """两段式滑动切换：点击 ↔ 自动"""
    toggled = pyqtSignal(bool)  # True = auto

    W, H = 86, 22

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto = False
        self.setFixedSize(self.W, self.H)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('点击切换：手动点击翻译 / 自动持续翻译')

    def set_auto(self, v: bool):
        self._auto = v
        self.update()

    def sizeHint(self):
        return QSize(self.W, self.H)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h // 2
        mid = w // 2

        # Track background
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(30, 30, 45, 200))
        p.drawRoundedRect(0, 0, w, h, r, r)

        # Active pill
        pill_x = mid if self._auto else 0
        pill_color = QColor(55, 185, 95, 215) if self._auto else QColor(60, 120, 240, 215)
        p.setBrush(pill_color)
        p.drawRoundedRect(pill_x, 0, mid, h, r, r)

        # Text labels
        f = p.font()
        f.setPixelSize(11)
        p.setFont(f)

        p.setPen(QColor(255, 255, 255, 230 if not self._auto else 90))
        p.drawText(0, 0, mid, h, Qt.AlignCenter, '点击')

        p.setPen(QColor(255, 255, 255, 230 if self._auto else 90))
        p.drawText(mid, 0, mid, h, Qt.AlignCenter, '自动')

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._auto = not self._auto
            self.update()
            self.toggled.emit(self._auto)


# ── 主结果条 ─────────────────────────────────────────────────────

class ResultBar(QWidget):
    start_selection_requested = pyqtSignal()
    stop_clear_requested      = pyqtSignal()
    explain_requested         = pyqtSignal(str)
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
        self._minimized = False
        self._drag_pos = QPoint()
        self._box_mode = 'temp'
        self._overlay_mode = self.settings.get('overlay_default_mode', 'off')
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

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_AlwaysShowToolTips, True)  # 保证 tooltip 在 Tool 窗口中可见
        self.setMinimumWidth(280)
        self.setMinimumHeight(60)
        self.resize(DEFAULT_W, DEFAULT_H)
        self._manual_size = True     # 防止 adjustSize() 在启动时压缩默认尺寸

    def _get_bg_alpha(self) -> int:
        return max(30, min(255, int(self.settings.get('result_bar_opacity', 0.85) * 255)))

    def _apply_opacity(self):
        alpha = self._get_bg_alpha()
        self._container.setStyleSheet(f'''
            QWidget#ct {{
                background: rgba(18, 18, 24, {alpha});
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,25);
            }}
        ''')

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
        self._btn_play.setStyleSheet('''
            QPushButton {
                background: rgba(60,130,240,200); color: white;
                border: 1px solid rgba(120,170,255,160);
                border-radius: 4px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(80,150,255,230); }
        ''')
        self._btn_play.clicked.connect(self.start_selection_requested.emit)
        tb.addWidget(self._btn_play)
        tb.addSpacing(4)

        self._btn_stop_clear = QPushButton('■')
        self._btn_stop_clear.setFixedSize(22, 22)
        self._btn_stop_clear.clicked.connect(self.stop_clear_requested.emit)
        tb.addWidget(self._btn_stop_clear)
        tb.addSpacing(4)

        # ↺ 恢复默认大小按钮
        self._btn_reset_size = QPushButton('↺')
        self._btn_reset_size.setToolTip('恢复结果条默认大小')
        self._btn_reset_size.setFixedSize(22, 22)
        self._btn_reset_size.setStyleSheet('''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(160,160,185,215);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: rgba(70,70,95,220); color: white; }
        ''')
        self._btn_reset_size.clicked.connect(self._reset_size)
        tb.addWidget(self._btn_reset_size)
        tb.addSpacing(4)

        # 左侧模式按钮
        self._btn_box_mode_cycle = self._mode_btn(*BOX_MODE_META['temp'], 'temp')
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
        self._btn_src_lang.setStyleSheet(self._lang_btn_style())
        self._btn_src_lang.clicked.connect(self._show_src_lang_menu)
        tb.addWidget(self._btn_src_lang)

        # 箭头分隔
        arrow = QLabel('→')
        arrow.setStyleSheet('color: rgba(120,120,140,180); font-size: 11px;')
        tb.addWidget(arrow)

        # 目标语言下拉按钮
        tgt_code = self.settings.get('target_language', 'zh-CN')
        tgt_label = next((s for c, s, _ in TARGET_LANGS if c == tgt_code), '简中')
        self._btn_tgt_lang = QPushButton(f'{tgt_label} ▾')
        self._btn_tgt_lang.setToolTip('目标翻译语言（点击切换）')
        self._btn_tgt_lang.setStyleSheet(self._lang_btn_style())
        self._btn_tgt_lang.clicked.connect(self._show_tgt_lang_menu)
        tb.addWidget(self._btn_tgt_lang)

        tb.addSpacing(6)

        # 复制译文（工具栏快捷区）
        self._btn_copy_trans = self._action_btn('📋', '复制译文到剪贴板', self._copy)
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

        tb.addSpacing(6)

        # 滑动切换：仅固定/多框模式显示
        self._toggle = TranslateToggle()
        self._toggle.toggled.connect(self._on_toggle_changed)
        self._toggle.setVisible(False)
        tb.addWidget(self._toggle)

        tb.addStretch()

        # 右侧图标按钮（固定在滚动区外，不随工具栏内容滚动）
        self._btn_history  = self._icon_btn('🕐', '翻译历史 (History)', self.history_requested.emit)
        self._btn_settings = self._icon_btn('⚙', '设置 (Settings)', self.settings_requested.emit)
        self._btn_minimize = self._icon_btn('─', '最小化/展开', self._toggle_minimize)
        self._btn_close    = self._icon_btn('✕', '关闭主窗口', self.close_requested.emit)

        self._tb_scroll = QScrollArea()
        self._tb_scroll.setWidget(self._tb_widget)
        self._tb_scroll.setWidgetResizable(False)
        self._tb_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._tb_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tb_scroll.setFrameShape(QFrame.NoFrame)
        self._tb_scroll.setFixedHeight(32)
        self._tb_scroll.setStyleSheet('''
            QScrollArea { background: transparent; border: none; }
            QScrollBar:horizontal {
                background: rgba(255,255,255,8); height: 4px; border-radius: 2px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255,255,255,50); border-radius: 2px; min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        ''')
        _tb_row = QHBoxLayout()
        _tb_row.setContentsMargins(0, 0, 0, 0)
        _tb_row.setSpacing(2)
        _tb_row.addWidget(self._tb_scroll, 1)
        for b in [self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close]:
            _tb_row.addWidget(b)
        cl.addLayout(_tb_row)
        self.set_stop_clear_busy(False)
        self._refresh_toolbar_layout()
        self._set_active_mode_btn(self._box_mode)
        self._refresh_overlay_button()

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: rgba(255,255,255,18);')
        cl.addWidget(sep)

        # ── 主体 ──────────────────────────────────────────────────
        self._body = QWidget()
        self._body.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        self._lbl_translation = QTextEdit()
        self._lbl_translation.setReadOnly(True)
        self._lbl_translation.setPlainText('等待翻译...')
        f = QFont()
        f.setPixelSize(14)
        self._lbl_translation.setFont(f)
        self._lbl_translation.setMinimumHeight(40)
        self._lbl_translation.setMinimumWidth(0)   # 防止 QTextEdit 撑宽结果条
        self._lbl_translation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_translation.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._lbl_translation.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._lbl_translation.setStyleSheet('''
            QTextEdit {
                color: #f0f0f0; background: transparent; border: none;
                padding: 0; margin: 0;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,12); width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,55); border-radius: 3px; min-height: 18px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        ''')
        bl.addWidget(self._lbl_translation)

        ar = QHBoxLayout()
        ar.setSpacing(5)
        self._btn_source   = self._action_btn('原文 ▼', '展开/收起原始识别文字', self._toggle_source)
        self._btn_copy_src = self._action_btn('📋 原文', '复制原始识别文字到剪贴板', self._copy_source)
        self._lbl_backend = QLabel('')
        self._lbl_backend.setStyleSheet('color: rgba(100,200,120,180); font-size: 10px;')
        self._resize_hint_lbl = QLabel('拖拽右下角调整大小 ⋱')
        self._resize_hint_lbl.setStyleSheet(
            'color: rgba(160,160,185,190); font-size: 10px; padding: 0;'
        )
        self._resize_hint_lbl.setToolTip('拖拽此处（右下角 20px 范围）调整窗口大小')
        ar.addWidget(self._btn_source)
        ar.addWidget(self._btn_copy_src)
        self._btn_ai = self._action_btn('💬 AI科普', '科普当前原文内容（同 Alt+E）', self._on_explain)
        ar.addWidget(self._btn_ai)
        ar.addStretch()
        ar.addWidget(self._lbl_backend)
        ar.addSpacing(8)
        ar.addWidget(self._resize_hint_lbl)
        bl.addLayout(ar)

        self._lbl_source = QLabel('')
        self._lbl_source.setStyleSheet('color: rgba(180,180,200,200); font-size: 12px; padding: 2px 0;')
        self._lbl_source.setWordWrap(True)
        self._lbl_source.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_source.setVisible(False)
        bl.addWidget(self._lbl_source)

        # ── AI科普加载提示（在原文按钮下方，不覆盖译文）─────────
        self._lbl_explain_loading = QLabel('💡 AI 科普中...')
        self._lbl_explain_loading.setStyleSheet(
            'color: rgba(230,220,130,200); font-size: 11px; padding: 2px 4px;'
        )
        self._lbl_explain_loading.setVisible(False)
        bl.addWidget(self._lbl_explain_loading)

        # ── AI科普区（运行后显示在原文按钮下方）─────────────────
        self._btn_explain_hdr = QPushButton('💡 AI科普 ▲')
        self._btn_explain_hdr.setVisible(False)
        self._btn_explain_hdr.setStyleSheet('''
            QPushButton {
                background: rgba(255,240,100,12); color: rgba(230,220,130,220);
                border: 1px solid rgba(255,240,100,30); border-radius: 4px;
                padding: 2px 8px; font-size: 11px; text-align: left;
            }
            QPushButton:hover { background: rgba(255,240,100,22); }
        ''')
        self._btn_explain_hdr.clicked.connect(self._toggle_explain_section)
        bl.addWidget(self._btn_explain_hdr)

        self._lbl_explain = QTextEdit()
        self._lbl_explain.setReadOnly(True)
        self._lbl_explain.setMinimumHeight(40)
        self._lbl_explain.setMinimumWidth(0)
        self._lbl_explain.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._lbl_explain.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._lbl_explain.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._lbl_explain.setVisible(False)
        self._lbl_explain.setStyleSheet('''
            QTextEdit {
                color: rgba(230,220,140,230); font-size: 12px;
                background: rgba(255,240,100,10); border: none;
                padding: 4px; border-radius: 4px;
            }
            QScrollBar:vertical {
                background: rgba(255,255,255,12); width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,160,60); border-radius: 3px; min-height: 18px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        ''')
        bl.addWidget(self._lbl_explain)

        cl.addWidget(self._body)

        outer.addWidget(self._container)

    # ── 按钮工厂 ──────────────────────────────────────────────────

    def _mode_btn(self, label: str, tip: str, key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setToolTip(tip)
        btn.setCheckable(True)
        btn.setFixedHeight(22)
        btn.setMinimumWidth(36)
        btn.setStyleSheet(self._mode_btn_style(False))
        btn.clicked.connect(lambda _, k=key: self._on_mode_btn_click(k))
        return btn

    def _small_toolbar_btn(self, label: str, tip: str, callback) -> QPushButton:
        btn = QPushButton(label)
        btn.setToolTip(tip)
        btn.setFixedSize(26, 22)
        btn.setStyleSheet('''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(200,200,210,220);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(70,70,95,220); color: white; }
        ''')
        btn.clicked.connect(callback)
        return btn

    def _mode_btn_style(self, active: bool) -> str:
        if active:
            return '''
                QPushButton {
                    background: rgba(80,140,255,200); color: white;
                    border: 1px solid rgba(120,170,255,180);
                    border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(100,160,255,220); }
            '''
        return '''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(180,180,200,200);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; padding: 2px 6px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,90,220); color: white; }
        '''

    def _lang_btn_style(self) -> str:
        return '''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(160,160,185,215);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; padding: 2px 8px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,95,220); color: rgba(210,220,255,235); }
        '''

    def _icon_btn(self, icon: str, tip: str, cb) -> QPushButton:
        b = QPushButton(icon)
        b.setToolTip(tip)
        b.setFixedSize(22, 22)
        b.setStyleSheet('''
            QPushButton { background: transparent; color: rgba(160,160,180,200);
                          border: none; font-size: 12px; }
            QPushButton:hover { color: white; background: rgba(255,255,255,15);
                                border-radius: 3px; }
        ''')
        b.clicked.connect(cb)
        return b

    def _action_btn(self, label: str, tip: str, cb) -> QPushButton:
        b = QPushButton(label)
        b.setToolTip(tip)
        b.setStyleSheet('''
            QPushButton { background: rgba(55,55,70,180); color: rgba(200,200,210,220);
                          border: 1px solid rgba(255,255,255,18); border-radius: 4px;
                          padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: rgba(75,75,100,210); color: white; }
        ''')
        b.clicked.connect(cb)
        return b

    def _update_lang_button_widths(self):
        for btn in (self._btn_src_lang, self._btn_tgt_lang):
            min_width = max(btn.sizeHint().width(), btn.fontMetrics().horizontalAdvance(btn.text()) + 20)
            btn.setMinimumWidth(min_width)

    def _stop_clear_btn_style(self, busy: bool) -> str:
        if busy:
            return '''
                QPushButton {
                    background: rgba(180,80,50,190); color: white;
                    border: 1px solid rgba(255,170,120,120);
                    border-radius: 4px; font-size: 11px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(210,95,60,220); }
            '''
        return '''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(200,200,210,220);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(70,70,95,220); color: white; }
        '''

    def _refresh_toolbar_layout(self):
        self._update_lang_button_widths()
        self._tb_widget.adjustSize()
        self._tb_widget.setFixedSize(self._tb_widget.sizeHint())

    def set_stop_clear_busy(self, busy: bool):
        self._translation_busy = busy
        tooltip = '终止当前翻译' if busy else '清空当前翻译内容'
        self._btn_stop_clear.setToolTip(tooltip)
        self._btn_stop_clear.setStyleSheet(self._stop_clear_btn_style(busy))

    def clear_current_content(self):
        self._current_result = None
        self._source_expanded = False
        self._lbl_translation.setPlainText('等待翻译...')
        self._lbl_backend.setText('')
        self._lbl_source.clear()
        self._lbl_source.setVisible(False)
        self._btn_source.setText('原文 ▼')
        self._lbl_explain_loading.setVisible(False)
        self._lbl_explain.clear()
        self._lbl_explain.setVisible(False)
        self._btn_explain_hdr.setVisible(False)
        self._smart_adjust()

    # ── 语言下拉菜单 ──────────────────────────────────────────────

    def _show_src_lang_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(DARK_MENU_STYLE)
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
        menu.setStyleSheet(DARK_MENU_STYLE)
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
        self._box_mode = key
        self._set_active_mode_btn(key)
        self._toggle.setVisible(key != 'temp')
        self._refresh_toolbar_layout()
        self.box_mode_changed.emit(key)
        self._smart_adjust()

    def _cycle_box_mode(self):
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

    def refresh_opacity(self):
        self._apply_opacity()

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

    def show_result(self, result: dict):
        self._current_result = result
        self._lbl_explain.setVisible(False)
        self._btn_explain_hdr.setVisible(False)
        self._lbl_explain_loading.setVisible(False)
        self._source_expanded = False
        self._lbl_source.setVisible(False)
        self._btn_source.setText('原文 ▼')

        self._lbl_translation.setPlainText(result.get('translated', ''))
        self._lbl_source.setText(result.get('original', ''))
        self._lbl_backend.setText(f"来源: {result.get('backend', '')}")

        # 更新源语言按钮显示检测到的语言
        src = result.get('source_lang', '')
        if src:
            src_short = next((s for c, s, _ in SOURCE_LANGS
                              if c == src.lower() or c == src.lower().split('-')[0]), src.upper())
            self._btn_src_lang.setText(f'{src_short} ▾')
            self._refresh_toolbar_layout()

        if not self.isVisible() and not self._hidden_to_tray:
            self.show()
        self._smart_adjust()

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

    def show_loading(self, msg: str = '翻译中...'):
        self._lbl_translation.setPlainText(msg)
        self._lbl_backend.setText('')
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

    def _refresh_overlay_button(self):
        self._btn_overlay.setToolTip(OVERLAY_MODE_META.get(self._overlay_mode, OVERLAY_MODE_META['off']))
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

    def _on_explain(self):
        if self._current_result is None:
            # 结果条尚无内容，先自动触发框选
            self.start_selection_requested.emit()
            return
        text = self._current_result.get('original', '')
        if text:
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
            f' [临时 {hk_temp} / 固定 {hk_fixed} / 多框 {hk_multi}]'
        )
        self._btn_ai_mode.setToolTip(f'{BOX_MODE_META["ai"][1]}  [{hk_ai}]')
