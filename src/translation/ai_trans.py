from typing import Optional, Dict

TRANSLATE_PROMPT = """将以下文本翻译成{target_lang_name}。只返回翻译结果，不要解释，不要加引号。

文本：{text}"""

EXPLAIN_PROMPT = """对以下文字进行详细解释：
- 如果是单词：给出中文含义、词性、用法说明、例句
- 如果是短语或句子：给出中文含义、背景语境、使用场合

文字：{text}

用中文回答，简洁清晰。"""

LANG_NAMES = {
    'zh-CN': '简体中文', 'zh-TW': '繁体中文', 'en': '英语',
    'ja': '日语', 'ko': '韩语', 'fr': '法语', 'de': '德语',
    'es': '西班牙语', 'ru': '俄语', 'ar': '阿拉伯语',
}

class AIBackend:
    def __init__(self, provider: str = 'deepseek', api_key: str = ''):
        self.provider = provider
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
                    'original': text, 'translated': result, 'backend': self.provider,
                    'source_lang': source_lang, 'target_lang': target_lang,
                }
        except Exception:
            return None
        return None

    def explain(self, text: str) -> Optional[str]:
        if not self.api_key:
            return None
        try:
            return self._call_api(EXPLAIN_PROMPT.format(text=text.strip()))
        except Exception:
            return None

    def _call_api(self, prompt: str) -> Optional[str]:
        if self.provider in ('openai', 'deepseek'):
            return self._call_openai_compatible(prompt)
        elif self.provider == 'claude':
            return self._call_claude(prompt)
        return None

    def _call_openai_compatible(self, prompt: str) -> Optional[str]:
        from openai import OpenAI
        base_urls = {'openai': 'https://api.openai.com/v1', 'deepseek': 'https://api.deepseek.com/v1'}
        models = {'openai': 'gpt-4o-mini', 'deepseek': 'deepseek-chat'}
        client = OpenAI(api_key=self.api_key, base_url=base_urls.get(self.provider))
        resp = client.chat.completions.create(
            model=models.get(self.provider, 'gpt-4o-mini'),
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1000, temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    def _call_claude(self, prompt: str) -> Optional[str]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001', max_tokens=1000,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return msg.content[0].text.strip()
