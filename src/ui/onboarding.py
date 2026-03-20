"""首次启动引导向导

OnboardingWizard: 4 步悬浮向导，风格与 _TempModeHintDialog 一致。
首次启动时由 CoreController 触发，完成或跳过后写入 first_launch_done=True。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal


class OnboardingWizard(QWidget):
    """首次使用引导向导（4 步）。"""

    finished = pyqtSignal()
    open_settings = pyqtSignal(int)   # tab index: 0=通用, 1=翻译来源, 2=API密钥, 3=外观

    def __init__(self, settings, parent=None):
        super().__init__(parent, Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._settings = settings
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._current_step = 0
        self._total_steps = 4

        from ui.theme import get_skin
        skin_name = settings.get('skin', 'deep_space')
        variant = settings.get('button_style_variant', 'calm')
        skin = get_skin(skin_name, variant)

        self._bg   = skin.get('surface', skin.get('bg', '#1a1f2e'))
        self._fg   = skin.get('text', '#e8eaf0')
        self._acc  = skin.get('accent', skin.get('btn_primary_bg', '#4a90e2'))
        self._rad  = skin.get('radius', 8)
        self._muted = skin.get('text_muted', 'rgba(185,192,215,180)')

        self._container = QWidget(self)
        self._container.setObjectName('onboard_container')
        self._container.setFixedWidth(400)
        self._container.setStyleSheet(
            f"#onboard_container {{ background: {self._bg}; "
            f"border-radius: {self._rad}px; }}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._container)

        main_layout = QVBoxLayout(self._container)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(0)

        # ── 标题行 ──────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self._title_label = QLabel()
        self._title_label.setStyleSheet(
            f"color: {self._fg}; font-weight: bold; font-size: 13px; background: transparent;"
        )
        header_row.addWidget(self._title_label)
        header_row.addStretch()

        skip_btn = QPushButton('跳过')
        skip_btn.setFixedHeight(22)
        skip_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {self._muted}; border: none; "
            f"font-size: 11px; padding: 0 4px; }}"
            f"QPushButton:hover {{ color: {self._fg}; }}"
        )
        skip_btn.clicked.connect(self._on_skip)
        header_row.addWidget(skip_btn)

        main_layout.addLayout(header_row)
        main_layout.addSpacing(8)

        # ── 分隔线 ──────────────────────────────────────────────────
        sep_top = QFrame()
        sep_top.setFrameShape(QFrame.HLine)
        sep_top.setStyleSheet(f"color: rgba(255,255,255,20); background: rgba(255,255,255,20);")
        sep_top.setFixedHeight(1)
        main_layout.addWidget(sep_top)
        main_layout.addSpacing(12)

        # ── 内容区（QStackedWidget）────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setFixedHeight(230)
        step_widgets = self._build_step_widgets()
        for w in step_widgets:
            self._stack.addWidget(w)
        main_layout.addWidget(self._stack)
        main_layout.addSpacing(12)

        # ── 分隔线 ──────────────────────────────────────────────────
        sep_bot = QFrame()
        sep_bot.setFrameShape(QFrame.HLine)
        sep_bot.setStyleSheet(f"color: rgba(255,255,255,20); background: rgba(255,255,255,20);")
        sep_bot.setFixedHeight(1)
        main_layout.addWidget(sep_bot)
        main_layout.addSpacing(10)

        # ── 导航行 ──────────────────────────────────────────────────
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        # 步骤指示点
        self._dots = []
        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(5)
        for i in range(self._total_steps):
            dot = QLabel('●' if i == 0 else '○')
            dot.setStyleSheet(
                f"color: {self._acc if i == 0 else self._muted}; "
                f"font-size: 10px; background: transparent;"
            )
            self._dots.append(dot)
            dots_layout.addWidget(dot)
        nav_row.addLayout(dots_layout)
        nav_row.addStretch()

        self._prev_btn = QPushButton('上一步')
        self._prev_btn.setFixedHeight(26)
        self._prev_btn.setStyleSheet(self._nav_btn_style())
        self._prev_btn.clicked.connect(self._on_prev)

        self._next_btn = QPushButton('下一步')
        self._next_btn.setFixedHeight(26)
        self._next_btn.setStyleSheet(self._nav_btn_style(primary=True))
        self._next_btn.clicked.connect(self._on_next)

        nav_row.addWidget(self._prev_btn)
        nav_row.addWidget(self._next_btn)

        main_layout.addLayout(nav_row)

        self._go_to_step(0)

    # ── 步骤构建 ────────────────────────────────────────────────────

    def _build_step_widgets(self) -> list:
        return [
            self._build_step1(),
            self._build_step2(),
            self._build_step3(),
            self._build_step4(),
        ]

    def _make_step_widget(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        return w

    def _content_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {self._fg}; font-size: 12px; background: transparent;"
        )
        lbl.setWordWrap(True)
        return lbl

    def _muted_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {self._muted}; font-size: 12px; background: transparent;"
        )
        lbl.setWordWrap(True)
        return lbl

    def _build_step1(self) -> QWidget:
        w = self._make_step_widget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        hk_select = self._settings.get('hotkey_select', 'Alt+Q').upper()
        hk_explain = self._settings.get('hotkey_explain', 'Alt+E').upper()
        hk_toggle = self._settings.get('hotkey_toggle_boxes', 'Alt+W').upper()

        layout.addWidget(self._content_label('三个最常用的热键：'))
        layout.addSpacing(4)

        for hk, desc in [
            (hk_select,  '框选翻译 — 选取屏幕区域进行 OCR 翻译'),
            (hk_explain, 'AI 解释 — 对翻译结果进行 AI 深度解释'),
            (hk_toggle,  '隐藏/显示 — 切换所有翻译框的可见性'),
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            hk_lbl = QLabel(hk)
            hk_lbl.setStyleSheet(
                f"color: {self._fg}; font-size: 11px; font-weight: bold; "
                f"background: rgba(255,255,255,12); border: 1px solid rgba(255,255,255,25); "
                f"border-radius: 4px; padding: 1px 6px;"
            )
            hk_lbl.setFixedWidth(80)
            hk_lbl.setAlignment(Qt.AlignCenter)
            desc_lbl = self._muted_label(desc)
            row.addWidget(hk_lbl)
            row.addWidget(desc_lbl, 1)
            layout.addLayout(row)

        layout.addStretch()
        return w

    def _build_step2(self) -> QWidget:
        w = self._make_step_widget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(self._content_label('四种翻译模式：'))
        layout.addSpacing(4)

        modes = [
            ('临时模式', '翻译后自动隐藏结果条，译文显示在选区下方'),
            ('固定模式', '翻译框持续显示，可拖动、调整大小'),
            ('多框模式', '同时维护多个翻译框，结果条汇总全部译文'),
            ('AI 框选', '框选后直接进行 AI 解释，无需手动触发'),
        ]
        for name, desc in modes:
            row = QHBoxLayout()
            row.setSpacing(10)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                f"color: {self._fg}; font-size: 11px; font-weight: bold; "
                f"background: transparent;"
            )
            name_lbl.setFixedWidth(68)
            desc_lbl = self._muted_label(desc)
            row.addWidget(name_lbl)
            row.addWidget(desc_lbl, 1)
            layout.addLayout(row)

        layout.addStretch()
        return w

    def _build_step3(self) -> QWidget:
        w = self._make_step_widget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        layout.addWidget(self._content_label('翻译后端：'))

        backends = [
            ('Bing / Google', '免费，无需配置'),
            ('智谱 AI',        '免费，注册即用，支持 AI 解释 ★推荐'),
            ('百度翻译',       '需要 AppID + 密钥'),
            ('DeepL',          '需要 API Key，质量高'),
            ('OpenAI / Claude', '需要 API Key，AI 解释最强'),
        ]
        for name, desc in backends:
            row = QHBoxLayout()
            row.setSpacing(10)
            name_lbl = QLabel(name)
            is_rec = '★' in desc
            name_style = (
                f"color: {self._acc}; font-size: 11px; font-weight: bold; background: transparent;"
                if is_rec else
                f"color: {self._fg}; font-size: 11px; font-weight: bold; background: transparent;"
            )
            name_lbl.setStyleSheet(name_style)
            name_lbl.setFixedWidth(100)
            desc_lbl = self._muted_label(desc.replace(' ★推荐', ''))
            if is_rec:
                desc_lbl.setStyleSheet(
                    f"color: {self._acc}; font-size: 11px; background: transparent;"
                )
            row.addWidget(name_lbl)
            row.addWidget(desc_lbl, 1)
            layout.addLayout(row)

        # ── 智谱注册引导 ────────────────────────────────────────────
        rec_box = QWidget()
        rec_box.setStyleSheet(
            f"background: rgba(255,255,255,8); border: 1px solid rgba(255,255,255,20); "
            f"border-radius: 6px;"
        )
        rec_layout = QVBoxLayout(rec_box)
        rec_layout.setContentsMargins(10, 7, 10, 7)
        rec_layout.setSpacing(3)

        rec_title = QLabel('智谱 AI 免费注册（推荐）')
        rec_title.setStyleSheet(
            f"color: {self._acc}; font-size: 11px; font-weight: bold; background: transparent; border: none;"
        )
        rec_layout.addWidget(rec_title)

        steps = QLabel('① 访问 open.bigmodel.cn  ② 注册账号  ③ 进入「API Keys」创建密钥\n④ 复制 Key 填入设置 → API 密钥 → 智谱 Key')
        steps.setStyleSheet(
            f"color: {self._muted}; font-size: 10px; background: transparent; border: none;"
        )
        steps.setWordWrap(True)
        rec_layout.addWidget(steps)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addStretch()

        open_btn = QPushButton('打开注册页 →')
        open_btn.setFixedHeight(22)
        open_btn.setStyleSheet(self._nav_btn_style(primary=True))
        open_btn.clicked.connect(self._open_zhipu_url)
        btn_row.addWidget(open_btn)

        settings_btn = QPushButton('去设置 →')
        settings_btn.setFixedHeight(22)
        settings_btn.setStyleSheet(self._nav_btn_style())
        settings_btn.clicked.connect(self._on_open_api_settings)
        btn_row.addWidget(settings_btn)

        rec_layout.addLayout(btn_row)
        layout.addWidget(rec_box)

        return w

    def _on_open_api_settings(self):
        self.close()
        self.open_settings.emit(2)   # 2 = API 密钥标签页

    def _open_zhipu_url(self):
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        QDesktopServices.openUrl(QUrl('https://open.bigmodel.cn'))

    def _build_step4(self) -> QWidget:
        w = self._make_step_widget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addStretch()

        hk_select = self._settings.get('hotkey_select', 'Alt+Q').upper()
        big_hint = QLabel(f'现在按 {hk_select} 框选文字，\n开始第一次翻译！')
        big_hint.setAlignment(Qt.AlignCenter)
        big_hint.setStyleSheet(
            f"color: {self._fg}; font-size: 14px; font-weight: bold; "
            f"background: transparent;"
        )
        layout.addWidget(big_hint)

        layout.addSpacing(8)
        tip = QLabel('可随时在托盘右键菜单或结果条设置按钮中重新查看引导。')
        tip.setAlignment(Qt.AlignCenter)
        tip.setStyleSheet(
            f"color: {self._muted}; font-size: 11px; background: transparent;"
        )
        tip.setWordWrap(True)
        layout.addWidget(tip)

        layout.addStretch()
        return w

    # ── 导航 ────────────────────────────────────────────────────────

    def _nav_btn_style(self, primary: bool = False) -> str:
        if primary:
            return (
                f"QPushButton {{ background: {self._acc}; color: #fff; "
                f"border: none; border-radius: 4px; padding: 0 14px; font-size: 12px; }}"
                f"QPushButton:hover {{ opacity: 0.9; }}"
            )
        return (
            f"QPushButton {{ background: transparent; color: {self._fg}; "
            f"border: 1px solid rgba(255,255,255,30); border-radius: 4px; "
            f"padding: 0 12px; font-size: 12px; }}"
            f"QPushButton:hover {{ background: rgba(255,255,255,12); }}"
        )

    def _go_to_step(self, index: int):
        self._current_step = index
        self._stack.setCurrentIndex(index)

        # 更新标题
        titles = ['核心热键', '翻译模式', '翻译后端', '开始使用']
        self._title_label.setText(f'第 {index + 1}/{self._total_steps} 步：{titles[index]}')

        # 更新指示点
        for i, dot in enumerate(self._dots):
            if i == index:
                dot.setText('●')
                dot.setStyleSheet(
                    f"color: {self._acc}; font-size: 10px; background: transparent;"
                )
            else:
                dot.setText('○')
                dot.setStyleSheet(
                    f"color: {self._muted}; font-size: 10px; background: transparent;"
                )

        # 更新按钮
        self._prev_btn.setVisible(index > 0)
        is_last = (index == self._total_steps - 1)
        self._next_btn.setText('完成' if is_last else '下一步')
        self._next_btn.setStyleSheet(self._nav_btn_style(primary=True))

    def _on_prev(self):
        if self._current_step > 0:
            self._go_to_step(self._current_step - 1)

    def _on_next(self):
        if self._current_step < self._total_steps - 1:
            self._go_to_step(self._current_step + 1)
        else:
            self._on_finish()

    def _on_skip(self):
        self._settings.set('first_launch_done', True)
        self.finished.emit()
        self.close()

    def _on_finish(self):
        self._settings.set('first_launch_done', True)
        self.finished.emit()
        self.close()
