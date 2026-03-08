import sqlite3
import os
from datetime import datetime
from typing import List, Dict

class HistoryDB:
    def __init__(self, path: str = None):
        if path is None:
            app_dir = os.path.expanduser('~/.screen_translator')
            os.makedirs(app_dir, exist_ok=True)
            path = os.path.join(app_dir, 'history.db')
        self._path = path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self._path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    source_lang TEXT,
                    target_lang TEXT,
                    backend TEXT
                )
            ''')

    def add(self, source: str, translated: str, src_lang: str, tgt_lang: str, backend: str):
        with self._conn() as conn:
            conn.execute(
                'INSERT INTO history (created_at, source_text, translated_text, source_lang, target_lang, backend) VALUES (?,?,?,?,?,?)',
                (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), source, translated, src_lang, tgt_lang, backend)
            )

    def get_recent(self, limit: int = 50) -> List[Dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def search(self, keyword: str) -> List[Dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                'SELECT * FROM history WHERE source_text LIKE ? OR translated_text LIKE ? ORDER BY id DESC LIMIT 100',
                (f'%{keyword}%', f'%{keyword}%')
            ).fetchall()
        return [dict(r) for r in rows]

    def clear(self):
        with self._conn() as conn:
            conn.execute('DELETE FROM history')
