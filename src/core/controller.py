import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject

logger = logging.getLogger(__name__)


class CoreController(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._workers = []  # keep workers alive
        from core.settings import SettingsStore
        from core.history import HistoryDB
        self.settings = SettingsStore()
        self.history = HistoryDB()

    def start(self):
        from translation.router import TranslationRouter
        from core.box_manager import BoxManager
        from ui.selection_overlay import SelectionOverlay
        from ui.result_bar import ResultBar
        from ui.tray import SystemTray

        self.router = TranslationRouter(self.settings)
        self.box_manager = BoxManager(self.settings)
        self.overlay = SelectionOverlay()
        self.result_bar = ResultBar(self.settings)
        self.tray = SystemTray()

        # 连接信号
        self.overlay.selection_made.connect(self._on_selection_made)
        self.box_manager.translate_box.connect(self._on_translate_box)
        self.result_bar.explain_requested.connect(self._on_explain_requested)
        self.result_bar.history_requested.connect(self._show_history)
        self.result_bar.settings_requested.connect(self._show_settings)
        self.tray.select_triggered.connect(self._start_selection)
        self.tray.settings_triggered.connect(self._show_settings)
        self.tray.history_triggered.connect(self._show_history)
        self.tray.quit_triggered.connect(self.app.quit)

        self.result_bar.show()
        self.tray.show()
        self._setup_hotkeys()
        logger.info('ScreenTranslator started')

    def _setup_hotkeys(self):
        try:
            from pynput import keyboard

            def on_activate_select():
                self._start_selection()

            def on_activate_explain():
                self._trigger_explain()

            hotkeys = keyboard.GlobalHotKeys({
                '<alt>+q': on_activate_select,
                '<alt>+e': on_activate_explain,
            })
            hotkeys.start()
            self._hotkey_listener = hotkeys
        except Exception as e:
            logger.warning(f'热键设置失败: {e}')

    def _start_selection(self):
        self.overlay.show_overlay()

    def _trigger_explain(self):
        if self.result_bar._current_result:
            text = self.result_bar._current_result.get('original', '')
            if text:
                self._on_explain_requested(text)

    def _on_selection_made(self, rect):
        box = self.box_manager.create_box(rect)
        self.result_bar.show_loading('识别中...')
        self._run_ocr(box)

    def _run_ocr(self, box):
        from ocr.ocr_worker import OCRWorker
        worker = OCRWorker(box.region)
        worker.result_ready.connect(lambda text, _: self._on_ocr_done(text, box))
        worker.error_occurred.connect(lambda e: self.result_bar.show_error(f'OCR: {e}'))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_ocr_done(self, text: str, box):
        if not text.strip():
            self.result_bar.show_error('未识别到文字，请重新框选')
            box.start_dismiss_timer()
            return
        box.set_ocr_text(text)
        self.result_bar.show_loading('翻译中...')
        self._run_translate(text, box)

    def _run_translate(self, text: str, box):
        from ocr.ocr_worker import TranslationWorker
        target = self.settings.get('target_language', 'zh-CN')
        worker = TranslationWorker(text, self.router, target_lang=target)
        worker.result_ready.connect(lambda r: self._on_translate_done(r, box))
        worker.error_occurred.connect(self.result_bar.show_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_translate_done(self, result: dict, box):
        self.result_bar.show_result(result)
        try:
            self.history.add(
                result.get('original', ''),
                result.get('translated', ''),
                result.get('source_lang', ''),
                result.get('target_lang', ''),
                result.get('backend', ''),
            )
        except Exception as e:
            logger.warning(f'History save failed: {e}')
        box.start_dismiss_timer()

    def _on_translate_box(self, box):
        self._run_ocr(box)

    def _on_explain_requested(self, text: str):
        from ocr.ocr_worker import ExplainWorker
        ai = self.router.get_ai_backend()
        worker = ExplainWorker(text, ai)
        worker.result_ready.connect(self.result_bar.show_explain)
        worker.error_occurred.connect(self.result_bar.show_error)
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _cleanup_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _show_history(self):
        from ui.history_window import HistoryWindow
        if not hasattr(self, '_history_win') or self._history_win is None or not self._history_win.isVisible():
            self._history_win = HistoryWindow(self.history)
            self._history_win.show()
        else:
            self._history_win.activateWindow()
            self._history_win.raise_()

    def _show_settings(self):
        from ui.settings_window import SettingsWindow
        if not hasattr(self, '_settings_win') or self._settings_win is None or not self._settings_win.isVisible():
            self._settings_win = SettingsWindow(self.settings)
            self._settings_win.settings_saved.connect(self.router.reload)
            self._settings_win.show()
        else:
            self._settings_win.activateWindow()
            self._settings_win.raise_()
