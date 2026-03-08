import logging
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QApplication, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class ResultBar(QWidget):
    explain_requested = pyqtSignal(str)
    history_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._current_result = None
        self._source_expanded = False
        self._minimized = False
        self._drag_pos = QPoint()
        self._setup_window()
        self._setup_ui()
        self._position_window()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(480)
        self.setMaximumWidth(800)

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
        self._container.setStyleSheet('''
            QWidget#ct {
                background: rgba(18, 18, 24, 230);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,25);
            }
        ''')
        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(12, 8, 12, 8)
        cl.setSpacing(5)

        # 工具栏
        tb = QHBoxLayout()
        tb.setSpacing(5)
        self._lbl_lang = QLabel('-- → --')
        self._lbl_lang.setStyleSheet('color: rgba(160,160,180,200); font-size: 11px;')
        self._btn_history = self._icon_btn('🕐', '翻译历史', self.history_requested.emit)
        self._btn_settings = self._icon_btn('⚙', '设置', self.settings_requested.emit)
        self._btn_minimize = self._icon_btn('─', '最小化/展开', self._toggle_minimize)
        self._btn_close = self._icon_btn('✕', '隐藏', self.hide)
        tb.addWidget(self._lbl_lang)
        tb.addStretch()
        for b in [self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close]:
            tb.addWidget(b)
        cl.addLayout(tb)

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: rgba(255,255,255,18);')
        cl.addWidget(sep)

        # 主体内容（可折叠）
        self._body = QWidget()
        bl = QVBoxLayout(self._body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(4)

        # 译文
        self._lbl_translation = QLabel('等待翻译...')
        font = QFont()
        font.setPixelSize(14)
        self._lbl_translation.setFont(font)
        self._lbl_translation.setStyleSheet('color: #f0f0f0;')
        self._lbl_translation.setWordWrap(True)
        self._lbl_translation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_translation.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        bl.addWidget(self._lbl_translation)

        # 操作行
        ar = QHBoxLayout()
        ar.setSpacing(5)
        self._btn_source = self._action_btn('原文 ▼', self._toggle_source)
        self._btn_copy = self._action_btn('📋 复制', self._copy)
        self._btn_explain = self._action_btn('💬 AI解释', self._on_explain)
        self._lbl_backend = QLabel('')
        self._lbl_backend.setStyleSheet('color: rgba(100,200,120,180); font-size: 10px;')
        ar.addWidget(self._btn_source)
        ar.addWidget(self._btn_copy)
        ar.addWidget(self._btn_explain)
        ar.addStretch()
        ar.addWidget(self._lbl_backend)
        bl.addLayout(ar)

        # 原文展开
        self._lbl_source = QLabel('')
        self._lbl_source.setStyleSheet('color: rgba(180,180,200,200); font-size: 12px; padding: 2px 0;')
        self._lbl_source.setWordWrap(True)
        self._lbl_source.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._lbl_source.setVisible(False)
        bl.addWidget(self._lbl_source)

        # AI解释展开
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

    def _icon_btn(self, icon, tip, cb):
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

    def _action_btn(self, label, cb):
        b = QPushButton(label)
        b.setStyleSheet('''
            QPushButton { background: rgba(55,55,70,180); color: rgba(200,200,210,220);
                          border: 1px solid rgba(255,255,255,18); border-radius: 4px;
                          padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: rgba(75,75,100,210); color: white; }
        ''')
        b.clicked.connect(cb)
        return b

    # ── public API ──────────────────────────────────────────

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

    # ── private slots ────────────────────────────────────────

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

    # ── drag ─────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
