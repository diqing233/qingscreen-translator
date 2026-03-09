"""
后台下载并构建 ECDICT 离线词典。
自动尝试 Gitee（国内） → GitHub Proxy → GitHub 直连 三个下载源。
"""
import os
import tempfile
import shutil
import urllib.request
import logging

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

# 下载源列表（按优先级排列，国内优先）
ECDICT_SOURCES = [
    ('Gitee 国内镜像',
     'https://gitee.com/skywind3000/ECDICT/raw/master/ecdict.csv'),
    ('GitHub Proxy',
     'https://mirror.ghproxy.com/https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv'),
    ('GitHub 直连',
     'https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv'),
]

# 取频率最高的前 N 条，0 = 全部 (~37万)
DEFAULT_LIMIT = 100_000


class DictDownloadThread(QThread):
    """后台下载并构建 ECDICT SQLite 词典。"""

    # (消息, 百分比；-1 = 不确定进度/动画模式)
    progress = pyqtSignal(str, int)
    # (成功, 详情消息)
    finished = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        from translation.dict_db import DictDB, DB_PATH

        tmp_dir = tempfile.mkdtemp(prefix='screentrans_dict_')
        csv_path = os.path.join(tmp_dir, 'ecdict.csv')

        try:
            # ── 依次尝试各下载源 ──────────────────────────────────────
            downloaded = False
            last_err = ''
            for name, url in ECDICT_SOURCES:
                if self._abort:
                    self.finished.emit(False, '已取消')
                    return
                self.progress.emit(f'正在连接 {name}...', 0)
                try:
                    self._download(url, csv_path, name)
                    downloaded = True
                    break
                except Exception as e:
                    last_err = str(e)
                    logger.warning(f'DictDownload [{name}] 失败：{e}')
                    if os.path.exists(csv_path):
                        os.remove(csv_path)

            if not downloaded:
                self.finished.emit(False, f'所有下载源均失败：{last_err}')
                return

            if self._abort:
                self.finished.emit(False, '已取消')
                return

            # ── 导入 SQLite ───────────────────────────────────────────
            self.progress.emit('正在写入数据库（约需 10~30 秒）...', -1)
            count = DictDB.build_from_csv(csv_path, db_path=DB_PATH,
                                          limit=DEFAULT_LIMIT)

            # 重置全局单例，使后续查询自动加载新数据库
            import translation.dictionary as _dict_mod
            _dict_mod._db = None

            self.finished.emit(True, f'导入完成，共 {count:,} 条词条')

        except Exception as e:
            logger.exception('DictDownloadThread 异常')
            self.finished.emit(False, str(e))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _download(self, url: str, dest: str, source_name: str):
        """从 url 下载到 dest，通过 progress 信号报告进度。"""
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; ScreenTranslator)'},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            total = int(resp.headers.get('Content-Length') or 0)
            received = 0
            with open(dest, 'wb') as f:
                while not self._abort:
                    chunk = resp.read(65536)  # 64 KB
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    mb = received / 1_048_576
                    if total > 0:
                        pct = min(99, received * 100 // total)
                        total_mb = total / 1_048_576
                        self.progress.emit(
                            f'{source_name}  {mb:.1f} / {total_mb:.1f} MB', pct
                        )
                    else:
                        self.progress.emit(
                            f'{source_name}  {mb:.1f} MB 已下载', -1
                        )
