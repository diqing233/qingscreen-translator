from typing import Optional, Dict

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
    'new': '新的', 'old': '旧的', 'big': '大的', 'small': '小的',
    'fast': '快速', 'slow': '慢的', 'hot': '热的', 'cold': '冷的',
    'happy': '快乐', 'sad': '悲伤', 'beautiful': '美丽', 'ugly': '丑陋',
}

class DictionaryBackend:
    MAX_WORDS = 4

    def translate(self, text: str, target_lang: str = 'zh-CN', source_lang: str = 'auto') -> Optional[Dict]:
        text = text.strip()
        words = text.split()
        if len(words) > self.MAX_WORDS:
            return None

        key = text.lower().rstrip('.,!?')
        if key in QUICK_DICT:
            return {
                'original': text,
                'translated': QUICK_DICT[key],
                'backend': 'dictionary',
                'source_lang': 'en',
                'target_lang': target_lang,
            }

        if len(words) == 1:
            return self._wordnet_lookup(text, target_lang)
        return None

    def _wordnet_lookup(self, word: str, target_lang: str) -> Optional[Dict]:
        try:
            from nltk.corpus import wordnet as wn
            synsets = wn.synsets(word.lower())
            if not synsets:
                return None
            definition = synsets[0].definition()
            lemmas = synsets[0].lemma_names()
            translated = definition
            if len(lemmas) > 1:
                translated += f' (syn: {", ".join(lemmas[1:3])})'
            return {
                'original': word,
                'translated': translated,
                'backend': 'dictionary',
                'source_lang': 'en',
                'target_lang': target_lang,
            }
        except Exception:
            return None
