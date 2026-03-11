import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock


class _FakeResponse:
    def __init__(self, body: str):
        self._body = body.encode('utf-8')

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_bing_translate_uses_cn_host_when_cn_session_is_active():
    from translation.bing_trans import BingBackend

    backend = BingBackend()
    calls = []
    page_html = """
    <html>
      <body data-iid="translator.5022">
        IG:"IGTOKEN"
        params_AbusePreventionHelper = [123456, "TOKEN123"]
      </body>
    </html>
    """

    def fake_urlopen(req, timeout=10):
        calls.append((req.full_url, req.get_header('Origin'), req.get_header('Referer')))
        if req.full_url == 'https://www.bing.com/translator':
            raise OSError('www.bing.com blocked on domestic network')
        if req.full_url == 'https://cn.bing.com/translator':
            return _FakeResponse(page_html)
        if req.full_url.startswith('https://cn.bing.com/ttranslatev3'):
            assert req.get_header('Origin') == 'https://cn.bing.com'
            assert req.get_header('Referer') == 'https://cn.bing.com/translator'
            return _FakeResponse('[{"translations":[{"text":"你好"}]}]')
        raise OSError(f'unexpected url: {req.full_url}')

    backend._urlopen = fake_urlopen

    result = backend.translate('hello')

    assert result is not None
    assert result['translated'] == '你好'
    assert any(url.startswith('https://cn.bing.com/ttranslatev3') for url, _, _ in calls)


def test_router_does_not_force_google_fallback_when_google_is_disabled():
    from translation.router import TranslationRouter

    settings = MagicMock()
    settings.get.side_effect = lambda key, default=None: {
        'translation_order': ['bing'],
        'enabled_backends': ['bing'],
    }.get(key, default)

    router = TranslationRouter.__new__(TranslationRouter)
    router._settings = settings

    bing_backend = MagicMock()
    bing_backend.translate.return_value = None

    google_backend = MagicMock()
    google_backend.translate.return_value = {
        'original': 'hello',
        'translated': '你好',
        'backend': 'google',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
    }

    router._backends = {
        'bing': bing_backend,
        'google': google_backend,
    }

    result = TranslationRouter.translate(router, 'hello')

    assert result is None
    google_backend.translate.assert_not_called()
