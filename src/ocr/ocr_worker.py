import logging
import os
import mss
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QRect

logger = logging.getLogger(__name__)

_DEBUG_DIR = os.path.expanduser('~/.screen_translator')

# ── RapidOCR 单例（由 ocr.engine 管理，在 main.py 中预热）─────────────────────
def prewarm_ocr():
    """Compatibility shim – real pre-warming is done by ocr.engine.prewarm()."""
    from ocr.engine import prewarm
    prewarm()


def _get_dpr() -> float:
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            return screen.devicePixelRatio() if screen else 1.0
    except Exception:
        pass
    return 1.0


# ── OCR Worker ────────────────────────────────────────────────────────────────

class OCRWorker(QThread):
    result_ready  = pyqtSignal(str, object)
    no_change     = pyqtSignal()   # 画面与上次一致，跳过 OCR
    error_occurred = pyqtSignal(str)

    def __init__(self, region: QRect, prev_hash: float = None, parent=None):
        super().__init__(parent)
        self.region    = region
        self.prev_hash = prev_hash   # 上次截图哈希，None 表示首次
        self.img_hash: float = None  # 本次截图哈希（由 run() 填入）

    def run(self):
        try:
            img = self._capture()
            if img is None:
                self.error_occurred.emit('截图失败')
                return

            # 计算本次截图哈希
            self.img_hash = self._compute_hash(img)

            # 若有上次哈希，差值小于阈值则认为画面未变化，跳过 OCR
            if self.prev_hash is not None:
                diff = abs(self.img_hash - self.prev_hash)
                if diff < 3.0:
                    logger.debug(f'画面无变化 (diff={diff:.2f})，跳过 OCR')
                    self.no_change.emit()
                    return

            h, w = img.shape[:2]
            mean_val = float(img.mean())
            logger.info(f'截图: {self.region.x()},{self.region.y()} '
                        f'{self.region.width()}x{self.region.height()} → '
                        f'图像 {w}x{h}, 均值={mean_val:.1f}')
            self._save_debug(img, 'last_capture.png')

            text = self._ocr_pipeline(img, mean_val)

            logger.info(f'OCR 结果: {repr(text[:120]) if text else "(空)"}')
            if not text:
                bright_pct = float((img > 80).mean()) * 100
                std_val = float(img.std())
                logger.warning(
                    f'OCR 未识别到文字 — 亮像素={bright_pct:.1f}%，std={std_val:.1f}'
                )
                if bright_pct < 2.0 and std_val < 20:
                    text = '\x00LOW_CONTRAST'
            self.result_ready.emit(text, self.region)

        except Exception as e:
            logger.exception('OCR failed')
            self.error_occurred.emit(str(e))

    # ── 截图 ─────────────────────────────────────────────────────────────────

    def _compute_hash(self, img) -> float:
        """快速图像哈希：4 倍降采样后求均值，用于检测画面变化。"""
        try:
            return float(img[::4, ::4].mean())
        except Exception:
            return 0.0

    def _capture(self):
        r = self.region
        dpr = _get_dpr()
        left   = int(r.x() * dpr)
        top    = int(r.y() * dpr)
        width  = max(int(r.width() * dpr), 20)
        height = max(int(r.height() * dpr), 20)
        logger.debug(f'DPR={dpr:.2f}, 物理截图: {left},{top} {width}x{height}')
        try:
            with mss.mss() as sct:
                shot = sct.grab({'left': left, 'top': top,
                                 'width': width, 'height': height})
                img = np.array(shot)
                return img[:, :, :3]   # BGRA → BGR
        except Exception as e:
            logger.error(f'mss capture failed: {e}')
            return None

    # ── OCR 主流水线 ──────────────────────────────────────────────────────────

    def _ocr_pipeline(self, img_bgr, mean_val: float) -> str:
        """
        策略（向 QQ 截图翻译对齐）:
        1. 预处理图（自适应放大 + 对比度增强 + 锐化）
        2. 若均值 < 128（暗底亮字），同时尝试反色预处理图
        3. 回退：原图直接跑（无预处理）
        """
        is_dark = mean_val < 128

        # 策略1：预处理图
        proc = self._preprocess(img_bgr, is_dark)
        self._save_debug(proc, 'last_capture_proc.png')
        text = self._run_rapidocr(proc)
        if text:
            return text

        # 策略2：若暗背景，反色后再试（暗底亮字 → 亮底暗字，RapidOCR 更准）
        if is_dark:
            logger.info(f'均值={mean_val:.0f}（暗背景），尝试反色')
            inv = self._invert(proc)
            self._save_debug(inv, 'last_capture_inv.png')
            text = self._run_rapidocr(inv)
            if text:
                return text

        # 策略3：回退到原图（不做放大，有时模型反而更准）
        text = self._run_rapidocr(img_bgr)
        if text:
            return text

        return ''

    # ── 图像预处理 ────────────────────────────────────────────────────────────

    def _preprocess(self, img_bgr, is_dark: bool = False):
        """
        自适应放大 + 对比度增强 + 锐化。
        目标：让最短边 >= 64px，文字清晰可辨。
        """
        try:
            from PIL import Image, ImageOps, ImageEnhance, ImageFilter
            h, w = img_bgr.shape[:2]

            # 计算放大倍数（最短边目标 ≥ 64px，小图最多放大 4x）
            min_dim = min(h, w)
            if min_dim < 32:
                scale = 4
            elif min_dim < 64:
                scale = 4
            elif min_dim < 128:
                scale = 3
            elif min_dim < 256:
                scale = 2
            else:
                scale = 1

            rgb = img_bgr[:, :, ::-1]
            pil = Image.fromarray(rgb.astype('uint8'))

            if scale > 1:
                pil = pil.resize((w * scale, h * scale), Image.LANCZOS)
                logger.debug(f'图像放大 {scale}x → {w*scale}x{h*scale}')

            # 自动对比度拉伸（去除噪点，裁剪最亮/最暗 1%）
            pil = ImageOps.autocontrast(pil, cutoff=1)

            # 锐化
            pil = ImageEnhance.Sharpness(pil).enhance(2.0)

            return np.array(pil)[:, :, ::-1]   # RGB → BGR
        except Exception as e:
            logger.debug(f'Preprocess failed: {e}')
            return img_bgr

    def _invert(self, img_bgr):
        try:
            from PIL import Image, ImageOps
            pil = Image.fromarray(img_bgr[:, :, ::-1].astype('uint8'))
            inv = ImageOps.invert(pil)
            return np.array(inv)[:, :, ::-1]
        except Exception:
            return 255 - img_bgr

    def _save_debug(self, img_bgr, filename: str):
        try:
            from PIL import Image
            Image.fromarray(img_bgr[:, :, ::-1].astype('uint8')).save(
                os.path.join(_DEBUG_DIR, filename))
        except Exception as e:
            logger.debug(f'Debug save failed: {e}')

    # ── OCR 引擎 ──────────────────────────────────────────────────────────────

    def _run_rapidocr(self, img) -> str:
        """Use the pre-warmed singleton RapidOCR engine."""
        from ocr.engine import get_engine
        engine = get_engine()
        if engine is None:
            logger.warning('RapidOCR 引擎未就绪（ocr.engine.prewarm() 需在 Qt 初始化前调用）')
            return ''
        try:
            result, elapse = engine(img)
            rows = len(result) if result else 0
            if elapse is not None:
                total_ms = (sum(elapse) if isinstance(elapse, list) else elapse) * 1000
                logger.info(f'RapidOCR: {total_ms:.0f}ms, rows={rows}')
            else:
                logger.info(f'RapidOCR: rows={rows}')
            if result:
                lines = [line[1] for line in result
                         if line and len(line) > 1 and isinstance(line[1], str)]
                return ' '.join(lines).strip()
        except Exception as e:
            logger.warning(f'RapidOCR inference failed: {e}')
        return ''


# ── 翻译 Worker ───────────────────────────────────────────────────────────────

class TranslationWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, router, target_lang: str = 'zh-CN',
                 source_lang: str = 'auto', parent=None):
        super().__init__(parent)
        self.text = text
        self.router = router
        self.target_lang = target_lang
        self.source_lang = source_lang

    def run(self):
        try:
            result = self.router.translate(
                self.text, target_lang=self.target_lang, source_lang=self.source_lang)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit('所有翻译后端均失败或未启用')
        except Exception as e:
            logger.exception('Translation failed')
            self.error_occurred.emit(str(e))


# ── AI 解释 Worker ────────────────────────────────────────────────────────────

class ExplainWorker(QThread):
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, ai_backend, parent=None):
        super().__init__(parent)
        self.text = text
        self.ai_backend = ai_backend

    def run(self):
        try:
            if self.ai_backend is None:
                self.error_occurred.emit('请先在设置中配置AI后端（DeepSeek/OpenAI/Claude）')
                return
            result = self.ai_backend.explain(self.text)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit('AI解释失败，请检查API密钥')
        except Exception as e:
            logger.exception('Explain failed')
            self.error_occurred.emit(str(e))
