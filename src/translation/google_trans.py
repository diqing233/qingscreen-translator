from typing import Optional, Dict

class GoogleBackend:
    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None
        try:
            from deep_translator import GoogleTranslator
            lang_map = {
                'zh-CN': 'zh-CN', 'zh-TW': 'zh-TW', 'en': 'en',
                'ja': 'ja', 'ko': 'ko', 'fr': 'fr', 'de': 'de',
                'es': 'es', 'ru': 'ru', 'ar': 'ar', 'auto': 'auto',
            }
            src = lang_map.get(source_lang, 'auto')
            tgt = lang_map.get(target_lang, 'zh-CN')
            translator = GoogleTranslator(source=src, target=tgt)
            result = translator.translate(text)
            if result:
                return {
                    'original': text,
                    'translated': result,
                    'backend': 'google',
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                }
        except Exception:
            return None
        return None
