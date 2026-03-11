import http.cookiejar
import json
import logging
import urllib.parse
import urllib.request
from typing import Dict, Optional

logger = logging.getLogger(__name__)

_WEB_URL = 'https://fanyi.youdao.com/translate'
_MOBILE_URL = 'https://m.youdao.com/translate'
_UA_DESKTOP = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)
_UA_MOBILE = (
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Mobile Safari/537.36'
)

_LANG_MAP = {
    'auto': 'AUTO',
    'zh-CN': 'zh-CHS',
    'zh-TW': 'zh-CHT',
    'en': 'EN',
    'ja': 'JA',
    'ko': 'KO',
    'fr': 'FR',
    'de': 'DE',
    'es': 'ES',
    'ru': 'RU',
}


class YoudaoBackend:
    """Unofficial Youdao web translator backend with multi-endpoint fallback."""

    def __init__(self):
        self._cookie_jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )

    def _urlopen(self, req: urllib.request.Request, timeout: int = 8):
        return self._opener.open(req, timeout=timeout)

    def _parse_translation(self, result: dict) -> str:
        rows = result.get('translateResult', []) if isinstance(result, dict) else []
        text = ''.join(seg.get('tgt', '') for row in rows for seg in row if isinstance(seg, dict))
        return text.strip()

    def _decode_json_body(self, body: str) -> dict:
        data = body.strip()
        if not data:
            raise ValueError('empty body')
        if data[0] not in '{[':
            raise ValueError('non-json response body')
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            raise ValueError('unexpected non-dict payload')
        return parsed

    def _try_web_endpoint(self, text: str, src: str, tgt: str) -> str:
        payload = urllib.parse.urlencode({
            'i': text,
            'from': src,
            'to': tgt,
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_CLICKBUTTION',
        }).encode('utf-8')
        req = urllib.request.Request(
            _WEB_URL,
            data=payload,
            headers={
                'User-Agent': _UA_DESKTOP,
                'Referer': 'https://fanyi.youdao.com/',
                'Origin': 'https://fanyi.youdao.com',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
        )
        with self._urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8', errors='ignore')

        result = self._decode_json_body(body)
        ec = result.get('errorCode')
        if str(ec) not in ('0', 'None'):
            raise ValueError(f'youdao-web errorCode={ec}')
        translated = self._parse_translation(result)
        if not translated:
            raise ValueError('youdao-web empty translation')
        return translated

    def _try_mobile_endpoint(self, text: str, src: str, tgt: str) -> str:
        payload = urllib.parse.urlencode({
            'text': text,
            'type': f'{src}2{tgt}',
            'doctype': 'json',
        }).encode('utf-8')
        req = urllib.request.Request(
            _MOBILE_URL,
            data=payload,
            headers={
                'User-Agent': _UA_MOBILE,
                'Referer': 'https://m.youdao.com/',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            },
        )
        with self._urlopen(req, timeout=8) as resp:
            body = resp.read().decode('utf-8', errors='ignore')

        result = self._decode_json_body(body)
        ec = result.get('errorCode')
        if str(ec) not in ('0', 'None'):
            raise ValueError(f'youdao-mobile errorCode={ec}')
        translated = self._parse_translation(result)
        if not translated:
            raise ValueError('youdao-mobile empty translation')
        return translated

    def translate(self, text: str, target_lang: str = 'zh-CN',
                  source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None

        src = _LANG_MAP.get(source_lang, 'AUTO')
        tgt = _LANG_MAP.get(target_lang, 'zh-CHS')

        errors = []
        for name, func in (
            ('web', self._try_web_endpoint),
            ('mobile', self._try_mobile_endpoint),
        ):
            try:
                translated = func(text, src, tgt)
                if translated:
                    return {
                        'original': text,
                        'translated': translated,
                        'backend': 'youdao',
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                    }
            except Exception as exc:
                errors.append(f'{name}:{exc}')

        logger.warning('youdao translate failed: %s', ' | '.join(errors))
        return None
