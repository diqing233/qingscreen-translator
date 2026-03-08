from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QLineEdit, QPushButton,
                              QTextEdit, QSplitter, QHeaderView, QMessageBox,
                              QAbstractItemView)
from PyQt5.QtCore import Qt


class HistoryWindow(QDialog):
    def __init__(self, history_db, parent=None):
        super().__init__(parent)
        self.history_db = history_db
        self.setWindowTitle('ScreenTranslator - 翻译历史')
        self.resize(720, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._records = []
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 搜索栏
        sr = QHBoxLayout()
        self._edit_search = QLineEdit()
        self._edit_search.setPlaceholderText('搜索原文或译文...')
        self._edit_search.textChanged.connect(self._on_search)
        btn_clear = QPushButton('清空历史')
        btn_clear.clicked.connect(self._clear)
        btn_refresh = QPushButton('刷新')
        btn_refresh.clicked.connect(self._load)
        sr.addWidget(self._edit_search)
        sr.addWidget(btn_refresh)
        sr.addWidget(btn_clear)
        layout.addLayout(sr)

        splitter = QSplitter(Qt.Vertical)

        # 表格
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(['时间', '原文', '译文', '来源'])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        # 详情
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(160)
        self._detail.setPlaceholderText('点击上方记录查看完整内容')
        splitter.addWidget(self._detail)

        layout.addWidget(splitter)

    def _load(self, records=None):
        if records is None:
            records = self.history_db.get_recent(300)
        self._records = records
        self._table.setRowCount(0)
        for r in records:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(r.get('created_at', '')[:16]))
            src = r.get('source_text', '')
            self._table.setItem(row, 1, QTableWidgetItem((src[:45] + '…') if len(src) > 45 else src))
            tgt = r.get('translated_text', '')
            self._table.setItem(row, 2, QTableWidgetItem((tgt[:45] + '…') if len(tgt) > 45 else tgt))
            self._table.setItem(row, 3, QTableWidgetItem(r.get('backend', '')))

    def _on_search(self, text):
        text = text.strip()
        if text:
            self._load(self.history_db.search(text))
        else:
            self._load()

    def _on_select(self):
        row = self._table.currentRow()
        if 0 <= row < len(self._records):
            r = self._records[row]
            self._detail.setHtml(
                f'<b>原文：</b><br>{r.get("source_text","")}<br><br>'
                f'<b>译文：</b><br>{r.get("translated_text","")}<br><br>'
                f'<small style="color:gray">来源: {r.get("backend","")} | '
                f'时间: {r.get("created_at","")}</small>'
            )

    def _clear(self):
        if QMessageBox.question(self, '确认', '确定要清空所有翻译历史吗？',
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.history_db.clear()
            self._load()
            self._detail.clear()
