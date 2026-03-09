"""
一次性脚本：下载 ECDICT 词库并构建离线 SQLite 词典。

用法：
    python tools/build_dict.py              # 下载全量（~37万条）
    python tools/build_dict.py --limit 100000   # 只取频率最高的 10万条
    python tools/build_dict.py --csv ecdict.csv # 使用本地已下载的 CSV

ECDICT 项目：https://github.com/skywind3000/ECDICT（MIT License）
下载地址：    https://github.com/skywind3000/ECDICT/releases 中的 ecdict.csv.zip
"""
import sys
import os
import argparse
import tempfile
import urllib.request
import zipfile
import time

# ── 路径设置 ──────────────────────────────────────────────────────────────────
_HERE  = os.path.dirname(os.path.abspath(__file__))
_ROOT  = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, 'src'))

from translation.dict_db import DictDB, DB_PATH

# ECDICT release zip（含 ecdict.csv）
ECDICT_ZIP_URL = (
    'https://github.com/skywind3000/ECDICT/releases/download/1.0.28/ecdict.csv.7z'
)
# 备用：直接从仓库下载 CSV（无压缩，~90MB，较慢）
ECDICT_CSV_URL = (
    'https://raw.githubusercontent.com/skywind3000/ECDICT/master/ecdict.csv'
)


def _progress_hook(block_num, block_size, total_size):
    if total_size <= 0:
        print(f'\r  已下载 {block_num * block_size / 1024 / 1024:.1f} MB', end='')
    else:
        pct = min(100, block_num * block_size * 100 // total_size)
        mb  = block_num * block_size / 1024 / 1024
        total_mb = total_size / 1024 / 1024
        bar = '█' * (pct // 5) + '░' * (20 - pct // 5)
        print(f'\r  [{bar}] {pct:3d}%  {mb:.1f}/{total_mb:.1f} MB', end='')


def download_csv(tmp_dir: str) -> str:
    """下载 ECDICT CSV，返回本地路径。优先下载 zip，失败则下载原始 CSV。"""
    # 先尝试下载 zip（体积更小）
    zip_path = os.path.join(tmp_dir, 'ecdict.csv.zip')
    csv_path = os.path.join(tmp_dir, 'ecdict.csv')

    # 直接下载 CSV（兼容性更好）
    print(f'正在从 GitHub 下载 ECDICT CSV（~90 MB）...')
    print(f'URL: {ECDICT_CSV_URL}')
    try:
        urllib.request.urlretrieve(ECDICT_CSV_URL, csv_path, _progress_hook)
        print()
        return csv_path
    except Exception as e:
        print(f'\n下载失败：{e}')
        raise


def main():
    parser = argparse.ArgumentParser(description='构建离线中英词典数据库')
    parser.add_argument('--csv',   default=None,
                        help='使用本地 ECDICT CSV 文件（跳过下载）')
    parser.add_argument('--limit', type=int, default=0,
                        help='最多导入 N 条（0=全部，建议 100000）')
    parser.add_argument('--db',    default=DB_PATH,
                        help=f'输出 SQLite 路径（默认：{DB_PATH}）')
    args = parser.parse_args()

    print('=' * 60)
    print('ScreenTranslator 离线词典构建工具')
    print('=' * 60)
    print(f'目标 DB：{args.db}')
    limit_desc = f'{args.limit:,} 条（频率最高）' if args.limit else '全部'
    print(f'导入数量：{limit_desc}')
    print()

    csv_path = args.csv
    tmp_dir  = None

    try:
        if csv_path is None:
            tmp_dir  = tempfile.mkdtemp(prefix='screentrans_dict_')
            csv_path = download_csv(tmp_dir)

        if not os.path.exists(csv_path):
            print(f'错误：找不到 CSV 文件：{csv_path}')
            sys.exit(1)

        size_mb = os.path.getsize(csv_path) / 1024 / 1024
        print(f'CSV 文件：{csv_path}  ({size_mb:.1f} MB)')
        print('正在解析并导入到 SQLite...')
        t0 = time.time()
        count = DictDB.build_from_csv(csv_path, db_path=args.db, limit=args.limit)
        elapsed = time.time() - t0

        db_mb = os.path.getsize(args.db) / 1024 / 1024
        print(f'\n✓ 完成！导入 {count:,} 条，耗时 {elapsed:.1f}s，DB 大小 {db_mb:.1f} MB')
        print(f'DB 路径：{args.db}')
        print()
        print('重启 ScreenTranslator 后词典后端将自动使用此数据库。')

    finally:
        if tmp_dir:
            import shutil
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass


if __name__ == '__main__':
    main()
