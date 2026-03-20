from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QPushButton,
                             QListWidget, QListWidgetItem, QTabWidget,
                             QWidget, QFormLayout, QMessageBox,
                             QProgressBar, QGroupBox, QCheckBox, QDoubleSpinBox,
                             QScrollArea, QSizePolicy, QGridLayout, QFrame,
                             QRadioButton, QButtonGroup)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPen
from ui.theme import SKINS, list_skins, FONT_SETS, ICON_SETS

def _no_wheel(widget):
    """禁止鼠标滚轮修改控件值。"""
    widget.wheelEvent = lambda e: e.ignore()
    return widget


BACKEND_LABELS = {    'dictionary':   '📖 本地词典（离线极快）',
    'bing':         '🔷 微软 Bing 翻译（免费，部分网络需梯子）',
    'google':       '🌐 谷歌翻译（免费，需梯子）',
    'baidu':        '🔵 百度翻译',
    'deepl':        '🟢 DeepL',
    'zhipu':        '🆓 智谱 GLM-4-Flash（永久免费）',
    'siliconflow':  '🆓 硅基流动（注册送 14 元）',
    'moonshot':     '🆓 月之暗面 Kimi（新用户赠额度）',
    'deepseek':     '🤖 DeepSeek AI',
    'openai':       '🤖 OpenAI GPT',
    'claude':       '🤖 Claude AI',
    'sogou':        '🟠 搜狗翻译（免费，国内直连，暂不可用）',
    'youdao':       '🟡 有道翻译（已封锁非官方调用，暂不可用）',
}


class _SkinCard(QWidget):
    """皮肤选择卡片：显示皮肤名称、描述和三色预览块，可点击选中。"""
    clicked = pyqtSignal(str)   # 发送皮肤 ID

    _W, _H = 160, 90

    def __init__(self, skin_id: str, skin: dict, parent=None):
        super().__init__(parent)
        self._id = skin_id
        self._skin = skin
        self._selected = False
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(skin.get('description', ''))

    def set_selected(self, v: bool):
        self._selected = v
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r, g, b = self._skin.get('bg_rgb', (20, 20, 28))
        # 背景
        p.setBrush(QColor(r, g, b, 230))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 0, w, h, 8, 8)
        # 选中边框
        if self._selected:
            p.setPen(QPen(QColor(80, 200, 120, 220), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(1, 1, w - 2, h - 2, 8, 8)
        else:
            p.setPen(QPen(QColor(255, 255, 255, 28), 1))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)
        # 三色预览块（左下角横排）
        swatches = self._skin.get('swatch', ('#222', '#555', '#888'))
        sw, sh, gap = 20, 12, 4
        sx = gap
        sy = h - sh - gap
        for color in swatches:
            p.setBrush(QColor(color))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(sx, sy, sw, sh, 3, 3)
            sx += sw + gap
        # 皮肤名称
        text_color = QColor(self._skin.get('text', '#e0e4ef'))
        p.setPen(text_color)
        f = p.font()
        f.setPixelSize(13)
        f.setBold(True)
        p.setFont(f)
        p.drawText(8, 14, self._skin.get('name', self._id))
        # 描述
        muted = QColor(self._skin.get('text_muted', '#888898'))
        p.setPen(muted)
        f.setPixelSize(10)
        f.setBold(False)
        p.setFont(f)
        p.drawText(8, 30, w - 16, 28, Qt.AlignLeft | Qt.TextWordWrap,
                   self._skin.get('description', ''))
        # 选中勾号
        if self._selected:
            p.setPen(QPen(QColor(80, 200, 120, 220), 2))
            check_x, check_y = w - 20, 8
            p.drawLine(check_x, check_y + 5, check_x + 4, check_y + 9)
            p.drawLine(check_x + 4, check_y + 9, check_x + 10, check_y + 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._id)


class SettingsWindow(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle('ScreenTranslator - 设置')
        self.setMinimumWidth(520)
        self.resize(560, 640)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
            | Qt.WindowStaysOnTopHint
        )
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        tabs = QTabWidget()

        # ── 通用 ──────────────────────────────────────────────
        gen = QWidget()
        gen_layout = QVBoxLayout(gen)
        gen_layout.setSpacing(8)
        gen_layout.setContentsMargins(0, 0, 0, 0)

        # 主设置表单
        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.setSpacing(8)

        self._chk_auto_dismiss = QCheckBox('临时框自动消失')
        form.addRow(self._chk_auto_dismiss)

        self._spin_timeout = _no_wheel(QSpinBox())
        self._spin_timeout.setRange(1, 60)
        self._spin_timeout.setSuffix(' 秒')
        form.addRow('    消失时间', self._spin_timeout)

        self._chk_auto_dismiss.stateChanged.connect(
            lambda state: self._spin_timeout.setEnabled(bool(state))
        )

        self._spin_interval = _no_wheel(QSpinBox())
        self._spin_interval.setRange(1, 120)
        form.addRow('固定框自动翻译间隔（秒）', self._spin_interval)

        self._combo_target = _no_wheel(QComboBox())
        for code, name in [('zh-CN', '简体中文'), ('zh-TW', '繁体中文'), ('en', '英语'),
                           ('ja', '日语'), ('ko', '韩语'), ('fr', '法语'),
                           ('de', '德语'), ('es', '西班牙语'), ('ru', '俄语')]:
            self._combo_target.addItem(name, code)
        form.addRow('默认翻译目标语言', self._combo_target)

        self._combo_pos = _no_wheel(QComboBox())
        self._combo_pos.addItem('中央', 'center')
        self._combo_pos.addItem('顶部', 'top')
        self._combo_pos.addItem('底部', 'bottom')
        self._combo_pos.addItem('左侧', 'left')
        self._combo_pos.addItem('右侧', 'right')
        self._combo_pos.addItem('上次位置', 'last')
        form.addRow('结果条位置', self._combo_pos)

        self._combo_size = _no_wheel(QComboBox())
        self._combo_size.addItem('默认大小', 'default')
        self._combo_size.addItem('上次大小', 'last')
        form.addRow('结果条大小', self._combo_size)

        self._combo_close_behavior = _no_wheel(QComboBox())
        self._combo_close_behavior.addItem('每次询问', 'ask')
        self._combo_close_behavior.addItem('最小化到托盘', 'tray')
        self._combo_close_behavior.addItem('直接退出程序', 'quit')
        form.addRow('关闭按钮行为', self._combo_close_behavior)

        self._combo_overlay_default_mode = _no_wheel(QComboBox())
        self._combo_overlay_default_mode.addItem('关闭', 'off')
        self._combo_overlay_default_mode.addItem('覆盖在原文上（整体）', 'over')
        self._combo_overlay_default_mode.addItem('覆盖在原文上（分段）', 'over_para')
        self._combo_overlay_default_mode.addItem('显示在原文下方', 'below')
        form.addRow('覆盖翻译默认模式', self._combo_overlay_default_mode)

        self._spin_overlay_font_delta = _no_wheel(QSpinBox())
        self._spin_overlay_font_delta.setRange(-12, 24)
        form.addRow('覆盖译文字号微调', self._spin_overlay_font_delta)

        self._para_check = QCheckBox()
        form.addRow('自动识别段落，分段翻译', self._para_check)

        self._para_ratio_spin = _no_wheel(QDoubleSpinBox())
        self._para_ratio_spin.setRange(0.1, 3.0)
        self._para_ratio_spin.setSingleStep(0.1)
        self._para_ratio_spin.setDecimals(1)
        self._para_ratio_spin.setToolTip('间距阈值越大，段落之间需要更大的垂直间距才会被切分')
        form.addRow('段落间距阈值（×行高）', self._para_ratio_spin)

        # checkbox 控制 spin 的可用性
        self._para_check.stateChanged.connect(
            lambda state: self._para_ratio_spin.setEnabled(bool(state))
        )

        gen_layout.addWidget(form_widget)

        # 临时模式行为分组
        temp_group = QGroupBox('临时模式')
        temp_layout = QVBoxLayout(temp_group)
        temp_layout.setSpacing(6)

        self._chk_temp_hide_bar = QCheckBox('临时模式下隐藏翻译条（翻译结果显示在选区框下方）')
        temp_layout.addWidget(self._chk_temp_hide_bar)

        hint_row = QHBoxLayout()
        hint_row.setContentsMargins(20, 0, 0, 0)
        self._btn_reset_hint = QPushButton('重置提示')
        self._btn_reset_hint.setFlat(True)
        self._btn_reset_hint.setStyleSheet(
            'QPushButton { color: #888; font-size: 11px; text-decoration: underline; border: none; }'
            'QPushButton:hover { color: #aaa; }'
            'QPushButton:disabled { color: #555; text-decoration: none; }'
        )
        self._btn_reset_hint.setFixedHeight(18)
        hint_row.addWidget(self._btn_reset_hint)
        hint_row.addStretch()
        temp_layout.addLayout(hint_row)

        self._btn_reset_hint.clicked.connect(self._on_reset_hint)
        gen_layout.addWidget(temp_group)

        # 快捷键分组（放在最下方）
        hotkey_group = QGroupBox('快捷键')
        hotkey_form = QFormLayout(hotkey_group)
        hotkey_form.setSpacing(8)

        self._edit_hotkey_select = QLineEdit()
        self._edit_hotkey_select.setPlaceholderText('如：alt+q')
        hotkey_form.addRow('框选热键', self._edit_hotkey_select)

        self._edit_hotkey_explain = QLineEdit()
        self._edit_hotkey_explain.setPlaceholderText('如：alt+e')
        hotkey_form.addRow('AI科普热键', self._edit_hotkey_explain)

        self._edit_hotkey_toggle = QLineEdit()
        self._edit_hotkey_toggle.setPlaceholderText('如：alt+w')
        hotkey_form.addRow('显示/隐藏框热键', self._edit_hotkey_toggle)

        self._edit_hotkey_mode_temp = QLineEdit()
        self._edit_hotkey_mode_temp.setPlaceholderText('如：alt+1')
        hotkey_form.addRow('切换临时模式热键', self._edit_hotkey_mode_temp)

        self._edit_hotkey_mode_fixed = QLineEdit()
        self._edit_hotkey_mode_fixed.setPlaceholderText('如：alt+2')
        hotkey_form.addRow('切换固定模式热键', self._edit_hotkey_mode_fixed)

        self._edit_hotkey_mode_multi = QLineEdit()
        self._edit_hotkey_mode_multi.setPlaceholderText('如：alt+3')
        hotkey_form.addRow('切换多框模式热键', self._edit_hotkey_mode_multi)

        self._edit_hotkey_mode_ai = QLineEdit()
        self._edit_hotkey_mode_ai.setPlaceholderText('如：alt+4')
        hotkey_form.addRow('切换AI框选热键', self._edit_hotkey_mode_ai)

        gen_layout.addWidget(hotkey_group)

        gen_scroll = QScrollArea()
        gen_scroll.setWidget(gen)
        gen_scroll.setWidgetResizable(True)
        gen_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        gen_scroll.setFrameShape(QFrame.NoFrame)
        tabs.addTab(gen_scroll, '通用')

        # ── 翻译来源 ──────────────────────────────────────────
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)
        tip = QLabel('💡 拖拽列表项可调整优先级，勾选则启用该后端。'
                     '本地词典仅适合单词速查，句子翻译效果较差；'
                     '国内推荐优先启用"搜狗"；Bing 是否可用取决于网络环境。'
                     '有道已封锁非官方调用，暂不可用。'
                     '谷歌翻译在中国大陆需要梯子，可根据网络情况开启。')
        tip.setWordWrap(True)
        tip.setStyleSheet('color: #888; font-size: 11px; padding: 4px 0;')
        src_layout.addWidget(tip)

        # ── 离线词典增强区域（勾选本地词典时才显示）────────────
        self._dict_group = QGroupBox('📖 离线词典增强（ECDICT）')
        self._dict_group.setVisible(False)
        dict_vbox = QVBoxLayout(self._dict_group)
        dict_vbox.setSpacing(6)
        dict_vbox.setContentsMargins(8, 6, 8, 6)

        dict_desc = QLabel(
            '下载 ECDICT 英汉词库（CSV ~90 MB），导入约 10 万条高频词条到本地数据库。'
            '自动尝试 Gitee 国内镜像 → GitHub Proxy → GitHub 直连，无需手动选择。'
        )
        dict_desc.setWordWrap(True)
        dict_desc.setStyleSheet('color: #666; font-size: 12px;')
        dict_vbox.addWidget(dict_desc)

        status_row = QHBoxLayout()
        status_row.addWidget(QLabel('状态：'))
        self._dict_status = QLabel('检测中...')
        status_row.addWidget(self._dict_status)
        status_row.addStretch()
        dict_vbox.addLayout(status_row)

        btn_row = QHBoxLayout()
        self._btn_dl_download = QPushButton('下载词典')
        self._btn_dl_download.setFixedWidth(110)
        self._btn_dl_download.clicked.connect(self._start_dict_download)
        self._btn_dl_delete = QPushButton('删除')
        self._btn_dl_delete.setFixedWidth(60)
        self._btn_dl_delete.clicked.connect(self._delete_dict)
        self._btn_dl_delete.setVisible(False)
        btn_row.addWidget(self._btn_dl_download)
        btn_row.addWidget(self._btn_dl_delete)
        btn_row.addStretch()
        dict_vbox.addLayout(btn_row)

        # 进度区（下载时才显示）
        self._dict_prog_widget = QWidget()
        prog_row = QHBoxLayout(self._dict_prog_widget)
        prog_row.setContentsMargins(0, 0, 0, 0)
        self._dict_progress = QProgressBar()
        self._dict_progress.setRange(0, 100)
        self._dict_progress.setTextVisible(False)
        self._dict_prog_label = QLabel()
        self._dict_prog_label.setStyleSheet('font-size: 11px; color: #555;')
        self._btn_dl_cancel = QPushButton('取消')
        self._btn_dl_cancel.setFixedWidth(50)
        self._btn_dl_cancel.clicked.connect(self._cancel_dict_download)
        prog_row.addWidget(self._dict_progress, 1)
        prog_row.addWidget(self._dict_prog_label)
        prog_row.addWidget(self._btn_dl_cancel)
        self._dict_prog_widget.setVisible(False)
        dict_vbox.addWidget(self._dict_prog_widget)

        src_layout.addWidget(self._dict_group)

        self._list_backends = QListWidget()
        self._list_backends.setDragDropMode(QListWidget.InternalMove)
        self._list_backends.setMinimumHeight(200)
        self._list_backends.itemChanged.connect(self._on_backend_item_changed)
        src_layout.addWidget(self._list_backends)

        tabs.addTab(src_tab, '翻译来源')

        # ── API 密钥 ──────────────────────────────────────────
        key_tab = QWidget()
        key_layout = QVBoxLayout(key_tab)
        key_layout.setSpacing(4)
        key_layout.setContentsMargins(8, 8, 8, 4)

        tip_label = QLabel('💡 点击右侧"获取密钥"直接跳转到对应平台申请页面，悬停输入框可查看说明。'
                           '国内推荐优先使用 <b>智谱（永久免费）</b>，注册即用，无需梯子。')
        tip_label.setTextFormat(Qt.RichText)
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet('color: #888; font-size: 11px; padding: 2px 0 6px 0;')
        key_layout.addWidget(tip_label)

        key_form_widget = QWidget()
        key_form = QFormLayout(key_form_widget)
        key_form.setSpacing(6)
        key_layout.addWidget(key_form_widget)
        key_layout.addStretch()

        self._key_fields = {}
        key_configs = [
            ('zhipu_key',       '智谱 API Key:',
             'https://open.bigmodel.cn/usercenter/apikeys',
             '智谱 AI 开放平台\nGLM-4-Flash 模型永久免费\n注册后在"API 密钥"页面创建'),
            ('siliconflow_key', '硅基流动 API Key:',
             'https://cloud.siliconflow.cn/account/ak',
             '硅基流动（SiliconFlow）\n注册赠送 14 元额度，多款开源模型可用\n在"API 密钥"页面创建'),
            ('moonshot_key',    'Kimi API Key:',
             'https://platform.moonshot.cn/console/api-keys',
             '月之暗面 Kimi\n新用户有免费体验额度\n在控制台"API 密钥"页面创建'),
            ('deepseek_key',    'DeepSeek API Key:',
             'https://platform.deepseek.com/api_keys',
             'DeepSeek AI\n价格极低、效果优秀，国内直连\n在平台"API Keys"页面创建'),
            ('baidu_appid',     '百度 AppID:',
             'https://fanyi-api.baidu.com/manage/developer',
             '百度翻译开放平台\n通用版每月 500 万字符免费\n需同时填写 AppID 和 SecretKey'),
            ('baidu_key',       '百度 SecretKey:',
             'https://fanyi-api.baidu.com/manage/developer',
             '百度翻译 SecretKey，与 AppID 配套使用\n在开放平台"管理控制台"中获取'),
            ('deepl_key',       'DeepL API Key:',
             'https://www.deepl.com/pro-api',
             'DeepL 翻译 API\n免费版每月 50 万字符\n注册后在账户页面 → API Keys 获取'),
            ('openai_key',      'OpenAI API Key:',
             'https://platform.openai.com/api-keys',
             'OpenAI GPT 系列\n需绑定信用卡，按量计费\n在 platform.openai.com → API keys 创建'),
            ('claude_key',      'Claude API Key:',
             'https://console.anthropic.com/settings/keys',
             'Anthropic Claude 系列\n在 console.anthropic.com → Settings → API Keys 创建'),
        ]
        for name, label, url, tooltip in key_configs:
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText('留空则此后端不可用')
            edit.setToolTip(tooltip)
            self._key_fields[name] = edit

            link = QLabel(f'<a href="{url}" style="color:#4a9eff;font-size:11px;text-decoration:none;">获取密钥 ↗</a>')
            link.setOpenExternalLinks(True)
            link.setToolTip(url)
            link.setFixedWidth(68)
            link.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            row_layout.addWidget(edit)
            row_layout.addWidget(link)

            key_form.addRow(label, row_widget)

        key_scroll = QScrollArea()
        key_scroll.setWidget(key_tab)
        key_scroll.setWidgetResizable(True)
        key_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        key_scroll.setFrameShape(QFrame.NoFrame)
        tabs.addTab(key_scroll, 'API 密钥')

        # ── 外观（皮肤选择）────────────────────────────────────────
        skin_tab = QWidget()
        skin_v = QVBoxLayout(skin_tab)
        skin_v.setSpacing(10)
        skin_v.setContentsMargins(10, 10, 10, 10)

        skin_tip = QLabel('选择一个皮肤，保存后立即生效。可随时切换，所有窗口同步更新。')
        skin_tip.setWordWrap(True)
        skin_tip.setStyleSheet('color: #888; font-size: 11px; padding-bottom: 4px;')
        skin_v.addWidget(skin_tip)

        # 卡片网格（每行 3 个）
        self._skin_cards: dict[str, _SkinCard] = {}
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(10)
        for idx, sid in enumerate(list_skins()):
            card = _SkinCard(sid, SKINS[sid])
            card.clicked.connect(self._on_skin_card_clicked)
            self._skin_cards[sid] = card
            grid.addWidget(card, idx // 3, idx % 3)
        skin_v.addWidget(grid_widget)

        variant_group = QGroupBox('按钮风格')
        variant_layout = QVBoxLayout(variant_group)
        variant_layout.setContentsMargins(10, 10, 10, 10)
        variant_layout.setSpacing(6)

        variant_help = QLabel(
            '皮肤控制整体配色。按钮风格控制强调色、字体和图标。'
        )
        variant_help.setWordWrap(True)
        variant_help.setStyleSheet('color: #888; font-size: 11px;')
        variant_layout.addWidget(variant_help)

        self._button_style_variant_group = QButtonGroup(self)
        self._button_style_variant_buttons: dict[str, QRadioButton] = {}
        for variant_id, label in (
            ('calm', 'A - 平静层次'),
            ('semantic', 'B - 功能色彩'),
        ):
            button = QRadioButton(label)
            self._button_style_variant_group.addButton(button)
            self._button_style_variant_buttons[variant_id] = button
            variant_layout.addWidget(button)

        skin_v.addWidget(variant_group)

        # ── 字体集 ──────────────────────────────────────────────
        font_group = QGroupBox('字体集')
        font_layout = QVBoxLayout(font_group)
        font_layout.setContentsMargins(10, 10, 10, 10)
        font_layout.setSpacing(6)

        font_help = QLabel('选择 None 跟随皮肤默认字体。')
        font_help.setWordWrap(True)
        font_help.setStyleSheet('color: #888; font-size: 11px;')
        font_layout.addWidget(font_help)

        self._combo_font_set = _no_wheel(QComboBox())
        self._combo_font_set.addItem('跟随皮肤默认', None)
        self._combo_font_set.addItem('Sans · Noto Sans SC', 'sans')
        self._combo_font_set.addItem('Mono · JetBrains Mono', 'mono')
        self._combo_font_set.addItem('Rounded · Nunito', 'rounded')
        self._combo_font_set.addItem('Serif · Noto Serif SC', 'serif')
        self._combo_font_set.addItem('Display · Orbitron', 'display')
        font_layout.addWidget(self._combo_font_set)
        skin_v.addWidget(font_group)

        # ── 图标集 ──────────────────────────────────────────────
        icon_group = QGroupBox('图标集')
        icon_layout = QVBoxLayout(icon_group)
        icon_layout.setContentsMargins(10, 10, 10, 10)
        icon_layout.setSpacing(6)

        icon_help = QLabel('选择 None 跟随皮肤默认图标粗细。')
        icon_help.setWordWrap(True)
        icon_help.setStyleSheet('color: #888; font-size: 11px;')
        icon_layout.addWidget(icon_help)

        self._combo_icon_set = _no_wheel(QComboBox())
        self._combo_icon_set.addItem('跟随皮肤默认', None)
        self._combo_icon_set.addItem('Phosphor Light', 'phosphor-light')
        self._combo_icon_set.addItem('Phosphor Regular', 'phosphor-regular')
        self._combo_icon_set.addItem('Phosphor Bold', 'phosphor-bold')
        icon_layout.addWidget(self._combo_icon_set)
        skin_v.addWidget(icon_group)

        skin_v.addStretch()

        skin_scroll = QScrollArea()
        skin_scroll.setWidget(skin_tab)
        skin_scroll.setWidgetResizable(True)
        skin_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        skin_scroll.setFrameShape(QFrame.NoFrame)
        tabs.addTab(skin_scroll, '外观')
        layout.addWidget(tabs)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_reset = QPushButton('恢复默认设置')
        btn_reset.clicked.connect(self._reset_defaults)
        btn_save = QPushButton('保存')
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton('取消')
        btn_cancel.clicked.connect(self.close)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load_values(self):
        timeout = self.settings.get('temp_box_timeout', 0)
        self._chk_auto_dismiss.setChecked(timeout > 0)
        self._spin_timeout.setValue(timeout if timeout > 0 else 3)
        self._spin_timeout.setEnabled(timeout > 0)
        self._spin_interval.setValue(self.settings.get('auto_translate_interval', 2))

        target = self.settings.get('target_language', 'zh-CN')
        idx = self._combo_target.findData(target)
        if idx >= 0:
            self._combo_target.setCurrentIndex(idx)

        pos = self.settings.get('result_bar_position', 'top')
        idx = self._combo_pos.findData(pos)
        if idx >= 0:
            self._combo_pos.setCurrentIndex(idx)

        size = self.settings.get('result_bar_size', 'default')
        idx = self._combo_size.findData(size)
        if idx >= 0:
            self._combo_size.setCurrentIndex(idx)

        close_behavior = self.settings.get('close_button_behavior', 'ask')
        idx = self._combo_close_behavior.findData(close_behavior)
        if idx >= 0:
            self._combo_close_behavior.setCurrentIndex(idx)

        overlay_default_mode = self.settings.get('overlay_default_mode', 'off')
        idx = self._combo_overlay_default_mode.findData(overlay_default_mode)
        if idx >= 0:
            self._combo_overlay_default_mode.setCurrentIndex(idx)

        self._spin_overlay_font_delta.setValue(self.settings.get('overlay_font_delta', 0))

        self._edit_hotkey_select.setText(self.settings.get('hotkey_select', 'alt+q'))
        self._edit_hotkey_explain.setText(self.settings.get('hotkey_explain', 'alt+e'))
        self._edit_hotkey_toggle.setText(self.settings.get('hotkey_toggle_boxes', 'alt+w'))
        self._edit_hotkey_mode_temp.setText(self.settings.get('hotkey_mode_temp', 'alt+1'))
        self._edit_hotkey_mode_fixed.setText(self.settings.get('hotkey_mode_fixed', 'alt+2'))
        self._edit_hotkey_mode_multi.setText(self.settings.get('hotkey_mode_multi', 'alt+3'))
        self._edit_hotkey_mode_ai.setText(self.settings.get('hotkey_mode_ai', 'alt+4'))

        saved_order = self.settings.get('translation_order', list(BACKEND_LABELS.keys()))
        # 过滤掉已删除的后端（如旧版 settings.json 残留的条目）
        known = set(BACKEND_LABELS.keys())
        order = [n for n in saved_order if n in known]
        # 把新增的后端补到末尾（防止漏项）
        for n in BACKEND_LABELS:
            if n not in order:
                order.append(n)
        enabled = set(self.settings.get('enabled_backends', ['google', 'zhipu']))
        self._list_backends.clear()
        for name in order:
            item = QListWidgetItem(BACKEND_LABELS.get(name, name))
            item.setData(Qt.UserRole, name)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            self._list_backends.addItem(item)

        keys = self.settings.get('api_keys', {})
        for name, edit in self._key_fields.items():
            edit.setText(keys.get(name, ''))

        self._para_check.setChecked(bool(self.settings.get('para_split_enabled', True)))
        self._para_ratio_spin.setValue(float(self.settings.get('para_gap_ratio', 0.5)))
        self._para_ratio_spin.setEnabled(self._para_check.isChecked())

        self._chk_temp_hide_bar.setChecked(self.settings.get('temp_mode_hide_bar', True))
        dismissed = self.settings.get('temp_mode_hint_dismissed', False)
        self._btn_reset_hint.setEnabled(dismissed)

        self._refresh_dict_status()
        self._sync_dict_group_visibility()

        # 皮肤卡片
        current_skin = self.settings.get('skin', 'deep_space')
        for sid, card in self._skin_cards.items():
            card.set_selected(sid == current_skin)

        current_variant = self.settings.get('button_style_variant', 'calm')
        if current_variant not in self._button_style_variant_buttons:
            current_variant = 'calm'
        self._button_style_variant_buttons[current_variant].setChecked(True)

        # 字体集 / 图标集
        font_set = self.settings.get('font_set', None)
        idx = self._combo_font_set.findData(font_set)
        self._combo_font_set.setCurrentIndex(max(0, idx))

        icon_set = self.settings.get('icon_set', None)
        idx = self._combo_icon_set.findData(icon_set)
        self._combo_icon_set.setCurrentIndex(max(0, idx))

    def _save(self):
        self.settings.set('temp_box_timeout',
                          self._spin_timeout.value() if self._chk_auto_dismiss.isChecked() else 0)
        self.settings.set('auto_translate_interval', self._spin_interval.value())
        self.settings.set('target_language', self._combo_target.currentData())
        self.settings.set('result_bar_position', self._combo_pos.currentData())
        self.settings.set('result_bar_size', self._combo_size.currentData())
        self.settings.set('close_button_behavior', self._combo_close_behavior.currentData())
        self.settings.set('overlay_default_mode', self._combo_overlay_default_mode.currentData())
        self.settings.set('overlay_font_delta', self._spin_overlay_font_delta.value())
        self.settings.set('hotkey_select', self._edit_hotkey_select.text())
        self.settings.set('hotkey_explain', self._edit_hotkey_explain.text())
        self.settings.set('hotkey_toggle_boxes', self._edit_hotkey_toggle.text())
        self.settings.set('hotkey_mode_temp', self._edit_hotkey_mode_temp.text())
        self.settings.set('hotkey_mode_fixed', self._edit_hotkey_mode_fixed.text())
        self.settings.set('hotkey_mode_multi', self._edit_hotkey_mode_multi.text())
        self.settings.set('hotkey_mode_ai', self._edit_hotkey_mode_ai.text())

        order, enabled = [], []
        for i in range(self._list_backends.count()):
            item = self._list_backends.item(i)
            name = item.data(Qt.UserRole)
            order.append(name)
            if item.checkState() == Qt.Checked:
                enabled.append(name)
        self.settings.set('translation_order', order)
        self.settings.set('enabled_backends', enabled)

        keys = {name: edit.text() for name, edit in self._key_fields.items()}
        self.settings.set('api_keys', keys)

        self.settings.set('para_split_enabled', self._para_check.isChecked())
        self.settings.set('para_gap_ratio', self._para_ratio_spin.value())
        self.settings.set('temp_mode_hide_bar', self._chk_temp_hide_bar.isChecked())

        # 皮肤
        selected_skin = next(
            (sid for sid, card in self._skin_cards.items() if card._selected),
            'deep_space'
        )
        self.settings.set('skin', selected_skin)

        selected_variant = next(
            (
                variant_id
                for variant_id, button in self._button_style_variant_buttons.items()
                if button.isChecked()
            ),
            'calm'
        )
        self.settings.set('button_style_variant', selected_variant)

        self.settings.set('font_set', self._combo_font_set.currentData())
        self.settings.set('icon_set', self._combo_icon_set.currentData())

        self.settings_saved.emit()
        self.close()

    # ── 皮肤 ───────────────────────────────────────────────────────

    def _on_skin_card_clicked(self, skin_id: str):
        for sid, card in self._skin_cards.items():
            card.set_selected(sid == skin_id)

    # ── 离线词典 ──────────────────────────────────────────────

    def _reset_defaults(self):
        from core.settings import DEFAULTS
        self._chk_auto_dismiss.setChecked(False)
        self._spin_timeout.setValue(3)
        self._spin_timeout.setEnabled(False)
        self._spin_interval.setValue(DEFAULTS['auto_translate_interval'])
        idx = self._combo_target.findData(DEFAULTS['target_language'])
        if idx >= 0:
            self._combo_target.setCurrentIndex(idx)
        idx = self._combo_pos.findData(DEFAULTS['result_bar_position'])
        if idx >= 0:
            self._combo_pos.setCurrentIndex(idx)
        idx = self._combo_size.findData(DEFAULTS['result_bar_size'])
        if idx >= 0:
            self._combo_size.setCurrentIndex(idx)
        idx = self._combo_close_behavior.findData(DEFAULTS['close_button_behavior'])
        if idx >= 0:
            self._combo_close_behavior.setCurrentIndex(idx)
        idx = self._combo_overlay_default_mode.findData(DEFAULTS['overlay_default_mode'])
        if idx >= 0:
            self._combo_overlay_default_mode.setCurrentIndex(idx)
        self._spin_overlay_font_delta.setValue(DEFAULTS['overlay_font_delta'])
        self._edit_hotkey_select.setText(DEFAULTS['hotkey_select'])
        self._edit_hotkey_explain.setText(DEFAULTS['hotkey_explain'])
        self._edit_hotkey_toggle.setText(DEFAULTS['hotkey_toggle_boxes'])
        self._edit_hotkey_mode_temp.setText(DEFAULTS['hotkey_mode_temp'])
        self._edit_hotkey_mode_fixed.setText(DEFAULTS['hotkey_mode_fixed'])
        self._edit_hotkey_mode_multi.setText(DEFAULTS['hotkey_mode_multi'])
        self._edit_hotkey_mode_ai.setText(DEFAULTS['hotkey_mode_ai'])

        order = DEFAULTS.get('translation_order', list(BACKEND_LABELS.keys()))
        enabled = set(DEFAULTS.get('enabled_backends', []))
        self._list_backends.clear()
        for name in order:
            if name not in BACKEND_LABELS:
                continue
            item = QListWidgetItem(BACKEND_LABELS.get(name, name))
            item.setData(Qt.UserRole, name)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            self._list_backends.addItem(item)

        for name in BACKEND_LABELS:
            if name in order:
                continue
            item = QListWidgetItem(BACKEND_LABELS.get(name, name))
            item.setData(Qt.UserRole, name)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            self._list_backends.addItem(item)

        default_skin = DEFAULTS.get('skin', 'deep_space')
        for sid, card in self._skin_cards.items():
            card.set_selected(sid == default_skin)

        default_variant = DEFAULTS.get('button_style_variant', 'calm')
        if default_variant not in self._button_style_variant_buttons:
            default_variant = 'calm'
        self._button_style_variant_buttons[default_variant].setChecked(True)

        self._combo_font_set.setCurrentIndex(0)
        self._combo_icon_set.setCurrentIndex(0)

        # 重置段落分割设置
        if hasattr(self, '_para_check'):
            self._para_check.setChecked(True)  # para_split_enabled 默认 True
        if hasattr(self, '_para_ratio_spin'):
            self._para_ratio_spin.setValue(0.5)  # para_gap_ratio 默认 0.5
            self._para_ratio_spin.setEnabled(True)
        # 重置临时模式设置
        if hasattr(self, '_chk_temp_hide_bar'):
            self._chk_temp_hide_bar.setChecked(True)  # temp_mode_hide_bar 默认 True

        # 重置引导向导（下次启动重新显示）
        self.settings.set('first_launch_done', False)

        self._sync_dict_group_visibility()

    def _on_reset_hint(self):
        self.settings.set('temp_mode_hint_dismissed', False)
        self._btn_reset_hint.setEnabled(False)

    def _sync_dict_group_visibility(self):
        """根据"本地词典"是否勾选来显示/隐藏 ECDICT 分组框。"""
        for i in range(self._list_backends.count()):
            item = self._list_backends.item(i)
            if item.data(Qt.UserRole) == 'dictionary':
                self._dict_group.setVisible(item.checkState() == Qt.Checked)
                return

    def _on_backend_item_changed(self, item):
        if item.data(Qt.UserRole) == 'dictionary':
            self._dict_group.setVisible(item.checkState() == Qt.Checked)

    def _refresh_dict_status(self):
        from translation.dict_db import DB_PATH
        import os
        import sqlite3
        if not os.path.exists(DB_PATH):
            self._dict_status.setText('未安装')
            self._dict_status.setStyleSheet('color: #888;')
            self._btn_dl_download.setText('下载词典')
            self._btn_dl_delete.setVisible(False)
            return
        try:
            conn = sqlite3.connect(DB_PATH)
            count = conn.execute('SELECT COUNT(*) FROM ecdict').fetchone()[0]
            conn.close()
            self._dict_status.setText(f'已安装  {count:,} 条词条')
            self._dict_status.setStyleSheet('color: #2a9d2a; font-weight: bold;')
            self._btn_dl_download.setText('重新下载')
            self._btn_dl_delete.setVisible(True)
        except Exception:
            self._dict_status.setText('文件损坏，建议重新下载')
            self._dict_status.setStyleSheet('color: #cc4444;')
            self._btn_dl_download.setText('重新下载')
            self._btn_dl_delete.setVisible(True)

    def _start_dict_download(self):
        from translation.dict_downloader import DictDownloadThread
        if hasattr(self, '_dl_thread') and self._dl_thread \
                and self._dl_thread.isRunning():
            return
        self._dl_thread = DictDownloadThread(self)
        self._dl_thread.progress.connect(self._on_dl_progress)
        self._dl_thread.finished.connect(self._on_dl_finished)
        self._dict_progress.setRange(0, 100)
        self._dict_progress.setValue(0)
        self._dict_prog_label.setText('')
        self._dict_prog_widget.setVisible(True)
        self._btn_dl_download.setEnabled(False)
        self._btn_dl_delete.setEnabled(False)
        self._dl_thread.start()

    def _cancel_dict_download(self):
        if hasattr(self, '_dl_thread') and self._dl_thread:
            self._dl_thread.abort()

    def _on_dl_progress(self, msg: str, pct: int):
        self._dict_prog_label.setText(msg)
        if pct < 0:
            self._dict_progress.setRange(0, 0)   # 不确定动画
        else:
            self._dict_progress.setRange(0, 100)
            self._dict_progress.setValue(pct)

    def _on_dl_finished(self, success: bool, detail: str):
        self._dict_prog_widget.setVisible(False)
        self._btn_dl_download.setEnabled(True)
        self._btn_dl_delete.setEnabled(True)
        self._refresh_dict_status()
        if success:
            QMessageBox.information(self, '词典下载完成', detail)
        else:
            QMessageBox.warning(self, '词典下载失败', detail)

    def _delete_dict(self):
        from translation.dict_db import DB_PATH
        import os
        if QMessageBox.question(
            self, '删除词典',
            '确认删除离线词典数据库？\n（可随时重新下载）',
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            import translation.dictionary as _dict_mod
            _dict_mod._db = None
            self._refresh_dict_status()
            QMessageBox.information(self, '删除成功', '离线词典已删除。')
        except Exception as e:
            QMessageBox.warning(self, '删除失败', str(e))

    def closeEvent(self, event):
        if hasattr(self, '_dl_thread') and self._dl_thread \
                and self._dl_thread.isRunning():
            self._dl_thread.abort()
            self._dl_thread.wait(5000)
        super().closeEvent(event)
