from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QSpinBox, QComboBox, QPushButton,
                              QListWidget, QListWidgetItem, QTabWidget,
                              QWidget, QFormLayout, QMessageBox,
                              QProgressBar, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt

BACKEND_LABELS = {
    'dictionary':   '📖 本地词典（离线极快）',
    'google':       '🌐 谷歌翻译（免费）',
    'baidu':        '🔵 百度翻译',
    'deepl':        '🟢 DeepL',
    'zhipu':        '🆓 智谱 GLM-4-Flash（永久免费）',
    'siliconflow':  '🆓 硅基流动（注册送 14 元）',
    'moonshot':     '🆓 月之暗面 Kimi（新用户赠额度）',
    'deepseek':     '🤖 DeepSeek AI',
    'openai':       '🤖 OpenAI GPT',
    'claude':       '🤖 Claude AI',
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
        form.addRow('临时框消失时间（秒）', self._spin_timeout)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 120)
        form.addRow('固定框自动翻译间隔（秒）', self._spin_interval)

        self._combo_target = QComboBox()
        for code, name in [('zh-CN', '简体中文'), ('zh-TW', '繁体中文'), ('en', '英语'),
                           ('ja', '日语'), ('ko', '韩语'), ('fr', '法语'),
                           ('de', '德语'), ('es', '西班牙语'), ('ru', '俄语')]:
            self._combo_target.addItem(name, code)
        form.addRow('默认翻译目标语言', self._combo_target)

        self._combo_pos = QComboBox()
        self._combo_pos.addItem('中央', 'center')
        self._combo_pos.addItem('顶部', 'top')
        self._combo_pos.addItem('底部', 'bottom')
        self._combo_pos.addItem('左侧', 'left')
        self._combo_pos.addItem('右侧', 'right')
        self._combo_pos.addItem('上次位置', 'last')
        form.addRow('结果条位置', self._combo_pos)

        self._combo_size = QComboBox()
        self._combo_size.addItem('默认大小', 'default')
        self._combo_size.addItem('上次大小', 'last')
        form.addRow('结果条大小', self._combo_size)

        self._edit_hotkey_select = QLineEdit()
        self._edit_hotkey_select.setPlaceholderText('如：alt+q')
        form.addRow('框选热键', self._edit_hotkey_select)

        self._edit_hotkey_explain = QLineEdit()
        self._edit_hotkey_explain.setPlaceholderText('如：alt+e')
        form.addRow('AI解释热键', self._edit_hotkey_explain)

        self._edit_hotkey_toggle = QLineEdit()
        self._edit_hotkey_toggle.setPlaceholderText('如：alt+w')
        form.addRow('显示/隐藏框热键', self._edit_hotkey_toggle)

        self._edit_hotkey_mode_temp = QLineEdit()
        self._edit_hotkey_mode_temp.setPlaceholderText('如：alt+1')
        form.addRow('切换临时模式热键', self._edit_hotkey_mode_temp)

        self._edit_hotkey_mode_fixed = QLineEdit()
        self._edit_hotkey_mode_fixed.setPlaceholderText('如：alt+2')
        form.addRow('切换固定模式热键', self._edit_hotkey_mode_fixed)

        self._edit_hotkey_mode_multi = QLineEdit()
        self._edit_hotkey_mode_multi.setPlaceholderText('如：alt+3')
        form.addRow('切换多框模式热键', self._edit_hotkey_mode_multi)

        tabs.addTab(gen, '通用')

        # ── 翻译来源 ──────────────────────────────────────────
        src_tab = QWidget()
        src_layout = QVBoxLayout(src_tab)
        tip = QLabel('💡 拖拽列表项可调整优先级，勾选则启用该后端。'
                     '本地词典仅适合单词速查，句子翻译效果较差；'
                     '联网建议启用"谷歌翻译 + 智谱 GLM-4-Flash"免费组合，覆盖面广且无需付费。')
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
        key_form = QFormLayout(key_tab)
        key_form.setSpacing(6)

        self._key_fields = {}
        key_configs = [
            ('baidu_appid',      '百度 AppID:'),
            ('baidu_key',        '百度 SecretKey:'),
            ('deepl_key',        'DeepL API Key:'),
            ('zhipu_key',        '智谱 API Key:'),
            ('siliconflow_key',  '硅基流动 API Key:'),
            ('moonshot_key',     'Kimi API Key:'),
            ('deepseek_key',     'DeepSeek API Key:'),
            ('openai_key',       'OpenAI API Key:'),
            ('claude_key',       'Claude API Key:'),
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

        size = self.settings.get('result_bar_size', 'default')
        idx = self._combo_size.findData(size)
        if idx >= 0:
            self._combo_size.setCurrentIndex(idx)

        self._edit_hotkey_select.setText(self.settings.get('hotkey_select', 'alt+q'))
        self._edit_hotkey_explain.setText(self.settings.get('hotkey_explain', 'alt+e'))
        self._edit_hotkey_toggle.setText(self.settings.get('hotkey_toggle_boxes', 'alt+w'))
        self._edit_hotkey_mode_temp.setText(self.settings.get('hotkey_mode_temp', 'alt+1'))
        self._edit_hotkey_mode_fixed.setText(self.settings.get('hotkey_mode_fixed', 'alt+2'))
        self._edit_hotkey_mode_multi.setText(self.settings.get('hotkey_mode_multi', 'alt+3'))

        saved_order = self.settings.get('translation_order', list(BACKEND_LABELS.keys()))
        # 过滤掉已删除的后端（如旧版 settings.json 残留的条目）
        known = set(BACKEND_LABELS.keys())
        order = [n for n in saved_order if n in known]
        # 把新增的后端补到末尾（防止漏项）
        for n in BACKEND_LABELS:
            if n not in order:
                order.append(n)
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

        self._refresh_dict_status()
        self._sync_dict_group_visibility()

    def _save(self):
        self.settings.set('temp_box_timeout', self._spin_timeout.value())
        self.settings.set('auto_translate_interval', self._spin_interval.value())
        self.settings.set('target_language', self._combo_target.currentData())
        self.settings.set('result_bar_position', self._combo_pos.currentData())
        self.settings.set('result_bar_size', self._combo_size.currentData())
        self.settings.set('hotkey_select', self._edit_hotkey_select.text())
        self.settings.set('hotkey_explain', self._edit_hotkey_explain.text())
        self.settings.set('hotkey_toggle_boxes', self._edit_hotkey_toggle.text())
        self.settings.set('hotkey_mode_temp', self._edit_hotkey_mode_temp.text())
        self.settings.set('hotkey_mode_fixed', self._edit_hotkey_mode_fixed.text())
        self.settings.set('hotkey_mode_multi', self._edit_hotkey_mode_multi.text())

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

    # ── 离线词典 ──────────────────────────────────────────────

    def _reset_defaults(self):
        from core.settings import DEFAULTS
        self._spin_timeout.setValue(DEFAULTS['temp_box_timeout'])
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
        self._edit_hotkey_select.setText(DEFAULTS['hotkey_select'])
        self._edit_hotkey_explain.setText(DEFAULTS['hotkey_explain'])
        self._edit_hotkey_toggle.setText(DEFAULTS['hotkey_toggle_boxes'])
        self._edit_hotkey_mode_temp.setText(DEFAULTS['hotkey_mode_temp'])
        self._edit_hotkey_mode_fixed.setText(DEFAULTS['hotkey_mode_fixed'])
        self._edit_hotkey_mode_multi.setText(DEFAULTS['hotkey_mode_multi'])

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
