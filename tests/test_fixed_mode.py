# tests/test_fixed_mode.py
import os
import sys
from unittest.mock import MagicMock

from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_app = QApplication.instance() or QApplication(sys.argv)


def _make_box(mode='temp'):
    box = MagicMock()
    box.mode = mode
    return box


def test_switching_to_fixed_stops_existing_temp_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}

    box1 = _make_box('temp')
    box2 = _make_box('temp')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._on_box_mode_changed('fixed')

    box1.set_mode.assert_called_once_with('fixed')
    box2.set_mode.assert_called_once_with('fixed')


def test_switching_to_temp_does_not_change_existing_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'fixed'
    ctrl._multi_results = {}

    box1 = _make_box('fixed')
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1}

    ctrl._on_box_mode_changed('temp')

    box1.set_mode.assert_not_called()


def test_translate_done_refreshes_active_subtitle():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'below'
    box._subtitle_active = True
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('ni hao')


def test_translate_done_refreshes_current_overlay_mode():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'over'
    box._subtitle_active = False
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_called_once_with('ni hao')


def test_translate_done_no_subtitle_refresh_when_overlay_disabled():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'off'
    box._subtitle_active = False
    box._pending_auto = False

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    box.show_subtitle.assert_not_called()


def test_translate_done_stores_last_translation_even_when_overlay_disabled():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'off'
    box._subtitle_active = False
    box._pending_auto = False
    box._last_translation = ''

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }
    ctrl._on_translate_done(result, box)

    assert box._last_translation == 'ni hao'


def test_refresh_overlay_font_styles_updates_all_boxes():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    box1 = MagicMock()
    box2 = MagicMock()
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._refresh_overlay_font_styles()

    box1.refresh_overlay_style.assert_called_once_with()
    box2.refresh_overlay_style.assert_called_once_with()


def test_refresh_overlay_font_styles_ignores_boxes_without_refresh_method():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)

    box1 = MagicMock()
    box2 = object()
    ctrl.box_manager = MagicMock()
    ctrl.box_manager._boxes = {1: box1, 2: box2}

    ctrl._refresh_overlay_font_styles()

    box1.refresh_overlay_style.assert_called_once_with()


def test_controller_defaults_to_fixed_box_mode(monkeypatch):
    import core.history
    import core.settings
    from core.controller import CoreController

    monkeypatch.setattr(core.settings, 'SettingsStore', lambda: MagicMock())
    monkeypatch.setattr(core.history, 'HistoryDB', lambda: MagicMock())

    ctrl = CoreController(_app)

    assert ctrl._box_mode == 'fixed'


def test_ocr_done_preserves_layout_payload():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.result_bar = MagicMock()
    ctrl._run_translate = MagicMock()
    ctrl.settings = MagicMock()
    ctrl.settings.get.side_effect = lambda key, default=None: {
        'para_split_enabled': True,
        'para_gap_ratio': 0.5,
    }.get(key, default)

    box = MagicMock()

    payload = {
        'text': 'hello world',
        'rows': [
            {'text': 'hello', 'box': [[0, 0], [40, 0], [40, 12], [0, 12]]},
            {'text': 'world', 'box': [[0, 16], [40, 16], [40, 28], [0, 28]]},
        ],
    }

    ctrl._on_ocr_done(payload, box)

    box.set_ocr_text.assert_called_once_with('hello world')
    assert box._last_ocr_rows == payload['rows']
    assert box._last_ocr_paragraphs == [
        {
            'text': 'hello\nworld',
            'rows': [
                {'text': 'hello', 'box': [[0, 0], [40, 0], [40, 12], [0, 12]], 'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 12}},
                {'text': 'world', 'box': [[0, 16], [40, 16], [40, 28], [0, 28]], 'rect': {'x': 0, 'y': 16, 'width': 40, 'height': 12}},
            ],
            'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 28},
        }
    ]
    assert box._last_paragraph_translations == []
    ctrl._run_translate.assert_called_once_with('hello world', box)


def test_translate_done_requests_paragraph_translation_for_over_para_mode():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._box_mode = 'single'
    ctrl._multi_results = {}
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()
    ctrl._run_paragraph_translate = MagicMock()

    box = MagicMock()
    box.box_id = 1
    box.mode = 'fixed'
    box._subtitle_mode = 'over_para'
    box._subtitle_active = False
    box._pending_auto = False
    box._last_ocr_paragraphs = [{'text': 'hello', 'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 12}}]
    box._last_paragraph_translations = []

    result = {
        'original': 'hello',
        'translated': 'ni hao',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }

    ctrl._on_translate_done(result, box)

    ctrl._run_paragraph_translate.assert_called_once_with(box)
    box.show_subtitle.assert_called_once_with('ni hao')


def test_overlay_mode_change_to_over_para_requests_paragraph_translation_when_missing():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._run_paragraph_translate = MagicMock()

    box = MagicMock()
    box._last_translation = 'ni hao'
    box._last_ocr_paragraphs = [{'text': 'hello', 'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 12}}]
    box._last_paragraph_translations = []

    CoreController._on_box_overlay_mode_changed(ctrl, box, 'over_para')

    ctrl._run_paragraph_translate.assert_called_once_with(box)
    box.show_subtitle.assert_called_once_with('ni hao')


def test_overlay_mode_change_to_over_para_uses_cached_paragraph_translation():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl._run_paragraph_translate = MagicMock()

    box = MagicMock()
    box._last_translation = 'ni hao'
    box._last_ocr_paragraphs = [{'text': 'hello', 'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 12}}]
    box._last_paragraph_translations = ['浣犲ソ']

    CoreController._on_box_overlay_mode_changed(ctrl, box, 'over_para')

    ctrl._run_paragraph_translate.assert_not_called()
    box.show_subtitle.assert_called_once_with('ni hao')


def test_paragraph_translate_done_updates_box_and_refreshes_over_para_subtitle():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)

    box = MagicMock()
    box._subtitle_mode = 'over_para'
    box._last_translation = 'ni hao'

    CoreController._on_paragraph_translate_done(ctrl, ['浣犲ソ'], box)

    assert box._last_paragraph_translations == ['浣犲ソ']
    box.show_subtitle.assert_called_once_with('ni hao')


def test_run_paragraph_translate_starts_one_worker_per_paragraph(monkeypatch):
    import ocr.ocr_worker
    from core.controller import CoreController

    class _Signal:
        def __init__(self):
            self.callbacks = []

        def connect(self, callback):
            self.callbacks.append(callback)

    class _FakeWorker:
        created = []

        def __init__(self, text, router, target_lang='zh-CN', source_lang='auto', parent=None):
            self.text = text
            self.router = router
            self.target_lang = target_lang
            self.source_lang = source_lang
            self.result_ready = _Signal()
            self.error_occurred = _Signal()
            self.finished = _Signal()
            self._translation_job_id = None
            self.started = False
            _FakeWorker.created.append(self)

        def start(self):
            self.started = True

    monkeypatch.setattr(ocr.ocr_worker, 'TranslationWorker', _FakeWorker)

    ctrl = CoreController.__new__(CoreController)
    ctrl.settings = MagicMock()
    ctrl.settings.get.side_effect = lambda key, default=None: {
        'target_language': 'zh-CN',
        'source_language': 'auto',
    }.get(key, default)
    ctrl.router = object()
    ctrl.result_bar = MagicMock()
    ctrl._workers = []
    ctrl._active_translation_workers = {}
    ctrl._cancelled_translation_jobs = set()
    ctrl._translation_job_seq = 0

    box = MagicMock()
    box._last_ocr_paragraphs = [
        {'text': 'para 1', 'rect': {'x': 0, 'y': 0, 'width': 40, 'height': 12}},
        {'text': 'para 2', 'rect': {'x': 0, 'y': 20, 'width': 40, 'height': 12}},
    ]

    CoreController._run_paragraph_translate(ctrl, box)

    assert [worker.text for worker in _FakeWorker.created] == ['para 1', 'para 2']
    assert all(worker.started for worker in _FakeWorker.created)
    assert len(ctrl._active_translation_workers) == 2
    ctrl.result_bar.set_stop_clear_busy.assert_called_once_with(True)


def test_single_paragraph_translation_done_refreshes_when_all_segments_arrive():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)

    box = MagicMock()
    box._subtitle_mode = 'over_para'
    box._last_translation = 'full translation'
    box._pending_paragraph_translations = [''] * 2

    CoreController._on_single_paragraph_translation_done(
        ctrl,
        {'translated': 'first'},
        box,
        0,
        worker=None,
    )

    box.show_subtitle.assert_not_called()

    CoreController._on_single_paragraph_translation_done(
        ctrl,
        {'translated': 'second'},
        box,
        1,
        worker=None,
    )

    assert box._last_paragraph_translations == ['first', 'second']
    box.show_subtitle.assert_called_once_with('full translation')


def test_retranslate_requested_runs_translation_without_ocr():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.result_bar = MagicMock()
    ctrl._run_translate = MagicMock()

    CoreController._on_retranslate_requested(ctrl, 'edited source')

    ctrl.result_bar.show_loading.assert_called_once()
    ctrl._run_translate.assert_called_once_with('edited source', None)


def test_trigger_explain_prefers_current_result_bar_source_text():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.result_bar = MagicMock()
    ctrl.result_bar._current_result = {'original': 'old source'}
    ctrl.result_bar.current_source_text.return_value = 'edited source'
    ctrl._on_explain_requested = MagicMock()

    CoreController._trigger_explain(ctrl)

    ctrl._on_explain_requested.assert_called_once_with('edited source')
