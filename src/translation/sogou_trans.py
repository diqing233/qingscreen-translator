import hashlib
import http.cookiejar
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
import uuid
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_LANG_MAP = {
    'auto': 'auto',
    'zh-CN': 'zh-CHS',
    'zh-TW': 'zh-CHT',
    'en': 'en',
    'ja': 'ja',
    'ko': 'ko',
    'fr': 'fr',
    'de': 'de',
    'es': 'es',
    'ru': 'ru',
}

_HOME_URL = 'https://fanyi.sogou.com/'
_TRANS_URL = 'https://fanyi.sogou.com/api/transpc/text/result'
_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)
_SECRET_RES = (
    re.compile(r'"secretCode"\s*:\s*"([^"]+)"'),
    re.compile(r'\\"secretCode\\"\s*:\s*\\"([^"]+)\\"'),
)
_UUID_RES = (
    re.compile(r'"uuid"\s*:\s*"([a-fA-F0-9\-]{16,})"'),
    re.compile(r'\\"uuid\\"\s*:\s*\\"([a-fA-F0-9\-]{16,})\\"'),
)


class SogouBackend:
    """Unofficial Sogou web translator backend."""

    def __init__(self):
        self._secret_code = ''
        self._uuid = ''
        self._config_expiry = 0.0
        self._lock = threading.Lock()
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )

    def _extract(self, html: str, patterns) -> str:
        for pattern in patterns:
            match = pattern.search(html)
            if match:
                return match.group(1)
        return ''

    def _urlopen(self, req: urllib.request.Request, timeout: int = 10):
        return self._opener.open(req, timeout=timeout)

    def _refresh_config(self):
        req = urllib.request.Request(
            _HOME_URL,
            headers={
                'User-Agent': _UA,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            },
        )
        with self._urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        secret_code = self._extract(html, _SECRET_RES)
        if not secret_code:
            raise ValueError('secretCode not found on sogou page')

        page_uuid = self._extract(html, _UUID_RES)
        self._secret_code = secret_code
        self._uuid = page_uuid or str(uuid.uuid4())
        # Refresh periodically because webpage config can rotate.
        self._config_expiry = time.time() + 10 * 60

    def _ensure_config(self):
        with self._lock:
            if time.time() >= self._config_expiry or not self._secret_code:
                self._refresh_config()

    def _invalidate(self):
        with self._lock:
            self._secret_code = ''
            self._config_expiry = 0.0
            self._cookie_jar = http.cookiejar.CookieJar()
            self._opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self._cookie_jar)
            )

    def _extract_translation(self, result: dict) -> str:
        if not isinstance(result, dict):
            return ''

        data = result.get('data') if isinstance(result.get('data'), dict) else result
        trans_obj = data.get('translate') if isinstance(data, dict) else None
        if isinstance(trans_obj, dict):
            text = trans_obj.get('dit', '')
            if text:
                return text
        return ''

    def _request_json(self, payload_obj: dict) -> dict:
        req = urllib.request.Request(
            _TRANS_URL,
            data=json.dumps(payload_obj, ensure_ascii=False).encode('utf-8'),
            headers={
                'User-Agent': _UA,
                'Referer': _HOME_URL,
                'Origin': 'https://fanyi.sogou.com',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/json;charset=UTF-8',
            },
        )
        with self._urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
        return json.loads(body)

    def _request_form(self, payload_obj: dict) -> dict:
        req = urllib.request.Request(
            _TRANS_URL,
            data=urllib.parse.urlencode(payload_obj).encode('utf-8'),
            headers={
                'User-Agent': _UA,
                'Referer': _HOME_URL,
                'Origin': 'https://fanyi.sogou.com',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
        )
        with self._urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
        return json.loads(body)

    def translate(self, text: str, target_lang: str = 'zh-CN',
                  source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None

        src = _LANG_MAP.get(source_lang, 'auto')
        tgt = _LANG_MAP.get(target_lang, 'zh-CHS')

        for attempt in range(2):
            try:
                self._ensure_config()
                sign = hashlib.md5(
                    f'{src}{tgt}{text}{self._secret_code}'.encode('utf-8')
                ).hexdigest()
                payload_obj = {
                    'from': src,
                    'to': tgt,
                    'text': text,
                    'client': 'pc',
                    'fr': 'browser_pc',
                    'needQc': '1',
                    's': sign,
                    'uuid': self._uuid,
                    'exchange': 'false',
                }

                req_error = None
                for requester in (self._request_json, self._request_form):
                    try:
                        result = requester(payload_obj)
                        translated = self._extract_translation(result)
                        if translated:
                            return {
                                'original': text,
                                'translated': translated,
                                'backend': 'sogou',
                                'source_lang': source_lang,
                                'target_lang': target_lang,
                            }
                        req_error = ValueError(f'sogou empty result: {str(result)[:180]}')
                    except Exception as exc:
                        req_error = exc
                        continue

                if req_error:
                    raise req_error
                raise ValueError('sogou request failed without response')
            except Exception as exc:
                if attempt == 0:
                    self._invalidate()
                    continue
                logger.warning(f'sogou translate failed: {exc}')
                return None

        return None
