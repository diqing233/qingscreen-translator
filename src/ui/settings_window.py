from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QSpinBox, QComboBox, QPushButton,
                              QListWidget, QListWidgetItem, QTabWidget,
                              QWidget, QFormLayout, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt

BACKEND_LABELS = {
    'dictionary': '📖 本地词典（离线极快）',
    'google':     '🌐 谷歌翻译（免费）',
    'baidu':      '🔵 百度翻译',
    'deepl':      '🟢 DeepL',
    'deepseek':   '🤖 DeepSeek AI',
    'openai':     '🤖 OpenAI GPT',
    'claude':     '🤖 Claude AI',
}


class SettingsWindow(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle('ScreenTranslator - 设置')
        self.setMinimumWidth(520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        tabs = QTabWidget()

        # ── 通用 ──────────────────────────────────────────────
        gen = QWidget()
        form = QFormLayout(gen)
        form.setSpacing(8)

        self._spin_timeout = QSpinBox()
        self._spin_timeout.setRange(1, 60)
        self._spin_timeout.setSuffix(' 秒')
        form.addRow('临时框消失时间:', self._spin_timeout)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 120)
        self._spin_interval.setSuffix(' 秒')
        form.addRow('固定框自动翻译间隔:', self._spin_interval)

        self._combo_target = QComboBox()
        for code, name in [('zh-CN', '简体中文'), ('zh-TW', '繁体中文'), ('en', '英语'),
                           ('ja', '日语'), ('ko', '韩语'), ('fr', '法语'),
                           ('de', '德语'), ('es', '西班牙语'), ('ru', '俄语')]:
            self._combo_target.addItem(name, code)
        form.addRow('默认翻译目标语言:', self._combo_target)

        self._combo_pos = QComboBox()
        self._combo_pos.addItem('顶部', 'top')
        self._combo_pos.addItem('底部', 'bottom')
        form.addRow('结果条位置:', self._combo_pos)

        self._edit_hotkey_select = QLineEdit()
        self._edit_hotkey_select.setPlaceholderText('如：alt+q')
        form.addRow('框选热键:', self._edit_hotkey_select)

        self._edit_hotkey_explain = QLineEdit()
        self._edit_hotkey_explain.setPlaceholderText('如：alt+e')
        form.addRow('AI解释热键:', self._edit_hotkey_explain)

        self._edit_hotkey_toggle = QLineEdit()
        self._edit_hotkey_toggle.setPlaceholderText('如：alt+w')
        form.addRow('显示/隐藏框热键:', self._edit_hotkey_toggle)

        tabs.addTab(gen, '通用')

        # ── 翻译来源 ──────────────────────────────────────────
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)
        tip = QLabel('💡 提示：追求高效稳定？可将已配置的AI翻译拖到免费API前面，享受更快更准确的翻译体验。\n'
                     '拖拽列表项可调整优先级，勾选则启用该后端。')
        tip.setWordWrap(True)
        tip.setStyleSheet('color: #888; font-size: 11px; padding: 4px 0;')
        src_layout.addWidget(tip)

        self._list_backends = QListWidget()
        self._list_backends.setDragDropMode(QListWidget.InternalMove)
        self._list_backends.setMinimumHeight(200)
        src_layout.addWidget(self._list_backends)
        tabs.addTab(src_tab, '翻译来源')

        # ── API 密钥 ──────────────────────────────────────────
        key_tab = QWidget()
        key_form = QFormLayout(key_tab)
        key_form.setSpacing(6)

        self._key_fields = {}
        key_configs = [
            ('baidu_appid', '百度 AppID:'),
            ('baidu_key',   '百度 SecretKey:'),
            ('deepl_key',   'DeepL API Key:'),
            ('deepseek_key','DeepSeek API Key:'),
            ('openai_key',  'OpenAI API Key:'),
            ('claude_key',  'Claude API Key:'),
        ]
        for name, label in key_configs:
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText('留空则此后端不可用')
            self._key_fields[name] = edit
            key_form.addRow(label, edit)

        tabs.addTab(key_tab, 'API 密钥')
        layout.addWidget(tabs)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_save = QPushButton('保存')
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton('取消')
        btn_cancel.clicked.connect(self.close)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load_values(self):
        self._spin_timeout.setValue(self.settings.get('temp_box_timeout', 3))
        self._spin_interval.setValue(self.settings.get('auto_translate_interval', 2))

        target = self.settings.get('target_language', 'zh-CN')
        idx = self._combo_target.findData(target)
        if idx >= 0:
            self._combo_target.setCurrentIndex(idx)

        pos = self.settings.get('result_bar_position', 'top')
        idx = self._combo_pos.findData(pos)
        if idx >= 0:
            self._combo_pos.setCurrentIndex(idx)

        self._edit_hotkey_select.setText(self.settings.get('hotkey_select', 'alt+q'))
        self._edit_hotkey_explain.setText(self.settings.get('hotkey_explain', 'alt+e'))
        self._edit_hotkey_toggle.setText(self.settings.get('hotkey_toggle_boxes', 'alt+w'))

        order = self.settings.get('translation_order', list(BACKEND_LABELS.keys()))
        enabled = set(self.settings.get('enabled_backends', ['dictionary', 'google']))
        self._list_backends.clear()
        for name in order:
            item = QListWidgetItem(BACKEND_LABELS.get(name, name))
            item.setData(Qt.UserRole, name)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            self._list_backends.addItem(item)

        keys = self.settings.get('api_keys', {})
        for name, edit in self._key_fields.items():
            edit.setText(keys.get(name, ''))

    def _save(self):
        self.settings.set('temp_box_timeout', self._spin_timeout.value())
        self.settings.set('auto_translate_interval', self._spin_interval.value())
        self.settings.set('target_language', self._combo_target.currentData())
        self.settings.set('result_bar_position', self._combo_pos.currentData())
        self.settings.set('hotkey_select', self._edit_hotkey_select.text())
        self.settings.set('hotkey_explain', self._edit_hotkey_explain.text())
        self.settings.set('hotkey_toggle_boxes', self._edit_hotkey_toggle.text())

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

        self.settings_saved.emit()
        self.close()
