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
        from translation.youdao_trans import YoudaoBackend
        from translation.sogou_trans import SogouBackend
        from translation.bing_trans import BingBackend
        from translation.baidu_trans import BaiduBackend
        from translation.deepl_trans import DeepLBackend
        from translation.ai_trans import AIBackend

        keys = self._settings.get('api_keys', {})
        self._backends['dictionary'] = DictionaryBackend()
        self._backends['google']     = GoogleBackend()
        self._backends['youdao']     = YoudaoBackend()
        self._backends['sogou']      = SogouBackend()
        self._backends['bing']       = BingBackend()
        self._backends['baidu']      = BaiduBackend(keys.get('baidu_appid', ''), keys.get('baidu_key', ''))
        self._backends['deepl'] = DeepLBackend(keys.get('deepl_key', ''))
        for provider in ('deepseek', 'openai', 'claude', 'zhipu', 'siliconflow', 'moonshot'):
            self._backends[provider] = AIBackend(provider=provider, api_key=keys.get(f'{provider}_key', ''))

        # Bing 已启用时提前在后台获取 token
        enabled = set(self._settings.get('enabled_backends', []))
        if 'bing' in enabled:
            self._backends['bing'].prefetch()

    def reload(self):
        self._init_backends()

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        if not text:
            return None
        order = self._settings.get('translation_order', [])
        enabled = set(self._settings.get('enabled_backends', ['dictionary', 'google']))

        google_in_order = False
        for name in order:
            if name == 'google':
                google_in_order = True
            if name not in enabled:
                continue
            backend = self._backends.get(name)
            if backend is None:
                continue
            try:
                result = backend.translate(text, target_lang=target_lang, source_lang=source_lang)
                if result and result.get('translated'):
                    return result
            except Exception as e:
                logger.warning(f'Backend {name} failed: {e}')

        # 所有启用后端均无结果时，用谷歌翻译兜底（若用户未禁用且尚未尝试）
        if 'google' in enabled and not google_in_order:
            backend = self._backends.get('google')
            if backend:
                try:
                    result = backend.translate(text, target_lang=target_lang, source_lang=source_lang)
                    if result and result.get('translated'):
                        logger.info('Google fallback used')
                        return result
                except Exception as e:
                    logger.warning(f'Google fallback failed: {e}')
        return None

    def get_ai_backend(self):
        enabled = set(self._settings.get('enabled_backends', []))
        for p in ('deepseek', 'openai', 'claude', 'zhipu', 'siliconflow', 'moonshot'):
            if p in enabled and p in self._backends:
                b = self._backends[p]
                if b.api_key:
                    return b
        return None
