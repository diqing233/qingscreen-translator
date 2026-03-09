"""
SQLite 离线词典后端。
数据源：ECDICT（~37万英汉条目，MIT 协议）
DB 路径：~/.screen_translator/dict.db
首次使用前需运行 tools/build_dict.py 构建数据库。
"""
import os
import re
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.expanduser('~/.screen_translator/dict.db')

# ECDICT translation 字段格式示例：
#   "na. 名词含义\nv. 动词含义\nadj. 形容词含义"
_POS_PREFIX = re.compile(r'^[a-z]+\.\s*')


def _clean(raw: str) -> Optional[str]:
    """从 ECDICT translation 字段提取简洁中文释义（取前 2 条含义）。"""
    if not raw:
        return None
    # ECDICT CSV 用字面 \n（两字符）作为行分隔符
    raw = raw.replace('\\n', '\n')
    parts = []
    for line in raw.split('\n'):
        line = line.strip()
        if not line:
            continue
        line = _POS_PREFIX.sub('', line).strip()
        # 只保留含中文的行
        if line and re.search(r'[\u4e00-\u9fff]', line):
            parts.append(line)
        if len(parts) >= 2:
            break
    return '；'.join(parts) if parts else None


class DictDB:
    """线程安全的只读 SQLite 词典。"""

    def __init__(self, db_path: str = DB_PATH):
        self._path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._ready = False
        self._try_open()

    def _try_open(self):
        if not os.path.exists(self._path):
            return
        try:
            conn = sqlite3.connect(self._path, check_same_thread=False)
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='ecdict'"
            ).fetchone()
            if not row:
                conn.close()
                return
            count = conn.execute('SELECT COUNT(*) FROM ecdict').fetchone()[0]
            if count > 0:
                self._conn = conn
                self._ready = True
                logger.info(f'DictDB 已加载：{count:,} 条 ({self._path})')
        except Exception as e:
            logger.warning(f'DictDB 打开失败：{e}')

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def entry_count(self) -> int:
        if not self._ready:
            return 0
        try:
            return self._conn.execute('SELECT COUNT(*) FROM ecdict').fetchone()[0]
        except Exception:
            return 0

    def lookup_en(self, word: str) -> Optional[str]:
        """英→中查询，返回中文释义字符串，未命中返回 None。"""
        if not self._ready:
            return None
        try:
            row = self._conn.execute(
                'SELECT translation FROM ecdict WHERE word=? COLLATE NOCASE LIMIT 1',
                (word,)
            ).fetchone()
            if row:
                return _clean(row[0])
        except Exception as e:
            logger.debug(f'DictDB lookup_en error: {e}')
        return None

    def lookup_zh(self, word: str) -> Optional[str]:
        """中→英查询（精确匹配 translation 字段），返回英文词，未命中返回 None。"""
        if not self._ready:
            return None
        try:
            row = self._conn.execute(
                "SELECT word FROM ecdict WHERE translation LIKE ? LIMIT 1",
                (f'%{word}%',)
            ).fetchone()
            if row:
                return row[0]
        except Exception as e:
            logger.debug(f'DictDB lookup_zh error: {e}')
        return None

    # ── 构建 ──────────────────────────────────────────────────────────────────

    @classmethod
    def build_from_csv(cls, csv_path: str, db_path: str = DB_PATH,
                       limit: int = 0) -> int:
        """
        从 ECDICT CSV 文件构建 SQLite 数据库。
        limit=0 表示导入全部；limit>0 则取频率最高的前 N 条。
        返回实际导入条数。
        """
        import csv as _csv

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute('DROP TABLE IF EXISTS ecdict')
        conn.execute('''
            CREATE TABLE ecdict (
                word        TEXT PRIMARY KEY,
                translation TEXT,
                frq         INTEGER DEFAULT 0
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_word ON ecdict(word COLLATE NOCASE)')

        batch, total = [], 0
        with open(csv_path, encoding='utf-8', newline='') as f:
            reader = _csv.DictReader(f)
            rows_raw = []
            for row in reader:
                w   = (row.get('word') or '').strip()
                tr  = (row.get('translation') or '').strip()
                frq = int(row.get('frq') or 0)
                if w and tr and re.search(r'[\u4e00-\u9fff]', tr):
                    rows_raw.append((w, tr, frq))

        # 按频率降序，取前 limit 条
        rows_raw.sort(key=lambda x: x[2], reverse=True)
        if limit > 0:
            rows_raw = rows_raw[:limit]

        for row in rows_raw:
            batch.append(row)
            total += 1
            if len(batch) >= 2000:
                conn.executemany(
                    'INSERT OR REPLACE INTO ecdict VALUES (?,?,?)', batch)
                batch.clear()
        if batch:
            conn.executemany(
                'INSERT OR REPLACE INTO ecdict VALUES (?,?,?)', batch)

        conn.commit()
        conn.execute('ANALYZE')
        conn.close()
        logger.info(f'DictDB 构建完成：{total:,} 条 → {db_path}')
        return total
