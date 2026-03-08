import requests
import hashlib
import random
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

        lang_map = {'zh-CN': 'zh', 'en': 'en', 'ja': 'jp', 'ko': 'kor',
                    'fr': 'fra', 'de': 'de', 'es': 'spa', 'ru': 'ru', 'auto': 'auto'}
        tgt = lang_map.get(target_lang, 'zh')
        src = lang_map.get(source_lang, 'auto')

        salt = str(random.randint(10000, 99999))
        sign = hashlib.md5((self.appid + text + salt + self.key).encode()).hexdigest()

        try:
            resp = requests.get(self.API_URL, params={
                'q': text, 'from': src, 'to': tgt,
                'appid': self.appid, 'salt': salt, 'sign': sign
            }, timeout=5)
            data = resp.json()
            if 'trans_result' in data:
                translated = '\n'.join(r['dst'] for r in data['trans_result'])
                return {
                    'original': text, 'translated': translated, 'backend': 'baidu',
                    'source_lang': data.get('from', source_lang), 'target_lang': target_lang,
                }
        except Exception:
            pass
        return None
