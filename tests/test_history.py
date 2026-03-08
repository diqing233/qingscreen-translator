import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import tempfile, pytest
from core.history import HistoryDB

def make_db():
    f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    f.close()
    return HistoryDB(f.name)

def test_add_and_fetch():
    db = make_db()
    db.add('Hello world', '你好世界', 'en', 'zh-CN', 'google')
    records = db.get_recent(10)
    assert len(records) == 1
    assert records[0]['source_text'] == 'Hello world'
    assert records[0]['translated_text'] == '你好世界'
    assert records[0]['backend'] == 'google'

def test_search():
    db = make_db()
    db.add('Hello world', '你好世界', 'en', 'zh-CN', 'google')
    db.add('Good morning', '早上好', 'en', 'zh-CN', 'deepseek')
    results = db.search('Hello')
    assert len(results) == 1
    assert results[0]['source_text'] == 'Hello world'

def test_clear():
    db = make_db()
    db.add('Hello', '你好', 'en', 'zh-CN', 'google')
    db.clear()
    assert db.get_recent(10) == []

def test_limit():
    db = make_db()
    for i in range(5):
        db.add(f'text{i}', f'译文{i}', 'en', 'zh-CN', 'google')
    assert len(db.get_recent(3)) == 3
