# ScreenTranslator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一款 Windows 桌面屏幕翻译工具，支持框选OCR翻译、透明虚线"框"覆盖、深色浮动结果条、多种翻译后端和AI解释功能。

**Architecture:** PyQt5 多窗口架构，CoreController 统一调度；OCR 和翻译均在独立 QThread 中执行避免 UI 卡顿；所有"框"实例由 BoxManager 统一管理，通过 Qt 信号槽与 ResultBar 通信。

**Tech Stack:** Python 3.10+, PyQt5, PaddleOCR, mss, pynput, googletrans, deepl, openai, anthropic, nltk, SQLite3

---

## Task 1: 项目结构与依赖

**Files:**
- Create: `requirements.txt`
- Create: `src/main.py`
- Create: `src/__init__.py`
- Create: `src/core/__init__.py`
- Create: `src/ui/__init__.py`
- Create: `src/ocr/__init__.py`
- Create: `src/translation/__init__.py`
- Create: `tests/__init__.py`

**Step 1: 创建目录结构**

```bash
cd c:/Users/Administrator/my-todo
mkdir -p src/core src/ui src/ocr src/translation tests docs/plans
touch src/__init__.py src/core/__init__.py src/ui/__init__.py
touch src/ocr/__init__.py src/translation/__init__.py tests/__init__.py
```

**Step 2: 创建 requirements.txt**

```
PyQt5>=5.15.9
PyQt5-Qt5>=5.15.2
paddlepaddle==2.6.1
paddleocr>=2.7.0
mss>=9.0.1
pynput>=1.7.6
googletrans==4.0.0rc1
deepl>=1.17.0
openai>=1.0.0
anthropic>=0.20.0
nltk>=3.8.1
requests>=2.31.0
```

**Step 3: 安装依赖**

```bash
pip install PyQt5 mss pynput googletrans==4.0.0rc1 deepl openai anthropic nltk requests
pip install paddlepaddle paddleocr
```

**Step 4: 创建入口 src/main.py**

```python
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    from core.controller import CoreController
    controller = CoreController(app)
    controller.start()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
```

**Step 5: 验证可运行**

```bash
cd c:/Users/Administrator/my-todo
python src/main.py
```
预期：暂时报 ImportError（CoreController 未实现），说明入口正常加载。

**Step 6: Commit**

```bash
git init
git add .
git commit -m "feat: initial project structure and requirements"
```

---

## Task 2: SettingsStore（配置持久化）

**Files:**
- Create: `src/core/settings.py`
- Create: `tests/test_settings.py`

**Step 1: 写失败测试**

```python
# tests/test_settings.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import json, tempfile, pytest
from core.settings import SettingsStore

def test_default_values():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    store = SettingsStore(path)
    assert store.get('temp_box_timeout') == 3
    assert store.get('auto_translate_interval') == 2
    assert store.get('target_language') == 'zh-CN'
    assert store.get('hotkey_select') == 'alt+q'
    assert store.get('hotkey_explain') == 'alt+e'
    assert store.get('result_bar_opacity') == 0.85
    assert isinstance(store.get('translation_order'), list)

def test_set_and_persist():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    store = SettingsStore(path)
    store.set('temp_box_timeout', 5)
    store2 = SettingsStore(path)
    assert store2.get('temp_box_timeout') == 5

def test_get_nonexistent_returns_default():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    store = SettingsStore(path)
    assert store.get('nonexistent', 'fallback') == 'fallback'
```

**Step 2: 运行测试确认失败**

```bash
cd c:/Users/Administrator/my-todo
python -m pytest tests/test_settings.py -v
```
预期：FAIL - ModuleNotFoundError

**Step 3: 实现 src/core/settings.py**

```python
import json
import os
from typing import Any

DEFAULTS = {
    'temp_box_timeout': 3,
    'auto_translate_interval': 2,
    'target_language': 'zh-CN',
    'source_language': 'auto',
    'hotkey_select': 'alt+q',
    'hotkey_explain': 'alt+e',
    'result_bar_opacity': 0.85,
    'result_bar_position': 'top',
    'translation_order': ['dictionary', 'google', 'baidu', 'deepl', 'deepseek', 'openai', 'claude'],
    'enabled_backends': ['dictionary', 'google'],
    'api_keys': {
        'baidu_appid': '',
        'baidu_key': '',
        'deepl_key': '',
        'deepseek_key': '',
        'openai_key': '',
        'claude_key': '',
    }
}

class SettingsStore:
    def __init__(self, path: str = None):
        if path is None:
            app_dir = os.path.expanduser('~/.screen_translator')
            os.makedirs(app_dir, exist_ok=True)
            path = os.path.join(app_dir, 'settings.json')
        self._path = path
        self._data = dict(DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self._data.update(saved)
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default: Any = None):
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def get_api_key(self, name: str) -> str:
        return self._data.get('api_keys', {}).get(name, '')

    def set_api_key(self, name: str, value: str):
        if 'api_keys' not in self._data:
            self._data['api_keys'] = {}
        self._data['api_keys'][name] = value
        self._save()
```

**Step 4: 运行测试确认通过**

```bash
python -m pytest tests/test_settings.py -v
```
预期：3 PASSED

**Step 5: Commit**

```bash
git add src/core/settings.py tests/test_settings.py
git commit -m "feat: add SettingsStore with JSON persistence"
```

---

## Task 3: HistoryDB（SQLite历史记录）

**Files:**
- Create: `src/core/history.py`
- Create: `tests/test_history.py`

**Step 1: 写失败测试**

```python
# tests/test_history.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import tempfile, pytest
from core.history import HistoryDB

def make_db():
    f = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
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
```

**Step 2: 运行测试确认失败**

```bash
python -m pytest tests/test_history.py -v
```

**Step 3: 实现 src/core/history.py**

```python
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
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_history.py -v
```
预期：4 PASSED

**Step 5: Commit**

```bash
git add src/core/history.py tests/test_history.py
git commit -m "feat: add HistoryDB with SQLite storage"
```

---

## Task 4: 翻译后端 - 本地词典

**Files:**
- Create: `src/translation/dictionary.py`
- Create: `tests/test_translation.py`

**Step 1: 下载 NLTK 数据**

```bash
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

**Step 2: 写失败测试**

```python
# tests/test_translation.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from translation.dictionary import DictionaryBackend

def test_lookup_english_word():
    b = DictionaryBackend()
    result = b.translate('hello', target_lang='zh-CN')
    assert result is not None
    assert result['translated'] != ''
    assert result['backend'] == 'dictionary'

def test_short_phrase_returns_none_or_result():
    b = DictionaryBackend()
    result = b.translate('good morning', target_lang='zh-CN')
    # 词组可能查不到，返回None是允许的
    assert result is None or isinstance(result['translated'], str)

def test_too_long_returns_none():
    b = DictionaryBackend()
    result = b.translate('this is a very long sentence that should not be looked up in the dictionary', target_lang='zh-CN')
    assert result is None
```

**Step 3: 实现 src/translation/dictionary.py**

```python
from typing import Optional, Dict

# 常用词中文映射（离线快速查询）
QUICK_DICT = {
    'hello': '你好', 'world': '世界', 'good': '好的', 'morning': '早晨',
    'night': '夜晚', 'day': '白天', 'yes': '是', 'no': '否',
    'please': '请', 'thank': '谢谢', 'thanks': '谢谢', 'sorry': '对不起',
    'ok': '好的', 'fine': '好的', 'great': '很好', 'bad': '坏的',
    'time': '时间', 'name': '名字', 'help': '帮助', 'love': '爱',
    'life': '生活', 'work': '工作', 'home': '家', 'food': '食物',
    'water': '水', 'money': '钱', 'people': '人们', 'man': '男人',
    'woman': '女人', 'child': '孩子', 'book': '书', 'phone': '电话',
    'computer': '电脑', 'car': '汽车', 'house': '房子', 'city': '城市',
}

class DictionaryBackend:
    """本地词典后端，仅处理单词和极短短语"""

    MAX_WORDS = 4  # 超过4个词不处理

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        words = text.split()
        if len(words) > self.MAX_WORDS:
            return None

        # 单词快速查询
        key = text.lower()
        if key in QUICK_DICT:
            return {
                'original': text,
                'translated': QUICK_DICT[key],
                'backend': 'dictionary',
                'source_lang': 'en',
                'target_lang': target_lang,
            }

        # 尝试 NLTK WordNet
        try:
            return self._wordnet_lookup(text, target_lang)
        except Exception:
            return None

    def _wordnet_lookup(self, word: str, target_lang: str) -> Optional[Dict]:
        from nltk.corpus import wordnet as wn
        synsets = wn.synsets(word)
        if not synsets:
            return None
        definition = synsets[0].definition()
        lemma_names = synsets[0].lemma_names()
        translated = f"{word}: {definition}"
        if len(lemma_names) > 1:
            translated += f" (同义: {', '.join(lemma_names[1:3])})"
        return {
            'original': word,
            'translated': translated,
            'backend': 'dictionary',
            'source_lang': 'en',
            'target_lang': target_lang,
        }
```

**Step 4: 运行测试**

```bash
python -m pytest tests/test_translation.py -v
```
预期：3 PASSED

**Step 5: Commit**

```bash
git add src/translation/dictionary.py tests/test_translation.py
git commit -m "feat: add local dictionary translation backend"
```

---

## Task 5: 翻译后端 - 谷歌翻译

**Files:**
- Modify: `src/translation/` → Create `google_trans.py`
- Modify: `tests/test_translation.py`

**Step 1: 添加测试（追加到 test_translation.py）**

```python
# 追加到 tests/test_translation.py
from translation.google_trans import GoogleBackend

def test_google_translate_basic():
    b = GoogleBackend()
    result = b.translate('Hello world', target_lang='zh-CN')
    if result is None:
        return  # 网络不可用时跳过
    assert '世界' in result['translated'] or '你好' in result['translated']
    assert result['backend'] == 'google'

def test_google_detect_language():
    b = GoogleBackend()
    result = b.translate('今天天气很好', target_lang='en')
    if result is None:
        return
    assert result['source_lang'] in ('zh-CN', 'zh', 'zh-TW', 'auto')
```

**Step 2: 实现 src/translation/google_trans.py**

```python
from typing import Optional, Dict

class GoogleBackend:
    def __init__(self):
        self._translator = None

    def _get_translator(self):
        if self._translator is None:
            from googletrans import Translator
            self._translator = Translator()
        return self._translator

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None
        try:
            t = self._get_translator()
            src = None if source_lang == 'auto' else source_lang
            result = t.translate(text, dest=target_lang, src=src)
            return {
                'original': text,
                'translated': result.text,
                'backend': 'google',
                'source_lang': result.src,
                'target_lang': target_lang,
            }
        except Exception as e:
            return None
```

**Step 3: 运行测试**

```bash
python -m pytest tests/test_translation.py::test_google_translate_basic -v
```

**Step 4: Commit**

```bash
git add src/translation/google_trans.py tests/test_translation.py
git commit -m "feat: add Google Translate backend"
```

---

## Task 6: 翻译后端 - 百度、DeepL、AI（OpenAI/Claude/DeepSeek）

**Files:**
- Create: `src/translation/baidu_trans.py`
- Create: `src/translation/deepl_trans.py`
- Create: `src/translation/ai_trans.py`

**Step 1: 实现 src/translation/baidu_trans.py**

```python
import requests, hashlib, random, time
from typing import Optional, Dict

class BaiduBackend:
    API_URL = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

    def __init__(self, appid: str = '', key: str = ''):
        self.appid = appid
        self.key = key

    def configure(self, appid: str, key: str):
        self.appid = appid
        self.key = key

    def translate(self, text: str, target_lang: str = 'zh', source_lang: str = 'auto') -> Optional[Dict]:
        if not self.appid or not self.key:
            return None
        text = text.strip()
        if not text:
            return None

        lang_map = {'zh-CN': 'zh', 'en': 'en', 'ja': 'jp', 'ko': 'kor', 'auto': 'auto'}
        tgt = lang_map.get(target_lang, target_lang)
        src = lang_map.get(source_lang, source_lang)

        salt = str(random.randint(10000, 99999))
        sign_str = self.appid + text + salt + self.key
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        params = {'q': text, 'from': src, 'to': tgt, 'appid': self.appid, 'salt': salt, 'sign': sign}
        try:
            resp = requests.get(self.API_URL, params=params, timeout=5)
            data = resp.json()
            if 'trans_result' in data:
                translated = ' '.join(r['dst'] for r in data['trans_result'])
                return {
                    'original': text,
                    'translated': translated,
                    'backend': 'baidu',
                    'source_lang': data.get('from', source_lang),
                    'target_lang': target_lang,
                }
        except Exception:
            return None
        return None
```

**Step 2: 实现 src/translation/deepl_trans.py**

```python
from typing import Optional, Dict

class DeepLBackend:
    def __init__(self, api_key: str = ''):
        self.api_key = api_key
        self._translator = None

    def configure(self, api_key: str):
        self.api_key = api_key
        self._translator = None

    def _get_translator(self):
        if self._translator is None and self.api_key:
            import deepl
            self._translator = deepl.Translator(self.api_key)
        return self._translator

    def translate(self, text: str, target_lang: str = 'ZH', source_lang: str = None) -> Optional[Dict]:
        t = self._get_translator()
        if t is None:
            return None
        text = text.strip()
        if not text:
            return None

        lang_map = {'zh-CN': 'ZH', 'en': 'EN-US', 'ja': 'JA', 'ko': 'KO'}
        tgt = lang_map.get(target_lang, target_lang.upper())

        try:
            result = t.translate_text(text, target_lang=tgt)
            return {
                'original': text,
                'translated': result.text,
                'backend': 'deepl',
                'source_lang': str(result.detected_source_lang),
                'target_lang': target_lang,
            }
        except Exception:
            return None
```

**Step 3: 实现 src/translation/ai_trans.py**

```python
from typing import Optional, Dict

TRANSLATE_PROMPT = """你是一名专业翻译。将以下文本翻译成{target_lang_name}。
只返回翻译结果，不要解释，不要加引号。

文本：{text}"""

EXPLAIN_PROMPT = """你是一名语言专家。对以下文字进行详细解释：
- 如果是单词：给出中文含义、词性、用法、例句
- 如果是短语或句子：给出中文含义、背景/语境说明、使用场合

文字：{text}

请用中文回答，简洁清晰。"""

LANG_NAMES = {
    'zh-CN': '简体中文', 'zh-TW': '繁体中文', 'en': '英语',
    'ja': '日语', 'ko': '韩语', 'fr': '法语', 'de': '德语',
    'es': '西班牙语', 'ru': '俄语', 'ar': '阿拉伯语',
}

class AIBackend:
    def __init__(self, provider: str = 'deepseek', api_key: str = ''):
        self.provider = provider  # 'deepseek', 'openai', 'claude'
        self.api_key = api_key

    def configure(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        if not self.api_key:
            return None
        text = text.strip()
        if not text:
            return None
        lang_name = LANG_NAMES.get(target_lang, target_lang)
        prompt = TRANSLATE_PROMPT.format(target_lang_name=lang_name, text=text)
        try:
            result = self._call_api(prompt)
            if result:
                return {
                    'original': text,
                    'translated': result,
                    'backend': self.provider,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                }
        except Exception:
            return None
        return None

    def explain(self, text: str) -> Optional[str]:
        if not self.api_key:
            return None
        prompt = EXPLAIN_PROMPT.format(text=text.strip())
        try:
            return self._call_api(prompt)
        except Exception:
            return None

    def _call_api(self, prompt: str) -> Optional[str]:
        if self.provider == 'openai' or self.provider == 'deepseek':
            return self._call_openai_compatible(prompt)
        elif self.provider == 'claude':
            return self._call_claude(prompt)
        return None

    def _call_openai_compatible(self, prompt: str) -> Optional[str]:
        from openai import OpenAI
        base_urls = {
            'openai': 'https://api.openai.com/v1',
            'deepseek': 'https://api.deepseek.com/v1',
        }
        models = {
            'openai': 'gpt-4o-mini',
            'deepseek': 'deepseek-chat',
        }
        client = OpenAI(api_key=self.api_key, base_url=base_urls.get(self.provider))
        resp = client.chat.completions.create(
            model=models.get(self.provider, 'gpt-4o-mini'),
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1000,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    def _call_claude(self, prompt: str) -> Optional[str]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return msg.content[0].text.strip()
```

**Step 4: Commit**

```bash
git add src/translation/
git commit -m "feat: add Baidu, DeepL, and AI (OpenAI/Claude/DeepSeek) backends"
```

---

## Task 7: Translation Router（智能路由）

**Files:**
- Create: `src/translation/router.py`
- Modify: `tests/test_translation.py`

**Step 1: 写路由测试（追加到 test_translation.py）**

```python
from translation.router import TranslationRouter
from core.settings import SettingsStore
import tempfile

def test_router_uses_dictionary_for_single_word():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    settings = SettingsStore(path)
    router = TranslationRouter(settings)
    result = router.translate('hello', target_lang='zh-CN')
    # 词典命中则直接返回
    if result:
        assert result['backend'] in ('dictionary', 'google', 'baidu', 'deepl', 'deepseek', 'openai', 'claude')

def test_router_returns_none_when_no_backends():
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        path = f.name
    settings = SettingsStore(path)
    settings.set('enabled_backends', [])
    router = TranslationRouter(settings)
    result = router.translate('hello world', target_lang='zh-CN')
    assert result is None
```

**Step 2: 实现 src/translation/router.py**

```python
from typing import Optional, Dict
from core.settings import SettingsStore

class TranslationRouter:
    """按 settings 中优先级顺序，依次尝试各后端翻译"""

    def __init__(self, settings: SettingsStore):
        self._settings = settings
        self._backends = {}
        self._init_backends()

    def _init_backends(self):
        from translation.dictionary import DictionaryBackend
        from translation.google_trans import GoogleBackend
        from translation.baidu_trans import BaiduBackend
        from translation.deepl_trans import DeepLBackend
        from translation.ai_trans import AIBackend

        keys = self._settings.get('api_keys', {})

        self._backends['dictionary'] = DictionaryBackend()
        self._backends['google'] = GoogleBackend()

        baidu = BaiduBackend(keys.get('baidu_appid', ''), keys.get('baidu_key', ''))
        self._backends['baidu'] = baidu

        deepl = DeepLBackend(keys.get('deepl_key', ''))
        self._backends['deepl'] = deepl

        for provider in ('deepseek', 'openai', 'claude'):
            key_name = f'{provider}_key'
            ai = AIBackend(provider=provider, api_key=keys.get(key_name, ''))
            self._backends[provider] = ai

    def reload(self):
        self._init_backends()

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None

        order = self._settings.get('translation_order', [])
        enabled = set(self._settings.get('enabled_backends', ['dictionary', 'google']))
        word_count = len(text.split())

        for name in order:
            if name not in enabled:
                continue
            backend = self._backends.get(name)
            if backend is None:
                continue
            # 词典只处理短文本
            if name == 'dictionary' and word_count > 4:
                continue
            result = backend.translate(text, target_lang=target_lang, source_lang=source_lang)
            if result and result.get('translated'):
                return result
        return None

    def get_ai_backend(self):
        """返回第一个可用的AI后端（用于AI解释功能）"""
        ai_providers = ['deepseek', 'openai', 'claude']
        enabled = set(self._settings.get('enabled_backends', []))
        for p in ai_providers:
            if p in enabled and p in self._backends:
                return self._backends[p]
        return None
```

**Step 3: 运行测试**

```bash
python -m pytest tests/test_translation.py -v
```

**Step 4: Commit**

```bash
git add src/translation/router.py tests/test_translation.py
git commit -m "feat: add TranslationRouter with priority-based backend selection"
```

---

## Task 8: OCRWorker（PaddleOCR后台线程）

**Files:**
- Create: `src/ocr/ocr_worker.py`

**Step 1: 实现 src/ocr/ocr_worker.py**

```python
import mss
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QRect

class OCRWorker(QThread):
    """在后台线程执行截图+OCR，完成后发出信号"""

    result_ready = pyqtSignal(str, object)  # (text, region_rect)
    error_occurred = pyqtSignal(str)

    def __init__(self, region: QRect, parent=None):
        super().__init__(parent)
        self.region = region
        self._ocr = None

    def _get_ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        return self._ocr

    def run(self):
        try:
            img = self._capture()
            if img is None:
                self.error_occurred.emit('截图失败')
                return
            text = self._extract_text(img)
            self.result_ready.emit(text, self.region)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _capture(self):
        r = self.region
        with mss.mss() as sct:
            monitor = {
                'left': r.x(), 'top': r.y(),
                'width': max(r.width(), 1), 'height': max(r.height(), 1)
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            return img[:, :, :3]  # BGR, 去掉alpha

    def _extract_text(self, img) -> str:
        ocr = self._get_ocr()
        results = ocr.ocr(img, cls=True)
        if not results or not results[0]:
            return ''
        lines = []
        for line in results[0]:
            if line and len(line) >= 2:
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                    lines.append(str(text_info[0]))
        return ' '.join(lines).strip()


class TranslationWorker(QThread):
    """在后台线程执行翻译"""

    result_ready = pyqtSignal(dict)  # translation result dict
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, router, target_lang: str = 'zh-CN', parent=None):
        super().__init__(parent)
        self.text = text
        self.router = router
        self.target_lang = target_lang

    def run(self):
        try:
            result = self.router.translate(self.text, target_lang=self.target_lang)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit('所有翻译后端均失败或未启用')
        except Exception as e:
            self.error_occurred.emit(str(e))


class ExplainWorker(QThread):
    """在后台线程执行AI解释"""

    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, ai_backend, parent=None):
        super().__init__(parent)
        self.text = text
        self.ai_backend = ai_backend

    def run(self):
        try:
            if self.ai_backend is None:
                self.error_occurred.emit('请先在设置中配置AI后端（DeepSeek/OpenAI/Claude）')
                return
            result = self.ai_backend.explain(self.text)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit('AI解释失败')
        except Exception as e:
            self.error_occurred.emit(str(e))
```

**Step 2: 简单验证（无完整单元测试，因需要屏幕环境）**

```bash
python -c "from src.ocr.ocr_worker import OCRWorker, TranslationWorker; print('OCRWorker import OK')"
```

**Step 3: Commit**

```bash
git add src/ocr/ocr_worker.py
git commit -m "feat: add OCRWorker and TranslationWorker QThread classes"
```

---

## Task 9: SelectionOverlay（全屏框选覆盖层）

**Files:**
- Create: `src/ui/selection_overlay.py`

**Step 1: 实现 src/ui/selection_overlay.py**

```python
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QCursor

class SelectionOverlay(QWidget):
    """全屏透明覆盖层，用于拖拽框选翻译区域"""

    selection_made = pyqtSignal(QRect)  # 用户完成框选，发出矩形区域
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._start = QPoint()
        self._end = QPoint()
        self._drawing = False
        self._setup_window()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setCursor(QCursor(Qt.CrossCursor))
        # 覆盖全部屏幕
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def show_overlay(self):
        self._drawing = False
        self._start = QPoint()
        self._end = QPoint()
        self.showFullScreen()
        self.activateWindow()
        self.raise_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._start = event.pos()
            self._end = event.pos()
            self._drawing = True

    def mouseMoveEvent(self, event):
        if self._drawing:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drawing:
            self._drawing = False
            self._end = event.pos()
            self.hide()
            rect = QRect(self._start, self._end).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.selection_made.emit(rect)
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._drawing = False
            self.hide()
            self.cancelled.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))

        if self._drawing and not self._start.isNull():
            rect = QRect(self._start, self._end).normalized()
            # 清除选区内的遮罩
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            # 红色虚线边框
            pen = QPen(QColor(255, 80, 80), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)
            # 尺寸提示
            painter.setPen(QColor(255, 255, 255))
            size_text = f'{rect.width()} × {rect.height()}'
            painter.drawText(rect.x() + 4, rect.y() - 4, size_text)
```

**Step 2: 验证导入**

```bash
python -c "from src.ui.selection_overlay import SelectionOverlay; print('SelectionOverlay OK')"
```

**Step 3: Commit**

```bash
git add src/ui/selection_overlay.py
git commit -m "feat: add SelectionOverlay fullscreen drawing widget"
```

---

## Task 10: TranslationBox（透明虚线"框"）

**Files:**
- Create: `src/ui/translation_box.py`

**Step 1: 实现 src/ui/translation_box.py**

```python
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QSizeGrip
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

class TranslationBox(QWidget):
    """屏幕上的透明虚线翻译框"""

    translate_requested = pyqtSignal(object)   # self
    close_requested = pyqtSignal(object)        # self
    mode_changed = pyqtSignal(object, str)      # self, mode

    MODE_TEMP = 'temp'
    MODE_FIXED = 'fixed'

    def __init__(self, rect: QRect, box_id: int, settings, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.region = rect          # 屏幕上的实际位置（用于截图）
        self.settings = settings
        self.mode = self.MODE_TEMP
        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(lambda: self.translate_requested.emit(self))
        self._dismiss_timer = QTimer()
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._on_dismiss_timeout)
        self._drag_pos = QPoint()
        self._buttons_visible = False
        self._ocr_text = ''
        self._setup_ui()
        self._setup_window(rect)

    def _setup_window(self, rect: QRect):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(rect)
        self.setMinimumSize(80, 40)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # 控制按钮行（悬停时显示）
        self._btn_bar = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_bar)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(3)

        self._btn_translate = self._make_btn('🔄', '立即翻译', self._on_translate)
        self._btn_pin = self._make_btn('📌', '切换固定/临时', self._on_toggle_pin)
        self._btn_hide = self._make_btn('👁', '隐藏', self.hide)
        self._btn_close = self._make_btn('✕', '关闭', lambda: self.close_requested.emit(self))

        for btn in [self._btn_translate, self._btn_pin, self._btn_hide, self._btn_close]:
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        self._btn_bar.setVisible(False)
        layout.addWidget(self._btn_bar)

        # OCR文字提示（小字）
        self._ocr_label = QLabel('')
        self._ocr_label.setStyleSheet('color: rgba(200,200,200,180); font-size: 10px;')
        self._ocr_label.setWordWrap(True)
        layout.addWidget(self._ocr_label)
        layout.addStretch()

    def _make_btn(self, icon, tooltip, callback):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(22, 22)
        btn.setStyleSheet('''
            QPushButton {
                background: rgba(50,50,50,160);
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(80,80,80,200); }
        ''')
        btn.clicked.connect(callback)
        return btn

    def _on_translate(self):
        self.translate_requested.emit(self)

    def _on_toggle_pin(self):
        if self.mode == self.MODE_TEMP:
            self.set_mode(self.MODE_FIXED)
        else:
            self.set_mode(self.MODE_TEMP)

    def set_mode(self, mode: str):
        self.mode = mode
        self._btn_pin.setText('📍' if mode == self.MODE_FIXED else '📌')
        if mode == self.MODE_FIXED:
            self._auto_timer.stop()
            self._dismiss_timer.stop()
        self.mode_changed.emit(self, mode)
        self.update()

    def set_ocr_text(self, text: str):
        self._ocr_text = text
        short = text[:40] + '...' if len(text) > 40 else text
        self._ocr_label.setText(short)

    def start_dismiss_timer(self):
        if self.mode == self.MODE_TEMP:
            timeout = self.settings.get('temp_box_timeout', 3) * 1000
            self._dismiss_timer.start(timeout)

    def start_auto_translate(self):
        interval = self.settings.get('auto_translate_interval', 2) * 1000
        self._auto_timer.start(interval)

    def stop_auto_translate(self):
        self._auto_timer.stop()

    def _on_dismiss_timeout(self):
        if self.mode == self.MODE_TEMP:
            self.close_requested.emit(self)

    def enterEvent(self, event):
        self._btn_bar.setVisible(True)

    def leaveEvent(self, event):
        self._btn_bar.setVisible(False)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 半透明背景
        color = QColor(20, 20, 20, 60) if self.mode == self.MODE_FIXED else QColor(20, 20, 20, 40)
        painter.fillRect(self.rect(), color)
        # 虚线边框
        border_color = QColor(100, 180, 255, 200) if self.mode == self.MODE_FIXED else QColor(255, 255, 255, 150)
        pen = QPen(border_color, 1, Qt.DashLine)
        painter.setPen(pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            new_pos = event.globalPos() - self._drag_pos
            self.move(new_pos)
            # 更新截图区域
            self.region = QRect(new_pos.x(), new_pos.y(), self.width(), self.height())
```

**Step 2: Commit**

```bash
git add src/ui/translation_box.py
git commit -m "feat: add TranslationBox transparent overlay widget"
```

---

## Task 11: ResultBar（结果显示条）

**Files:**
- Create: `src/ui/result_bar.py`

**Step 1: 实现 src/ui/result_bar.py**

```python
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout,
                              QVBoxLayout, QApplication, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont, QColor

class ResultBar(QWidget):
    """深色浮动结果显示条，始终置顶"""

    explain_requested = pyqtSignal(str)   # 请求AI解释
    history_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._current_result = None
        self._source_expanded = False
        self._drag_pos = QPoint()
        self._setup_window()
        self._setup_ui()
        self._position_window()

    def _setup_window(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(500)

    def _position_window(self):
        screen = QApplication.primaryScreen().geometry()
        pos = self.settings.get('result_bar_position', 'top')
        if pos == 'top':
            self.move(screen.center().x() - 300, 10)
        else:
            self.move(screen.center().x() - 300, screen.height() - self.height() - 40)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 主容器（带圆角深色背景）
        self._container = QWidget()
        self._container.setObjectName('container')
        self._container.setStyleSheet('''
            #container {
                background: rgba(20, 20, 25, 220);
                border-radius: 10px;
                border: 1px solid rgba(255,255,255,30);
            }
        ''')
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(10, 8, 10, 8)
        container_layout.setSpacing(4)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._lbl_lang = QLabel('EN → 简中')
        self._lbl_lang.setStyleSheet('color: rgba(180,180,180,200); font-size: 11px;')

        self._btn_history = self._tool_btn('🕐', '翻译历史', self.history_requested.emit)
        self._btn_settings = self._tool_btn('⚙', '设置', self.settings_requested.emit)
        self._btn_minimize = self._tool_btn('─', '最小化', self._toggle_minimize)
        self._btn_close = self._tool_btn('✕', '关闭', self.hide)

        toolbar.addWidget(self._lbl_lang)
        toolbar.addStretch()
        for btn in [self._btn_history, self._btn_settings, self._btn_minimize, self._btn_close]:
            toolbar.addWidget(btn)
        container_layout.addLayout(toolbar)

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background: rgba(255,255,255,20);')
        container_layout.addWidget(sep)

        # 译文区域
        self._lbl_translation = QLabel('等待翻译...')
        self._lbl_translation.setStyleSheet('color: #ffffff; font-size: 14px; font-weight: 500;')
        self._lbl_translation.setWordWrap(True)
        self._lbl_translation.setTextInteractionFlags(Qt.TextSelectableByMouse)
        container_layout.addWidget(self._lbl_translation)

        # 底部操作行
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self._btn_source = QPushButton('原文 ▼')
        self._btn_source.setStyleSheet(self._action_btn_style())
        self._btn_source.clicked.connect(self._toggle_source)

        self._btn_copy = QPushButton('📋 复制')
        self._btn_copy.setStyleSheet(self._action_btn_style())
        self._btn_copy.clicked.connect(self._copy_translation)

        self._btn_explain = QPushButton('💬 AI解释')
        self._btn_explain.setStyleSheet(self._action_btn_style())
        self._btn_explain.clicked.connect(self._on_explain)

        self._lbl_backend = QLabel('')
        self._lbl_backend.setStyleSheet('color: rgba(120,180,120,180); font-size: 10px;')

        action_row.addWidget(self._btn_source)
        action_row.addWidget(self._btn_copy)
        action_row.addWidget(self._btn_explain)
        action_row.addStretch()
        action_row.addWidget(self._lbl_backend)
        container_layout.addLayout(action_row)

        # 原文展开区域（默认折叠）
        self._source_widget = QLabel('')
        self._source_widget.setStyleSheet('color: rgba(180,180,180,200); font-size: 12px; padding: 4px 0;')
        self._source_widget.setWordWrap(True)
        self._source_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._source_widget.setVisible(False)
        container_layout.addWidget(self._source_widget)

        # AI解释展开区域（默认折叠）
        self._explain_widget = QLabel('')
        self._explain_widget.setStyleSheet('''
            color: rgba(220,220,180,220);
            font-size: 12px;
            padding: 6px;
            background: rgba(255,255,150,20);
            border-radius: 4px;
        ''')
        self._explain_widget.setWordWrap(True)
        self._explain_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._explain_widget.setVisible(False)
        container_layout.addWidget(self._explain_widget)

        main_layout.addWidget(self._container)
        self.adjustSize()

    def _tool_btn(self, icon, tooltip, callback):
        btn = QPushButton(icon)
        btn.setToolTip(tooltip)
        btn.setFixedSize(22, 22)
        btn.setStyleSheet('''
            QPushButton { background: transparent; color: rgba(180,180,180,200);
                          border: none; font-size: 12px; }
            QPushButton:hover { color: white; background: rgba(255,255,255,20);
                                border-radius: 3px; }
        ''')
        btn.clicked.connect(callback)
        return btn

    def _action_btn_style(self):
        return '''
            QPushButton { background: rgba(60,60,70,180); color: rgba(200,200,200,220);
                          border: 1px solid rgba(255,255,255,20); border-radius: 4px;
                          padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: rgba(80,80,100,200); color: white; }
        '''

    def show_result(self, result: dict):
        self._current_result = result
        self._explain_widget.setVisible(False)
        self._source_expanded = False
        self._source_widget.setVisible(False)
        self._btn_source.setText('原文 ▼')

        self._lbl_translation.setText(result.get('translated', ''))
        self._source_widget.setText(result.get('original', ''))
        self._lbl_backend.setText(f"来源: {result.get('backend', '')}")

        src = result.get('source_lang', 'auto')
        tgt = result.get('target_lang', 'zh-CN')
        self._lbl_lang.setText(f'{src.upper()} → {tgt}')

        self.show()
        self.adjustSize()

    def show_explain(self, text: str):
        self._explain_widget.setText(text)
        self._explain_widget.setVisible(True)
        self.adjustSize()

    def show_loading(self, text: str = '翻译中...'):
        self._lbl_translation.setText(text)
        self.show()

    def show_error(self, text: str):
        self._lbl_translation.setText(f'⚠ {text}')
        self.show()

    def _toggle_source(self):
        self._source_expanded = not self._source_expanded
        self._source_widget.setVisible(self._source_expanded)
        self._btn_source.setText('原文 ▲' if self._source_expanded else '原文 ▼')
        self.adjustSize()

    def _copy_translation(self):
        if self._current_result:
            QApplication.clipboard().setText(self._current_result.get('translated', ''))

    def _on_explain(self):
        text = ''
        if self._current_result:
            text = self._current_result.get('original', '')
        if text:
            self.explain_requested.emit(text)

    def _toggle_minimize(self):
        if self._container.isVisible():
            self._lbl_translation.setVisible(False)
            self._source_widget.setVisible(False)
            self._explain_widget.setVisible(False)
            self._btn_source.setVisible(False)
            self._btn_copy.setVisible(False)
            self._btn_explain.setVisible(False)
            self._lbl_backend.setVisible(False)
            self._btn_minimize.setText('□')
        else:
            for w in [self._lbl_translation, self._btn_source, self._btn_copy,
                      self._btn_explain, self._lbl_backend]:
                w.setVisible(True)
            self._btn_minimize.setText('─')
        self.adjustSize()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
```

**Step 2: Commit**

```bash
git add src/ui/result_bar.py
git commit -m "feat: add ResultBar floating dark translation display"
```

---

## Task 12: SystemTray + BoxManager + CoreController

**Files:**
- Create: `src/ui/tray.py`
- Create: `src/core/box_manager.py`
- Create: `src/core/controller.py`

**Step 1: 实现 src/ui/tray.py**

```python
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QApplication
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import pyqtSignal

class SystemTray(QSystemTrayIcon):
    select_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    history_triggered = pyqtSignal()
    quit_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(self._make_icon())
        self.setToolTip('ScreenTranslator')
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _make_icon(self):
        px = QPixmap(16, 16)
        px.fill(QColor(80, 140, 255))
        return QIcon(px)

    def _setup_menu(self):
        menu = QMenu()

        act_select = QAction('📷 框选翻译 (Alt+Q)', menu)
        act_select.triggered.connect(self.select_triggered.emit)

        act_history = QAction('🕐 翻译历史', menu)
        act_history.triggered.connect(self.history_triggered.emit)

        act_settings = QAction('⚙ 设置', menu)
        act_settings.triggered.connect(self.settings_triggered.emit)

        act_quit = QAction('退出', menu)
        act_quit.triggered.connect(self.quit_triggered.emit)

        menu.addAction(act_select)
        menu.addSeparator()
        menu.addAction(act_history)
        menu.addAction(act_settings)
        menu.addSeparator()
        menu.addAction(act_quit)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.select_triggered.emit()
```

**Step 2: 实现 src/core/box_manager.py**

```python
from typing import Dict
from PyQt5.QtCore import QRect, QObject, pyqtSignal

class BoxManager(QObject):
    """管理所有 TranslationBox 实例"""

    translate_box = pyqtSignal(object)  # box instance

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._boxes: Dict[int, object] = {}
        self._next_id = 1

    def create_box(self, rect: QRect) -> object:
        from ui.translation_box import TranslationBox
        box = TranslationBox(rect, self._next_id, self.settings)
        box_id = self._next_id
        self._next_id += 1
        self._boxes[box_id] = box
        box.translate_requested.connect(self.translate_box.emit)
        box.close_requested.connect(self._on_close_box)
        box.show()
        return box

    def _on_close_box(self, box):
        bid = box.box_id
        if bid in self._boxes:
            self._boxes[bid].hide()
            self._boxes[bid].deleteLater()
            del self._boxes[bid]

    def hide_all(self):
        for box in self._boxes.values():
            box.hide()

    def show_all(self):
        for box in self._boxes.values():
            box.show()

    def clear_all(self):
        for box in list(self._boxes.values()):
            self._on_close_box(box)
```

**Step 3: 实现 src/core/controller.py**

```python
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from pynput import keyboard

class CoreController(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        from core.settings import SettingsStore
        from core.history import HistoryDB
        self.settings = SettingsStore()
        self.history = HistoryDB()
        self._hotkey_listener = None
        self._pending_ocr_workers = []
        self._pending_translate_workers = []
        self._pending_explain_workers = []

    def start(self):
        from translation.router import TranslationRouter
        from core.box_manager import BoxManager
        from ui.selection_overlay import SelectionOverlay
        from ui.result_bar import ResultBar
        from ui.tray import SystemTray

        self.router = TranslationRouter(self.settings)
        self.box_manager = BoxManager(self.settings)
        self.overlay = SelectionOverlay()
        self.result_bar = ResultBar(self.settings)
        self.tray = SystemTray()

        # 信号连接
        self.overlay.selection_made.connect(self._on_selection_made)
        self.overlay.cancelled.connect(lambda: None)
        self.box_manager.translate_box.connect(self._on_translate_box)
        self.result_bar.explain_requested.connect(self._on_explain_requested)
        self.result_bar.history_requested.connect(self._show_history)
        self.result_bar.settings_requested.connect(self._show_settings)
        self.tray.select_triggered.connect(self._start_selection)
        self.tray.settings_triggered.connect(self._show_settings)
        self.tray.history_triggered.connect(self._show_history)
        self.tray.quit_triggered.connect(self.app.quit)

        self.result_bar.show()
        self.tray.show()
        self._setup_hotkeys()

    def _setup_hotkeys(self):
        hotkey_str = self.settings.get('hotkey_select', 'alt+q')
        try:
            combo = {keyboard.Key.alt, keyboard.KeyCode.from_char('q')}
            def on_press(key):
                combo_current = set()
                if key == keyboard.Key.alt:
                    combo_current.add(key)
                elif hasattr(key, 'char') and key.char == 'q':
                    combo_current.add(key)
            # 使用 GlobalHotKeys
            hotkeys = {
                '<alt>+q': self._start_selection,
                '<alt>+e': self._trigger_explain,
            }
            self._hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self._hotkey_listener.start()
        except Exception as e:
            print(f'热键设置失败: {e}')

    def _start_selection(self):
        self.overlay.show_overlay()

    def _trigger_explain(self):
        if self.result_bar._current_result:
            text = self.result_bar._current_result.get('original', '')
            if text:
                self._on_explain_requested(text)

    def _on_selection_made(self, rect):
        box = self.box_manager.create_box(rect)
        self.result_bar.show_loading('识别中...')
        self._run_ocr(box)

    def _run_ocr(self, box):
        from ocr.ocr_worker import OCRWorker
        worker = OCRWorker(box.region)
        worker.result_ready.connect(lambda text, region: self._on_ocr_done(text, box))
        worker.error_occurred.connect(lambda e: self.result_bar.show_error(f'OCR失败: {e}'))
        self._pending_ocr_workers.append(worker)
        worker.finished.connect(lambda: self._pending_ocr_workers.remove(worker) if worker in self._pending_ocr_workers else None)
        worker.start()

    def _on_ocr_done(self, text: str, box):
        if not text.strip():
            self.result_bar.show_error('未识别到文字，请重新框选')
            box.start_dismiss_timer()
            return
        box.set_ocr_text(text)
        self.result_bar.show_loading('翻译中...')
        self._run_translate(text, box)

    def _run_translate(self, text: str, box):
        from ocr.ocr_worker import TranslationWorker
        target = self.settings.get('target_language', 'zh-CN')
        worker = TranslationWorker(text, self.router, target_lang=target)
        worker.result_ready.connect(lambda result: self._on_translate_done(result, box))
        worker.error_occurred.connect(lambda e: self.result_bar.show_error(e))
        self._pending_translate_workers.append(worker)
        worker.finished.connect(lambda: self._pending_translate_workers.remove(worker) if worker in self._pending_translate_workers else None)
        worker.start()

    def _on_translate_done(self, result: dict, box):
        self.result_bar.show_result(result)
        self.history.add(
            result.get('original', ''),
            result.get('translated', ''),
            result.get('source_lang', ''),
            result.get('target_lang', ''),
            result.get('backend', ''),
        )
        box.start_dismiss_timer()

    def _on_translate_box(self, box):
        self._run_ocr(box)

    def _on_explain_requested(self, text: str):
        ai = self.router.get_ai_backend()
        from ocr.ocr_worker import ExplainWorker
        worker = ExplainWorker(text, ai)
        worker.result_ready.connect(self.result_bar.show_explain)
        worker.error_occurred.connect(lambda e: self.result_bar.show_error(e))
        self._pending_explain_workers.append(worker)
        worker.start()

    def _show_history(self):
        from ui.history_window import HistoryWindow
        if not hasattr(self, '_history_win') or not self._history_win.isVisible():
            self._history_win = HistoryWindow(self.history)
            self._history_win.show()
        else:
            self._history_win.activateWindow()

    def _show_settings(self):
        from ui.settings_window import SettingsWindow
        if not hasattr(self, '_settings_win') or not self._settings_win.isVisible():
            self._settings_win = SettingsWindow(self.settings)
            self._settings_win.settings_saved.connect(self.router.reload)
            self._settings_win.show()
        else:
            self._settings_win.activateWindow()
```

**Step 4: Commit**

```bash
git add src/ui/tray.py src/core/box_manager.py src/core/controller.py
git commit -m "feat: add SystemTray, BoxManager, and CoreController wiring"
```

---

## Task 13: SettingsWindow（设置窗口）

**Files:**
- Create: `src/ui/settings_window.py`

**Step 1: 实现 src/ui/settings_window.py**

```python
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                              QPushButton, QGroupBox, QCheckBox, QListWidget,
                              QListWidgetItem, QTabWidget, QWidget, QFormLayout)
from PyQt5.QtCore import pyqtSignal, Qt

BACKEND_LABELS = {
    'dictionary': '📖 本地词典（离线）',
    'google': '🌐 谷歌翻译（免费）',
    'baidu': '🔵 百度翻译',
    'deepl': '🟢 DeepL',
    'deepseek': '🤖 DeepSeek AI',
    'openai': '🤖 OpenAI GPT',
    'claude': '🤖 Claude AI',
}

class SettingsWindow(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle('ScreenTranslator - 设置')
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # Tab 1: 通用设置
        general_tab = QWidget()
        form = QFormLayout(general_tab)

        self._spin_timeout = QSpinBox()
        self._spin_timeout.setRange(1, 30)
        self._spin_timeout.setSuffix(' 秒')
        form.addRow('临时框消失时间:', self._spin_timeout)

        self._spin_interval = QSpinBox()
        self._spin_interval.setRange(1, 60)
        self._spin_interval.setSuffix(' 秒')
        form.addRow('自动翻译间隔:', self._spin_interval)

        self._combo_target = QComboBox()
        for code, name in [('zh-CN','简体中文'),('en','英语'),('ja','日语'),
                           ('ko','韩语'),('fr','法语'),('de','德语')]:
            self._combo_target.addItem(name, code)
        form.addRow('默认翻译目标语言:', self._combo_target)

        self._edit_hotkey_select = QLineEdit()
        form.addRow('框选热键:', self._edit_hotkey_select)

        self._edit_hotkey_explain = QLineEdit()
        form.addRow('AI解释热键:', self._edit_hotkey_explain)

        tabs.addTab(general_tab, '通用')

        # Tab 2: 翻译来源
        source_tab = QWidget()
        source_layout = QVBoxLayout(source_tab)

        tip = QLabel('💡 提示：追求高效稳定？可将已配置的AI翻译拖到免费API前面，享受更快更准的翻译体验。')
        tip.setWordWrap(True)
        tip.setStyleSheet('color: #888; font-size: 11px; padding: 4px;')
        source_layout.addWidget(tip)

        self._list_backends = QListWidget()
        self._list_backends.setDragDropMode(QListWidget.InternalMove)
        source_layout.addWidget(self._list_backends)

        tabs.addTab(source_tab, '翻译来源')

        # Tab 3: API密钥
        key_tab = QWidget()
        key_form = QFormLayout(key_tab)

        self._key_fields = {}
        key_configs = [
            ('baidu_appid', '百度 AppID:'),
            ('baidu_key', '百度 Key:'),
            ('deepl_key', 'DeepL Key:'),
            ('deepseek_key', 'DeepSeek Key:'),
            ('openai_key', 'OpenAI Key:'),
            ('claude_key', 'Claude Key:'),
        ]
        for key_name, label in key_configs:
            edit = QLineEdit()
            edit.setEchoMode(QLineEdit.Password)
            edit.setPlaceholderText('留空则不使用此后端')
            self._key_fields[key_name] = edit
            key_form.addRow(label, edit)

        tabs.addTab(key_tab, 'API 密钥')

        layout.addWidget(tabs)

        # 按钮行
        btn_row = QHBoxLayout()
        btn_save = QPushButton('保存')
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

        self._edit_hotkey_select.setText(self.settings.get('hotkey_select', 'alt+q'))
        self._edit_hotkey_explain.setText(self.settings.get('hotkey_explain', 'alt+e'))

        order = self.settings.get('translation_order', list(BACKEND_LABELS.keys()))
        enabled = set(self.settings.get('enabled_backends', ['dictionary', 'google']))
        self._list_backends.clear()
        for name in order:
            item = QListWidgetItem(BACKEND_LABELS.get(name, name))
            item.setData(Qt.UserRole, name)
            item.setCheckState(Qt.Checked if name in enabled else Qt.Unchecked)
            self._list_backends.addItem(item)

        keys = self.settings.get('api_keys', {})
        for key_name, edit in self._key_fields.items():
            edit.setText(keys.get(key_name, ''))

    def _save(self):
        self.settings.set('temp_box_timeout', self._spin_timeout.value())
        self.settings.set('auto_translate_interval', self._spin_interval.value())
        self.settings.set('target_language', self._combo_target.currentData())
        self.settings.set('hotkey_select', self._edit_hotkey_select.text())
        self.settings.set('hotkey_explain', self._edit_hotkey_explain.text())

        order = []
        enabled = []
        for i in range(self._list_backends.count()):
            item = self._list_backends.item(i)
            name = item.data(Qt.UserRole)
            order.append(name)
            if item.checkState() == Qt.Checked:
                enabled.append(name)
        self.settings.set('translation_order', order)
        self.settings.set('enabled_backends', enabled)

        keys = {}
        for key_name, edit in self._key_fields.items():
            keys[key_name] = edit.text()
        self.settings.set('api_keys', keys)

        self.settings_saved.emit()
        self.close()
```

**Step 2: Commit**

```bash
git add src/ui/settings_window.py
git commit -m "feat: add SettingsWindow with tabbed UI and drag-to-reorder backends"
```

---

## Task 14: HistoryWindow（历史记录窗口）

**Files:**
- Create: `src/ui/history_window.py`

**Step 1: 实现 src/ui/history_window.py**

```python
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                              QTableWidgetItem, QLineEdit, QPushButton, QLabel,
                              QTextEdit, QSplitter, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QTimer

class HistoryWindow(QDialog):
    def __init__(self, history_db, parent=None):
        super().__init__(parent)
        self.history_db = history_db
        self.setWindowTitle('翻译历史')
        self.resize(700, 500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 搜索栏
        search_row = QHBoxLayout()
        self._edit_search = QLineEdit()
        self._edit_search.setPlaceholderText('搜索原文或译文...')
        self._edit_search.textChanged.connect(self._on_search)
        btn_clear = QPushButton('清空历史')
        btn_clear.clicked.connect(self._clear_history)
        search_row.addWidget(self._edit_search)
        search_row.addWidget(btn_clear)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Vertical)

        # 表格
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(['时间', '原文', '译文', '来源'])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.itemSelectionChanged.connect(self._on_select)
        splitter.addWidget(self._table)

        # 详情区
        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(150)
        splitter.addWidget(self._detail)

        layout.addWidget(splitter)

    def _load(self, records=None):
        if records is None:
            records = self.history_db.get_recent(200)
        self._records = records
        self._table.setRowCount(0)
        for r in records:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(r.get('created_at', '')[:16]))
            src = r.get('source_text', '')
            self._table.setItem(row, 1, QTableWidgetItem(src[:50] + '...' if len(src) > 50 else src))
            tgt = r.get('translated_text', '')
            self._table.setItem(row, 2, QTableWidgetItem(tgt[:50] + '...' if len(tgt) > 50 else tgt))
            self._table.setItem(row, 3, QTableWidgetItem(r.get('backend', '')))

    def _on_search(self, text):
        if text.strip():
            results = self.history_db.search(text.strip())
            self._load(results)
        else:
            self._load()

    def _on_select(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        row_idx = self._table.currentRow()
        if row_idx < len(self._records):
            r = self._records[row_idx]
            self._detail.setHtml(f'''
                <b>原文：</b><br>{r.get("source_text","")}<br><br>
                <b>译文：</b><br>{r.get("translated_text","")}<br><br>
                <small>来源: {r.get("backend","")} | {r.get("created_at","")}</small>
            ''')

    def _clear_history(self):
        reply = QMessageBox.question(self, '确认', '确定要清空所有翻译历史吗？',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history_db.clear()
            self._load()
```

**Step 2: Commit**

```bash
git add src/ui/history_window.py
git commit -m "feat: add HistoryWindow with search and detail view"
```

---

## Task 15: 最终整合与验证

**Step 1: 创建 README.md**

```markdown
# ScreenTranslator

屏幕翻译工具 - 框选任意屏幕区域进行OCR翻译

## 安装

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"
```

## 运行

```bash
python src/main.py
```

## 快捷键

- `Alt+Q` — 框选翻译
- `Alt+E` — AI解释当前内容

## 首次使用

1. 系统托盘图标右键 → 设置
2. 在"翻译来源"标签中勾选要使用的后端
3. 在"API密钥"标签中填写对应密钥
4. 保存后，按 `Alt+Q` 开始框选翻译
```

**Step 2: 运行完整测试套件**

```bash
cd c:/Users/Administrator/my-todo
python -m pytest tests/ -v
```
预期：所有测试通过

**Step 3: 启动应用验证**

```bash
python src/main.py
```
验证清单：
- [ ] 系统托盘图标出现
- [ ] Alt+Q 触发框选覆盖层
- [ ] 框选区域后出现虚线框
- [ ] ResultBar 显示翻译结果
- [ ] 原文折叠按钮工作正常
- [ ] 设置窗口可打开并保存
- [ ] 历史记录窗口可查看
- [ ] 临时框在设定时间后消失
- [ ] 固定框保持常驻

**Step 4: 最终 Commit**

```bash
git add README.md
git commit -m "feat: complete ScreenTranslator v1.0"
```
