import logging
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

# 三种框模式
BOX_MODES = [
    ('temp',  '临时',  '临时翻译：框选后立即翻译，N秒后自动消失'),
    ('fixed', '固定',  '固定翻译：框保留在屏幕上，可手动或自动翻译'),
    ('multi', '多框',  '多框翻译：可在屏幕上放置多个独立翻译框'),
]


class ResultBar(QWidget):
    explain_requested = pyqtSignal(str)
    history_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    box_mode_changed = pyqtSignal(str)       # 'temp' | 'fixed' | 'multi'
    translate_mode_changed = pyqtSignal(str) # 'manual' | 'auto'

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._current_result = None
        self._source_expanded = False
        self._minimized = False
        self._drag_pos = QPoint()
        self._box_mode = 'temp'
        self._translate_mode = 'manual'
        self._setup_window()
        self._setup_ui()
        self._position_window()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(500)
        self.setMaximumWidth(860)

    def _get_bg_alpha(self) -> int:
        """从设置中读取透明度，转换为 0-255"""
        opacity = self.settings.get('result_bar_opacity', 0.85)
        return max(30, min(255, int(opacity * 255)))

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
        self.adjustSize()
        if pos == 'top':
            self.move(cx - self.width() // 2, 10)
        else:
            self.move(cx - self.width() // 2, screen.height() - self.height() - 50)

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._container = QWidget()
        self._container.setObjectName('ct')
        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(10, 7, 10, 7)
        cl.setSpacing(4)
        self._apply_opacity()

        # ── 工具栏 ────────────────────────────────────────────
        tb = QHBoxLayout()
        tb.setSpacing(4)

        # 左侧：三个模式按钮
        self._mode_btns = {}
        for key, label, tip in BOX_MODES:
            btn = self._mode_btn(label, tip, key)
            self._mode_btns[key] = btn
            tb.addWidget(btn)

        tb.addSpacing(6)

        # 语言方向标签
        self._lbl_lang = QLabel('-- → --')
        self._lbl_lang.setStyleSheet('color: rgba(160,160,180,200); font-size: 11px;')
        tb.addWidget(self._lbl_lang)

        tb.addSpacing(4)

        # 翻译方式切换按钮（仅固定/多框模式有意义）
        self._btn_trans_mode = QPushButton('点击翻译')
        self._btn_trans_mode.setToolTip('切换手动点击翻译 / 自动持续翻译')
        self._btn_trans_mode.setCheckable(True)
        self._btn_trans_mode.setStyleSheet(self._trans_mode_style(False))
        self._btn_trans_mode.clicked.connect(self._on_translate_mode_click)
        tb.addWidget(self._btn_trans_mode)

        tb.addStretch()

        # 右侧图标按钮
        self._btn_history  = self._icon_btn('🕐', '翻译历史', self.history_requested.emit)
        self._btn_settings = self._icon_btn('⚙',  '设置',    self.settings_requested.emit)
        self._btn_minimize = self._icon_btn('─',  '最小化/展开', self._toggle_minimize)
        self._btn_close    = self._icon_btn('✕',  '隐藏结果条', self.hide)
        for b in [self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close]:
            tb.addWidget(b)

        cl.addLayout(tb)

        # 激活默认模式按钮
        self._set_active_mode_btn('temp')

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: rgba(255,255,255,18);')
        cl.addWidget(sep)

        # ── 主体（可折叠）────────────────────────────────────
        self._body = QWidget()
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        # 译文
        self._lbl_translation = QLabel('等待翻译...')
        f = QFont()
        f.setPixelSize(14)
        self._lbl_translation.setFont(f)
        self._lbl_translation.setStyleSheet('color: #f0f0f0;')
        self._lbl_translation.setWordWrap(True)
        self._lbl_translation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_translation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bl.addWidget(self._lbl_translation)

        # 操作行
        ar = QHBoxLayout()
        ar.setSpacing(5)
        self._btn_source  = self._action_btn('原文 ▼', self._toggle_source)
        self._btn_copy    = self._action_btn('📋 复制', self._copy)
        self._btn_explain = self._action_btn('💬 AI解释', self._on_explain)
        self._lbl_backend = QLabel('')
        self._lbl_backend.setStyleSheet('color: rgba(100,200,120,180); font-size: 10px;')
        ar.addWidget(self._btn_source)
        ar.addWidget(self._btn_copy)
        ar.addWidget(self._btn_explain)
        ar.addStretch()
        ar.addWidget(self._lbl_backend)
        bl.addLayout(ar)

        # 原文展开区
        self._lbl_source = QLabel('')
        self._lbl_source.setStyleSheet('color: rgba(180,180,200,200); font-size: 12px; padding: 2px 0;')
        self._lbl_source.setWordWrap(True)
        self._lbl_source.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_source.setVisible(False)
        bl.addWidget(self._lbl_source)

        # AI 解释展开区
        self._lbl_explain = QLabel('')
        self._lbl_explain.setStyleSheet('''
            color: rgba(230,220,160,230); font-size: 12px;
            padding: 6px; border-radius: 4px;
            background: rgba(255,240,100,15);
        ''')
        self._lbl_explain.setWordWrap(True)
        self._lbl_explain.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_explain.setVisible(False)
        bl.addWidget(self._lbl_explain)

        cl.addWidget(self._body)
        outer.addWidget(self._container)

    # ── 按钮工厂 ──────────────────────────────────────────────

    def _mode_btn(self, label: str, tip: str, key: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setToolTip(tip)
        btn.setCheckable(True)
        btn.setFixedHeight(22)
        btn.setMinimumWidth(36)
        btn.setStyleSheet(self._mode_btn_style(False))
        btn.clicked.connect(lambda _, k=key: self._on_mode_btn_click(k))
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

    def _trans_mode_style(self, is_auto: bool) -> str:
        if is_auto:
            return '''
                QPushButton {
                    background: rgba(80,200,120,180); color: white;
                    border: 1px solid rgba(100,220,140,160);
                    border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(90,210,130,200); }
            '''
        return '''
            QPushButton {
                background: rgba(50,50,65,180); color: rgba(180,180,200,200);
                border: 1px solid rgba(255,255,255,15);
                border-radius: 4px; padding: 2px 8px; font-size: 11px;
            }
            QPushButton:hover { background: rgba(70,70,90,220); color: white; }
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

    def _action_btn(self, label: str, cb) -> QPushButton:
        b = QPushButton(label)
        b.setStyleSheet('''
            QPushButton { background: rgba(55,55,70,180); color: rgba(200,200,210,220);
                          border: 1px solid rgba(255,255,255,18); border-radius: 4px;
                          padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: rgba(75,75,100,210); color: white; }
        ''')
        b.clicked.connect(cb)
        return b

    # ── 模式切换 ───────────────────────────────────────────────

    def _set_active_mode_btn(self, key: str):
        for k, btn in self._mode_btns.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._mode_btn_style(k == key))

    def _on_mode_btn_click(self, key: str):
        self._box_mode = key
        self._set_active_mode_btn(key)
        # 仅固定/多框模式显示翻译方式按钮
        self._btn_trans_mode.setVisible(key != 'temp')
        self.box_mode_changed.emit(key)
        self.adjustSize()

    def _on_translate_mode_click(self):
        is_auto = self._btn_trans_mode.isChecked()
        self._translate_mode = 'auto' if is_auto else 'manual'
        self._btn_trans_mode.setText('自动翻译' if is_auto else '点击翻译')
        self._btn_trans_mode.setStyleSheet(self._trans_mode_style(is_auto))
        self.translate_mode_changed.emit(self._translate_mode)

    # ── public API ─────────────────────────────────────────────

    def refresh_opacity(self):
        """设置保存后调用，刷新透明度"""
        self._apply_opacity()

    def show_result(self, result: dict):
        self._current_result = result
        self._lbl_explain.setVisible(False)
        self._source_expanded = False
        self._lbl_source.setVisible(False)
        self._btn_source.setText('原文 ▼')

        self._lbl_translation.setText(result.get('translated', ''))
        self._lbl_source.setText(result.get('original', ''))
        self._lbl_backend.setText(f"来源: {result.get('backend', '')}")

        src = result.get('source_lang', '--')
        tgt = result.get('target_lang', '--')
        self._lbl_lang.setText(f'{src.upper()} → {tgt}')

        if not self.isVisible():
            self.show()
        self.adjustSize()

    def show_explain(self, text: str):
        self._lbl_explain.setText(text)
        self._lbl_explain.setVisible(True)
        self.adjustSize()

    def show_loading(self, msg: str = '翻译中...'):
        self._lbl_translation.setText(msg)
        self._lbl_backend.setText('')
        if not self.isVisible():
            self.show()

    def show_error(self, msg: str):
        self._lbl_translation.setText(f'⚠ {msg}')
        if not self.isVisible():
            self.show()

    # ── private slots ──────────────────────────────────────────

    def _toggle_source(self):
        self._source_expanded = not self._source_expanded
        self._lbl_source.setVisible(self._source_expanded)
        self._btn_source.setText('原文 ▲' if self._source_expanded else '原文 ▼')
        self.adjustSize()

    def _copy(self):
        if self._current_result:
            QApplication.clipboard().setText(self._current_result.get('translated', ''))

    def _on_explain(self):
        if self._current_result:
            text = self._current_result.get('original', '')
            if text:
                self.explain_requested.emit(text)

    def _toggle_minimize(self):
        self._minimized = not self._minimized
        self._body.setVisible(not self._minimized)
        self._btn_minimize.setText('□' if self._minimized else '─')
        self.adjustSize()

    # ── drag ───────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
