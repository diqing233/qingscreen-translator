import os
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_busy_stop_clear_requests_interruption_and_clears_result_bar():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.result_bar = MagicMock()
    ctrl._active_translation_workers = {}
    ctrl._cancelled_translation_jobs = set()

    worker = MagicMock()
    worker._translation_job_id = 7
    ctrl._active_translation_workers[worker._translation_job_id] = worker

    CoreController._on_stop_clear_requested(ctrl)

    worker.requestInterruption.assert_called_once()
    assert ctrl._cancelled_translation_jobs == {7}
    ctrl.result_bar.clear_current_content.assert_called_once()
    ctrl.result_bar.set_stop_clear_busy.assert_called_once_with(False)


def test_idle_stop_clear_only_clears_result_bar():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.result_bar = MagicMock()
    ctrl._active_translation_workers = {}
    ctrl._cancelled_translation_jobs = set()

    CoreController._on_stop_clear_requested(ctrl)

    ctrl.result_bar.clear_current_content.assert_called_once()
    ctrl.result_bar.set_stop_clear_busy.assert_not_called()
    assert ctrl._cancelled_translation_jobs == set()


def test_cancelled_translation_result_is_ignored():
    from core.controller import CoreController

    ctrl = CoreController.__new__(CoreController)
    ctrl.history = MagicMock()
    ctrl.result_bar = MagicMock()
    ctrl._box_mode = 'temp'
    ctrl._multi_results = {}
    ctrl._cancelled_translation_jobs = {11}

    box = MagicMock()
    box.mode = 'temp'
    box.box_id = 1

    worker = MagicMock()
    worker._translation_job_id = 11

    result = {
        'original': 'hello',
        'translated': '你好',
        'source_lang': 'en',
        'target_lang': 'zh-CN',
        'backend': 'google',
    }

    CoreController._on_translate_done(ctrl, result, box, worker)

    ctrl.history.add.assert_not_called()
    ctrl.result_bar.show_result.assert_not_called()
    box.start_dismiss_timer.assert_not_called()
