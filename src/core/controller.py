import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QCheckBox
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


def _fmt_hotkey(key_str: str) -> str:
    """Convert 'alt+q' → '<alt>+q' for pynput GlobalHotKeys."""
    modifiers = {'alt', 'ctrl', 'shift', 'cmd', 'win'}
    parts = []
    for p in key_str.lower().split('+'):
        p = p.strip()
        parts.append(f'<{p}>' if p in modifiers else p)
    return '+'.join(parts)



class CoreController(QObject):
    _sig_start_selection = pyqtSignal()
    _sig_trigger_explain = pyqtSignal()
    _sig_toggle_boxes    = pyqtSignal()
    _sig_mode_temp       = pyqtSignal()
    _sig_mode_fixed      = pyqtSignal()
    _sig_mode_multi      = pyqtSignal()
    _sig_mode_ai         = pyqtSignal()

    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self._workers = []
        self._active_translation_workers = {}
        self._cancelled_translation_jobs = set()
        self._translation_job_seq = 0
        self._box_mode = 'fixed'
        self._translate_mode = 'manual'
        self._multi_results: dict  = {}   # box_id → result dict（多框模式）
        self._box_img_hashes: dict = {}   # box_id → float（自动翻译变化检测）

        from core.settings import SettingsStore
        from core.history import HistoryDB
        self.settings = SettingsStore()
        self.history = HistoryDB()

        self._sig_start_selection.connect(self._start_selection)
        self._sig_trigger_explain.connect(self._trigger_explain)
        self._sig_toggle_boxes.connect(self._toggle_boxes)
        self._sig_mode_temp.connect(lambda: self._activate_mode('temp'))
        self._sig_mode_fixed.connect(lambda: self._activate_mode('fixed'))
        self._sig_mode_multi.connect(lambda: self._activate_mode('multi'))
        self._sig_mode_ai.connect(lambda: self._activate_mode('ai'))

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

        self.overlay.selection_made.connect(self._on_selection_made)
        self.box_manager.translate_box.connect(self._on_translate_box)
        self.box_manager.box_removed.connect(self._on_box_removed)
        self.result_bar.start_selection_requested.connect(self._start_selection)
        self.result_bar.stop_clear_requested.connect(self._on_stop_clear_requested)
        self.result_bar.explain_requested.connect(self._on_explain_requested)
        self.result_bar.retranslate_requested.connect(self._on_retranslate_requested)
        self.result_bar.history_requested.connect(self._show_history)
        self.result_bar.settings_requested.connect(self._show_settings)
        self.result_bar.close_requested.connect(self._handle_result_bar_close)
        self.result_bar.box_mode_changed.connect(self._on_box_mode_changed)
        self.result_bar.translate_mode_changed.connect(self._on_translate_mode_changed)
        self.result_bar.target_language_changed.connect(self._on_target_language_changed)
        self.result_bar.source_language_changed.connect(self._on_source_language_changed)
        self.result_bar.overlay_requested.connect(self._on_overlay_requested)
        self.result_bar.overlay_font_delta_changed.connect(self._refresh_overlay_font_styles)
        self.tray.show_main_requested.connect(self._restore_main_window)
        self.tray.select_triggered.connect(self._sig_start_selection)
        self.tray.settings_triggered.connect(self._show_settings)
        self.tray.history_triggered.connect(self._show_history)
        self.tray.quit_triggered.connect(self.app.quit)

        self.result_bar.show()
        self.tray.show()
        self._setup_hotkeys()
        self._refresh_mode_tooltips()
        logger.info('ScreenTranslator started')

    # ── OCR payload 规范化 ───────────────────────────────────────

    def _normalize_ocr_payload(self, payload: dict) -> dict:
        from core.overlay_layout import group_rows_into_paragraphs
        if not isinstance(payload, dict):
            return {'text': str(payload or ''), 'rows': [], 'paragraphs': [], 'para_texts': []}
        rows = list(payload.get('rows', []) or [])
        para_enabled = self.settings.get('para_split_enabled', True)
        gap_ratio = float(self.settings.get('para_gap_ratio', 0.5))

        paras = []
        para_texts = []
        if para_enabled and rows:
            paras = group_rows_into_paragraphs(rows, gap_ratio=gap_ratio)

        if para_enabled and len(paras) >= 2:
            para_texts = [' '.join(r['text'] for r in p['rows']) for p in paras]
            text = '\n\n'.join(para_texts)
        else:
            text = str(payload.get('text', ''))
            paras = []
            para_texts = []

        return {
            'text':       text,
            'rows':       rows,
            'paragraphs': paras,
            'para_texts': para_texts,
        }

    # ── 热键 ────────────────────────────────────────────────────

    def _setup_hotkeys(self):
        try:
            from pynput import keyboard

            # 使用命名函数（不用 lambda），确保 pynput 子线程回调稳定
            def on_select():   self._sig_start_selection.emit()
            def on_explain():  self._sig_trigger_explain.emit()
            def on_toggle():   self._sig_toggle_boxes.emit()
            def on_mode1():    self._sig_mode_temp.emit()
            def on_mode2():    self._sig_mode_fixed.emit()
            def on_mode3():    self._sig_mode_multi.emit()
            def on_mode4():    self._sig_mode_ai.emit()

            core_map = {
                _fmt_hotkey(self.settings.get('hotkey_select',       'alt+q')): on_select,
                _fmt_hotkey(self.settings.get('hotkey_explain',      'alt+e')): on_explain,
                _fmt_hotkey(self.settings.get('hotkey_toggle_boxes', 'alt+w')): on_toggle,
            }
            # 模式切换热键单独加入，若注册失败不影响核心热键
            try:
                core_map[_fmt_hotkey(self.settings.get('hotkey_mode_temp',  'alt+1'))] = on_mode1
                core_map[_fmt_hotkey(self.settings.get('hotkey_mode_fixed', 'alt+2'))] = on_mode2
                core_map[_fmt_hotkey(self.settings.get('hotkey_mode_multi', 'alt+3'))] = on_mode3
                core_map[_fmt_hotkey(self.settings.get('hotkey_mode_ai',    'alt+4'))] = on_mode4
            except Exception as e:
                logger.warning(f'模式切换热键格式错误（已忽略）: {e}')

            try:
                hotkeys = keyboard.GlobalHotKeys(core_map)
            except Exception:
                # 如全量注册失败，回退到仅核心三键
                logger.warning('完整热键注册失败，回退核心三键')
                core_map = {
                    _fmt_hotkey(self.settings.get('hotkey_select',  'alt+q')): on_select,
                    _fmt_hotkey(self.settings.get('hotkey_explain', 'alt+e')): on_explain,
                    _fmt_hotkey(self.settings.get('hotkey_toggle_boxes', 'alt+w')): on_toggle,
                }
                hotkeys = keyboard.GlobalHotKeys(core_map)

            hotkeys.start()
            self._hotkey_listener = hotkeys
            logger.info(f'热键注册成功: {list(core_map.keys())}')
        except Exception as e:
            logger.warning(f'热键设置失败: {e}')

    def _reload_hotkeys(self):
        if hasattr(self, '_hotkey_listener'):
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        self._setup_hotkeys()
        self._refresh_mode_tooltips()

    def _refresh_mode_tooltips(self):
        if hasattr(self, 'result_bar'):
            self.result_bar.update_mode_tooltips(
                self.settings.get('hotkey_mode_temp',  'alt+1'),
                self.settings.get('hotkey_mode_fixed', 'alt+2'),
                self.settings.get('hotkey_mode_multi', 'alt+3'),
                self.settings.get('hotkey_mode_ai',    'alt+4'),
            )

    def _activate_mode(self, mode: str):
        self._box_mode = mode
        self.result_bar._on_mode_btn_click(mode)

    # ── 设置同步 ─────────────────────────────────────────────────

    def _on_box_mode_changed(self, mode: str):
        self._box_mode = mode
        if mode != 'multi':
            self._multi_results.clear()
        if mode == 'fixed':
            for box in self.box_manager._boxes.values():
                box.set_mode('fixed')

    def _on_translate_mode_changed(self, mode: str):
        self._translate_mode = mode
        if mode == 'auto':
            for box in self.box_manager._boxes.values():
                if box.mode == 'fixed':
                    box.start_auto_translate()
        else:
            for box in self.box_manager._boxes.values():
                box.stop_auto_translate()

    def _on_target_language_changed(self, lang: str):
        self.router.reload()

    def _on_source_language_changed(self, lang: str):
        logger.info(f'Source language -> {lang}')

    # ── 操作 ────────────────────────────────────────────────────

    def _start_selection(self):
        self.overlay.show_overlay()

    def _handle_result_bar_close(self):
        behavior = self.settings.get('close_button_behavior', 'ask')
        remember = False
        if behavior == 'ask':
            behavior, remember = self._ask_close_behavior()
            if behavior is None:
                return
            if remember:
                self.settings.set('close_button_behavior', behavior)

        if behavior == 'tray':
            self._send_main_window_to_tray()
        elif behavior == 'quit':
            self.app.quit()

    def _send_main_window_to_tray(self):
        if not self._is_tray_available():
            self._warn_tray_unavailable()
            self.app.quit()
            return

        if hasattr(self.result_bar, 'mark_hidden_to_tray'):
            self.result_bar.mark_hidden_to_tray(True)
        else:
            self.result_bar._hidden_to_tray = True
        self.result_bar.hide()

    def _restore_main_window(self):
        if hasattr(self.result_bar, 'mark_hidden_to_tray'):
            self.result_bar.mark_hidden_to_tray(False)
        else:
            self.result_bar._hidden_to_tray = False
        self.result_bar.show()
        self.result_bar.raise_()
        self.result_bar.activateWindow()

    def _ask_close_behavior(self):
        box = QMessageBox(self.result_bar)
        box.setWindowTitle('关闭程序')
        box.setText('关闭后要做什么？')
        box.setInformativeText('之后可以在“设置 -> 通用 -> 关闭按钮行为”里修改')
        tray_button = box.addButton('放到托盘', QMessageBox.AcceptRole)
        quit_button = box.addButton('退出程序', QMessageBox.DestructiveRole)
        cancel_button = box.addButton('取消', QMessageBox.RejectRole)
        remember_box = QCheckBox('记住我的选择，下次不再询问', box)
        remember_box.setChecked(True)
        box.setCheckBox(remember_box)
        box.setDefaultButton(tray_button)
        box.exec_()

        clicked = box.clickedButton()
        if clicked is tray_button:
            return 'tray', remember_box.isChecked()
        if clicked is quit_button:
            return 'quit', remember_box.isChecked()
        if clicked is cancel_button:
            return None, False
        return None, False

    def _is_tray_available(self):
        from PyQt5.QtWidgets import QSystemTrayIcon

        return QSystemTrayIcon.isSystemTrayAvailable()

    def _warn_tray_unavailable(self):
        QMessageBox.warning(
            self.result_bar,
            '系统托盘不可用',
            '当前系统托盘不可用，将直接退出程序。'
        )

    def _toggle_boxes(self):
        self.box_manager.toggle_all_visibility()

    def _on_selection_made(self, rect):
        """框选完成：先等 overlay 从合成器消失，再截图；截图后才创建翻译框"""
        if self._box_mode != 'multi':
            self.box_manager.clear_all()
        self.result_bar.show_loading('识别中...')
        # 给 DWM 合成器 150ms 完全清除 overlay，之后再开始截图
        # 此时翻译框还未创建，截图区域无任何遮挡
        QTimer.singleShot(150, lambda: self._run_ocr_for_rect(rect))

    def _run_ocr_for_rect(self, rect):
        """在截图前不创建翻译框，确保截图区域干净"""
        from ocr.ocr_worker import OCRWorker
        worker = OCRWorker(rect)
        worker.result_ready.connect(
            lambda payload, region, w=worker: self._on_ocr_done_for_rect(payload, region, w))
        worker.error_occurred.connect(
            lambda e: self.result_bar.show_error(f'OCR: {e}'))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_ocr_done_for_rect(self, payload, rect, worker=None):
        """截图完成后才创建翻译框，避免框遮挡被截图区域"""
        box = self.box_manager.create_box(rect)
        if hasattr(box, 'overlay_font_delta_changed'):
            box.overlay_font_delta_changed.connect(self._refresh_overlay_font_styles)
        if hasattr(box, 'overlay_mode_changed'):
            box.overlay_mode_changed.connect(self._on_box_overlay_mode_changed)
        # 保存初始哈希，供后续自动翻译变化检测使用
        if worker is not None and worker.img_hash is not None:
            self._box_img_hashes[box.box_id] = worker.img_hash
        if self._box_mode in ('temp', 'ai'):
            box.set_mode('temp')
        else:
            box.set_mode('fixed')
            if self._translate_mode == 'auto':
                box._pending_auto = True
        if self._box_mode == 'ai':
            box.set_mode('temp')   # AI框选框 临时消失
            text = self._normalize_ocr_payload(payload)['text']
            if text.strip():
                box.set_ocr_text(text)
                box.start_dismiss_timer()
                self._on_explain_requested(text)
            else:
                self.result_bar.show_error('未识别到文字，请重新框选')
                box.start_dismiss_timer()
        else:
            self._on_ocr_done(payload, box)

    def _run_ocr(self, box):
        """用于固定框自动重翻：带画面变化检测，无变化则跳过"""
        from ocr.ocr_worker import OCRWorker
        prev_hash = self._box_img_hashes.get(box.box_id)
        worker = OCRWorker(box.region, prev_hash=prev_hash)
        worker.result_ready.connect(
            lambda payload, _, w=worker: self._on_auto_ocr_done(payload, box, w))
        worker.no_change.connect(lambda: self._cleanup_worker(worker))
        worker.error_occurred.connect(lambda e: self.result_bar.show_error(f'OCR: {e}'))
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _on_auto_ocr_done(self, payload, box, worker):
        """自动翻译 OCR 完成后：更新哈希，然后走正常 OCR 完成流程"""
        if worker.img_hash is not None:
            self._box_img_hashes[box.box_id] = worker.img_hash
        self._on_ocr_done(payload, box)

    def _on_ocr_done(self, payload, box):
        payload = self._normalize_ocr_payload(payload)
        text = payload['text']
        setattr(box, '_last_ocr_rows', payload['rows'])
        from core.overlay_layout import group_rows_into_paragraphs
        setattr(box, '_last_ocr_paragraphs', group_rows_into_paragraphs(payload['rows']))
        setattr(box, '_last_paragraph_translations', [])
        setattr(box, '_paragraph_translation_pending', False)
        setattr(box, '_pending_paragraph_translations', [])
        if text == '\x00LOW_CONTRAST':
            self.result_bar.show_error('所选区域无有效文字（图像近乎空白），请重新框选含文字的区域')
            box.start_dismiss_timer()
            return
        if not text.strip():
            self.result_bar.show_error('未识别到文字，请重新框选（调试图已保存至 ~/.screen_translator/last_capture.png）')
            box.start_dismiss_timer()
            return
        box.set_ocr_text(text)
        self.result_bar.show_loading('翻译中...')
        self._run_translate(text, box)

    def _run_translate(self, text: str, box):
        from ocr.ocr_worker import TranslationWorker
        target = self.settings.get('target_language', 'zh-CN')
        source = self.settings.get('source_language', 'auto')
        self._translation_job_seq += 1
        job_id = self._translation_job_seq
        worker = TranslationWorker(text, self.router, target_lang=target, source_lang=source)
        worker._translation_job_id = job_id
        self._active_translation_workers[job_id] = worker
        self.result_bar.set_stop_clear_busy(True)
        worker.result_ready.connect(lambda r, w=worker: self._on_translate_done(r, box, w))
        worker.error_occurred.connect(lambda msg, w=worker: self._on_translate_error(msg, w))
        worker.finished.connect(lambda w=worker: self._on_translate_finished(w))
        self._workers.append(worker)
        worker.start()

    def _run_paragraph_translate(self, box):
        from ocr.ocr_worker import TranslationWorker

        paragraphs = list(getattr(box, '_last_ocr_paragraphs', []) or [])
        if not paragraphs or getattr(box, '_paragraph_translation_pending', False) is True:
            return

        target = self.settings.get('target_language', 'zh-CN')
        source = self.settings.get('source_language', 'auto')
        setattr(box, '_paragraph_translation_pending', True)
        setattr(box, '_pending_paragraph_translations', [''] * len(paragraphs))
        self.result_bar.set_stop_clear_busy(True)

        for index, paragraph in enumerate(paragraphs):
            self._translation_job_seq += 1
            job_id = self._translation_job_seq
            worker = TranslationWorker(
                paragraph.get('text', ''),
                self.router,
                target_lang=target,
                source_lang=source,
            )
            worker._translation_job_id = job_id
            worker._paragraph_index = index
            worker._paragraph_box_id = getattr(box, 'box_id', None)
            worker._paragraph_box = box
            self._active_translation_workers[job_id] = worker
            worker.result_ready.connect(
                lambda result, idx=index, w=worker: self._on_single_paragraph_translation_done(result, box, idx, w)
            )
            worker.error_occurred.connect(
                lambda _msg, idx=index, w=worker: self._on_single_paragraph_translation_error(_msg, box, idx, w)
            )
            worker.finished.connect(lambda w=worker: self._on_translate_finished(w))
            self._workers.append(worker)
            worker.start()

    def _on_single_paragraph_translation_done(self, result: dict, box, index: int, worker=None):
        if self._is_translation_cancelled(worker):
            return
        translations = list(getattr(box, '_pending_paragraph_translations', []) or [])
        if not translations or index >= len(translations):
            return
        translations[index] = result.get('translated', '')
        setattr(box, '_pending_paragraph_translations', translations)
        if all(translations):
            setattr(box, '_paragraph_translation_pending', False)
            self._on_paragraph_translate_done(translations, box, worker=None)

    def _on_single_paragraph_translation_error(self, msg: str, box, index: int, worker=None):
        if self._is_translation_cancelled(worker):
            return
        setattr(box, '_paragraph_translation_pending', False)
        setattr(box, '_pending_paragraph_translations', [])
        setattr(box, '_last_paragraph_translations', [])
        self.result_bar.show_error(msg)

    def _on_box_overlay_mode_changed(self, box, mode: str):
        translated = getattr(box, '_last_translation', '')
        if not translated or mode == 'off':
            return
        if mode == 'over':
            paragraphs = getattr(box, '_last_ocr_paragraphs', [])
            translations = getattr(box, '_last_paragraph_translations', [])
            if paragraphs and not translations:
                self._run_paragraph_translate(box)
        box.show_subtitle(translated)

    def _on_paragraph_translate_done(self, translations, box, worker=None):
        if self._is_translation_cancelled(worker):
            return
        setattr(box, '_paragraph_translation_pending', False)
        setattr(box, '_pending_paragraph_translations', [])
        setattr(box, '_last_paragraph_translations', list(translations or []))
        if getattr(box, '_subtitle_mode', 'off') == 'over' and getattr(box, '_last_translation', ''):
            box.show_subtitle(box._last_translation)

    def _on_translate_error(self, msg: str, worker=None):
        if self._is_translation_cancelled(worker):
            return
        self.result_bar.show_error(msg)

    def _on_translate_finished(self, worker):
        job_id = getattr(worker, '_translation_job_id', None)
        if job_id is not None:
            self._active_translation_workers.pop(job_id, None)
            self._cancelled_translation_jobs.discard(job_id)
        paragraph_box = getattr(worker, '_paragraph_box', None)
        if paragraph_box is not None:
            still_running = any(
                getattr(active_worker, '_paragraph_box', None) is paragraph_box
                for active_worker in self._active_translation_workers.values()
            )
            if not still_running:
                setattr(paragraph_box, '_paragraph_translation_pending', False)
        self._cleanup_worker(worker)
        if not self._active_translation_workers:
            self.result_bar.set_stop_clear_busy(False)

    def _is_translation_cancelled(self, worker) -> bool:
        if worker is None:
            return False
        job_id = getattr(worker, '_translation_job_id', None)
        return bool(job_id in self._cancelled_translation_jobs or worker.isInterruptionRequested())

    def _on_stop_clear_requested(self):
        if self._active_translation_workers:
            for job_id, worker in list(self._active_translation_workers.items()):
                self._cancelled_translation_jobs.add(job_id)
                worker.requestInterruption()
            self.result_bar.clear_current_content()
            self.result_bar.set_stop_clear_busy(False)
            return
        self.result_bar.clear_current_content()

    def _on_box_removed(self, box_id: int):
        """框被关闭时清理相关状态，多框模式刷新显示"""
        self._multi_results.pop(box_id, None)
        self._box_img_hashes.pop(box_id, None)
        if self._box_mode == 'multi':
            self.result_bar.show_multi_results(list(self._multi_results.values()))

    def _on_translate_box(self, box):
        self._run_ocr(box)

    def _on_explain_requested(self, text: str):
        from ocr.ocr_worker import ExplainWorker
        ai = self.router.get_ai_backend()
        self.result_bar.show_explain_loading()
        worker = ExplainWorker(text, ai)
        worker.result_ready.connect(self.result_bar.show_explain)
        worker.error_occurred.connect(self.result_bar.show_explain)
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
            self._settings_win.settings_saved.connect(self.result_bar.refresh_opacity)
            self._settings_win.settings_saved.connect(self.result_bar.apply_settings)
            self._settings_win.settings_saved.connect(self._reload_hotkeys)
            self._settings_win.settings_saved.connect(self._refresh_overlay_font_styles)
            self._settings_win.show()
        else:
            self._settings_win.activateWindow()
            self._settings_win.raise_()

    def _on_overlay_requested(self, mode: str, text: str):
        boxes = list(self.box_manager._boxes.values())
        if not boxes:
            return
        for box in boxes:
            box.set_overlay_mode(mode)
            if mode == 'off':
                box.hide_subtitle()
                continue

            result = self._multi_results.get(box.box_id)
            translated = result.get('translated', '') if result else text
            if translated:
                box.show_subtitle(translated)

    def _refresh_overlay_font_styles(self, _value=None):
        boxes = getattr(self.box_manager, '_boxes', {}).values()
        for box in boxes:
            if hasattr(box, 'refresh_overlay_style'):
                box.refresh_overlay_style()

    def _trigger_explain(self):
        if self.result_bar._current_result:
            text = ''
            if hasattr(self.result_bar, 'current_source_text'):
                text = self.result_bar.current_source_text()
            if not text:
                text = self.result_bar._current_result.get('original', '')
            if text:
                self._on_explain_requested(text)

    def _on_retranslate_requested(self, text: str):
        text = str(text or '').strip()
        if not text:
            return
        self.result_bar.show_loading('翻译中...')
        self._run_translate(text, None)

    def _on_translate_done(self, result: dict, box, worker=None):
        if self._is_translation_cancelled(worker):
            return
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

        if box is not None and self._box_mode == 'multi':
            self._multi_results[box.box_id] = result
            self.result_bar.show_multi_results(list(self._multi_results.values()))
        else:
            self.result_bar.show_result(result)

        translated = result.get('translated', '')
        if box is not None:
            setattr(box, '_last_translation', translated)
            overlay_mode = getattr(box, '_subtitle_mode', 'off')
            if overlay_mode == 'over' and getattr(box, '_last_ocr_paragraphs', []) and not getattr(box, '_last_paragraph_translations', []):
                self._run_paragraph_translate(box)
            if translated and (getattr(box, '_subtitle_active', False) or overlay_mode != 'off'):
                box.show_subtitle(translated)

            if box.mode == 'temp':
                box.start_dismiss_timer()
            elif getattr(box, '_pending_auto', False):
                box._pending_auto = False
                box.start_auto_translate()
