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

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        t = self._get_translator()
        if t is None:
            return None
        text = text.strip()
        if not text:
            return None
        lang_map = {'zh-CN': 'ZH', 'en': 'EN-US', 'ja': 'JA', 'ko': 'KO',
                    'fr': 'FR', 'de': 'DE', 'es': 'ES', 'ru': 'RU'}
        tgt = lang_map.get(target_lang, 'ZH')
        try:
            result = t.translate_text(text, target_lang=tgt)
            return {
                'original': text, 'translated': result.text, 'backend': 'deepl',
                'source_lang': str(result.detected_source_lang), 'target_lang': target_lang,
            }
        except Exception:
            return None
