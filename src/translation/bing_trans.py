import http.cookiejar
import json
import logging
import re
import threading
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_LANG_MAP = {
    'auto': 'auto-detect',
    'zh-CN': 'zh-Hans',
    'zh-TW': 'zh-Hant',
    'en': 'en',
    'ja': 'ja',
    'ko': 'ko',
    'fr': 'fr',
    'de': 'de',
    'es': 'es',
    'ru': 'ru',
}

_PAGE_URLS = (
    'https://cn.bing.com/translator',
    'https://www.bing.com/translator',
)
_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)
_IG_RE = re.compile(r'IG:"([^"]+)"')
_IID_RE = re.compile(r'data-iid="([^"]+)"')
_KEY_TOKEN_RES = (
    re.compile(r'params_AbusePreventionHelper\s*=\s*\[\s*(\d+)\s*,\s*"([^"]+)"'),
    re.compile(r'"key"\s*:\s*(\d+)\s*,\s*"token"\s*:\s*"([^"]+)"'),
    re.compile(r'AbusePreventionHelper\s*=\s*\[\s*(\d+)\s*,\s*"([^"]+)"'),
)


class BingBackend:
    """Unofficial Bing web translator backend."""

    def __init__(self):
        self._page_url = _PAGE_URLS[0]
        self._ig = ''
        self._iid = 'translator.5022'
        self._key = ''
        self._token = ''
        self._token_expiry = 0.0
        self._lock = threading.Lock()
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )

    def prefetch(self):
        t = threading.Thread(target=self._safe_refresh, daemon=True)
        t.start()

    def _safe_refresh(self):
        try:
            self._refresh()
        except Exception as exc:
            logger.warning(f'bing prefetch failed: {exc}')

    def _extract_key_token(self, html: str) -> Tuple[str, str]:
        for pattern in _KEY_TOKEN_RES:
            match = pattern.search(html)
            if match:
                return match.group(1), match.group(2)
        return '', ''

    def _urlopen(self, req: urllib.request.Request, timeout: int = 10):
        return self._opener.open(req, timeout=timeout)

    def _refresh(self):
        last_error: Optional[Exception] = None
        for page_url in _PAGE_URLS:
            try:
                req = urllib.request.Request(
                    page_url,
                    headers={
                        'User-Agent': _UA,
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    },
                )
                with self._urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')

                ig_m = _IG_RE.search(html)
                key, token = self._extract_key_token(html)
                if not ig_m or not key or not token:
                    raise ValueError('missing ig/key/token from translator page')

                iid_m = _IID_RE.search(html)
                self._page_url = page_url
                self._ig = ig_m.group(1)
                self._iid = iid_m.group(1) if iid_m else 'translator.5022'
                self._key = key
                self._token = token
                # Bing rotates these values frequently.
                self._token_expiry = time.time() + 8 * 60
                return
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            raise last_error
        raise RuntimeError('unable to refresh bing session')

    def _extract_translation(self, result) -> str:
        if isinstance(result, list) and result:
            first = result[0] if isinstance(result[0], dict) else {}
            trans = first.get('translations') if isinstance(first, dict) else None
            if isinstance(trans, list) and trans:
                text = trans[0].get('text', '') if isinstance(trans[0], dict) else ''
                if text:
                    return text

        if isinstance(result, dict):
            trans = result.get('translations')
            if isinstance(trans, list) and trans:
                text = trans[0].get('text', '') if isinstance(trans[0], dict) else ''
                if text:
                    return text

        return ''

    def _get_origin(self, page_url: str) -> str:
        parts = urllib.parse.urlsplit(page_url)
        return f'{parts.scheme}://{parts.netloc}'

    def _invalidate(self):
        with self._lock:
            self._token_expiry = 0.0
            self._ig = ''
            self._key = ''
            self._token = ''
            self._cookie_jar = http.cookiejar.CookieJar()
            self._opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self._cookie_jar)
            )

    def translate(self, text: str, target_lang: str = 'zh-CN',
                  source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None

        src = _LANG_MAP.get(source_lang, 'auto-detect')
        tgt = _LANG_MAP.get(target_lang, 'zh-Hans')

        for attempt in range(2):
            try:
                with self._lock:
                    if time.time() >= self._token_expiry or not (self._ig and self._key and self._token):
                        self._refresh()
                    page_url = self._page_url
                    ig = self._ig
                    iid = self._iid
                    key = self._key
                    token = self._token

                data = urllib.parse.urlencode({
                    'fromLang': src,
                    'to': tgt,
                    'text': text,
                    'tryFetchingGenderDebiasedTranslations': 'true',
                    'token': token,
                    'key': key,
                }).encode('utf-8')

                origin = self._get_origin(page_url)
                trans_url = f'{origin}/ttranslatev3?isVertical=1&IG={ig}&IID={iid}'
                req = urllib.request.Request(
                    trans_url,
                    data=data,
                    headers={
                        'User-Agent': _UA,
                        'Referer': page_url,
                        'Origin': origin,
                        'Accept': 'application/json, text/plain, */*',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    },
                )
                with self._urlopen(req, timeout=10) as resp:
                    body = resp.read().decode('utf-8', errors='ignore')
                result = json.loads(body)
                translated = self._extract_translation(result)
                if not translated:
                    raise ValueError(f'empty translation payload: {str(result)[:180]}')

                return {
                    'original': text,
                    'translated': translated,
                    'backend': 'bing',
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                }
            except Exception as exc:
                if attempt == 0:
                    self._invalidate()
                    continue
                logger.warning(f'bing translate failed: {exc}')
                return None

        return None
