from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class TranslationRouter:
    def __init__(self, settings):
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
        self._backends['baidu'] = BaiduBackend(keys.get('baidu_appid', ''), keys.get('baidu_key', ''))
        self._backends['deepl'] = DeepLBackend(keys.get('deepl_key', ''))
        for provider in ('deepseek', 'openai', 'claude'):
            self._backends[provider] = AIBackend(provider=provider, api_key=keys.get(f'{provider}_key', ''))

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
            if name == 'dictionary' and word_count > 4:
                continue
            try:
                result = backend.translate(text, target_lang=target_lang, source_lang=source_lang)
                if result and result.get('translated'):
                    return result
            except Exception as e:
                logger.warning(f'Backend {name} failed: {e}')
        return None

    def get_ai_backend(self):
        enabled = set(self._settings.get('enabled_backends', []))
        for p in ('deepseek', 'openai', 'claude'):
            if p in enabled and p in self._backends:
                b = self._backends[p]
                if b.api_key:
                    return b
        return None
