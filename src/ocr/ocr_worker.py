import logging
import os

import mss
import numpy as np
from PyQt5.QtCore import QThread, QRect, pyqtSignal

logger = logging.getLogger(__name__)

_DEBUG_DIR = os.path.expanduser("~/.screen_translator")


def prewarm_ocr():
    """Compatibility shim; the real prewarm happens in ocr.engine."""
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


class OCRWorker(QThread):
    result_ready = pyqtSignal(object, object)
    no_change = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, region: QRect, prev_hash: float = None, parent=None):
        super().__init__(parent)
        self.region = region
        self.prev_hash = prev_hash
        self.img_hash: float = None

    def run(self):
        try:
            img = self._capture()
            if img is None:
                self.error_occurred.emit("截图失败")
                return

            self.img_hash = self._compute_hash(img)
            if self.prev_hash is not None:
                diff = abs(self.img_hash - self.prev_hash)
                if diff < 3.0:
                    logger.debug(f"screen unchanged (diff={diff:.2f}), skipping OCR")
                    self.no_change.emit()
                    return

            h, w = img.shape[:2]
            mean_val = float(img.mean())
            logger.info(
                "capture: %s,%s %sx%s -> %sx%s mean=%.1f",
                self.region.x(),
                self.region.y(),
                self.region.width(),
                self.region.height(),
                w,
                h,
                mean_val,
            )
            self._save_debug(img, "last_capture.png")

            payload = self._ocr_pipeline(img, mean_val)
            text = payload.get("text", "")

            logger.info("OCR result: %r", text[:120] if text else "(empty)")
            if not text:
                bright_pct = float((img > 80).mean()) * 100
                std_val = float(img.std())
                logger.warning(
                    "OCR returned no text; bright pixels %.1f%%, std %.1f",
                    bright_pct,
                    std_val,
                )
                if bright_pct < 2.0 and std_val < 20:
                    payload["text"] = "\x00LOW_CONTRAST"

            self.result_ready.emit(payload, self.region)
        except Exception as exc:
            logger.exception("OCR failed")
            self.error_occurred.emit(str(exc))

    def _compute_hash(self, img) -> float:
        try:
            return float(img[::4, ::4].mean())
        except Exception:
            return 0.0

    def _capture(self):
        r = self.region
        dpr = _get_dpr()
        left = int(r.x() * dpr)
        top = int(r.y() * dpr)
        width = max(int(r.width() * dpr), 20)
        height = max(int(r.height() * dpr), 20)
        logger.debug("DPR=%.2f capture=%s,%s %sx%s", dpr, left, top, width, height)
        try:
            with mss.mss() as sct:
                shot = sct.grab(
                    {
                        "left": left,
                        "top": top,
                        "width": width,
                        "height": height,
                    }
                )
                img = np.array(shot)
                return img[:, :, :3]
        except Exception as exc:
            logger.error("mss capture failed: %s", exc)
            return None

    def _ocr_pipeline(self, img_bgr, mean_val: float) -> dict:
        is_dark = mean_val < 128

        processed, scale = self._preprocess(img_bgr, is_dark)
        self._save_debug(processed, "last_capture_proc.png")
        payload = self._run_rapidocr(processed, scale=scale)
        if payload.get("text"):
            return payload

        if is_dark:
            logger.info("dark background detected (mean %.0f), trying inverted image", mean_val)
            inverted = self._invert(processed)
            self._save_debug(inverted, "last_capture_inv.png")
            payload = self._run_rapidocr(inverted, scale=scale)
            if payload.get("text"):
                return payload

        payload = self._run_rapidocr(img_bgr, scale=1)
        if payload.get("text"):
            return payload

        return {"text": "", "rows": []}

    def _preprocess(self, img_bgr, is_dark: bool = False):
        """Return the processed image plus the scale factor used for OCR."""
        try:
            from PIL import Image, ImageEnhance, ImageOps

            h, w = img_bgr.shape[:2]
            min_dim = min(h, w)
            if min_dim < 64:
                scale = 4
            elif min_dim < 128:
                scale = 3
            elif min_dim < 256:
                scale = 2
            else:
                scale = 1

            rgb = img_bgr[:, :, ::-1]
            pil = Image.fromarray(rgb.astype("uint8"))

            if scale > 1:
                pil = pil.resize((w * scale, h * scale), Image.LANCZOS)
                logger.debug("image upscaled %sx to %sx%s", scale, w * scale, h * scale)

            pil = ImageOps.autocontrast(pil, cutoff=1)
            pil = ImageEnhance.Sharpness(pil).enhance(2.0)

            return np.array(pil)[:, :, ::-1], scale
        except Exception as exc:
            logger.debug("Preprocess failed: %s", exc)
            return img_bgr, 1

    def _invert(self, img_bgr):
        try:
            from PIL import Image, ImageOps

            pil = Image.fromarray(img_bgr[:, :, ::-1].astype("uint8"))
            inv = ImageOps.invert(pil)
            return np.array(inv)[:, :, ::-1]
        except Exception:
            return 255 - img_bgr

    def _save_debug(self, img_bgr, filename: str):
        try:
            from PIL import Image

            Image.fromarray(img_bgr[:, :, ::-1].astype("uint8")).save(
                os.path.join(_DEBUG_DIR, filename)
            )
        except Exception as exc:
            logger.debug("Debug save failed: %s", exc)

    def _run_rapidocr(self, img, scale: float = 1) -> dict:
        from ocr.engine import get_engine

        engine = get_engine()
        if engine is None:
            logger.warning("RapidOCR engine is not ready")
            return {"text": "", "rows": []}

        try:
            result, elapse = engine(img)
            row_count = len(result) if result else 0
            if elapse is not None:
                total_ms = (sum(elapse) if isinstance(elapse, list) else elapse) * 1000
                logger.info("RapidOCR: %.0fms rows=%s", total_ms, row_count)
            else:
                logger.info("RapidOCR: rows=%s", row_count)

            if not result:
                return {"text": "", "rows": []}

            lines = []
            normalized_rows = []
            for line in result:
                if not line or len(line) < 2 or not isinstance(line[1], str):
                    continue
                text = line[1].strip()
                if not text:
                    continue
                box = line[0] if isinstance(line[0], list) else []
                if scale and scale != 1:
                    box = [
                        [int(round(point[0] / scale)), int(round(point[1] / scale))]
                        for point in box
                    ]
                normalized_rows.append({"text": text, "box": box})
                lines.append(text)

            return {
                "text": " ".join(lines).strip(),
                "rows": normalized_rows,
            }
        except Exception as exc:
            logger.warning("RapidOCR inference failed: %s", exc)
            return {"text": "", "rows": []}


class TranslationWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        text: str,
        router,
        target_lang: str = "zh-CN",
        source_lang: str = "auto",
        parent=None,
    ):
        super().__init__(parent)
        self.text = text
        self.router = router
        self.target_lang = target_lang
        self.source_lang = source_lang

    def run(self):
        try:
            if self.isInterruptionRequested():
                return
            result = self.router.translate(
                self.text,
                target_lang=self.target_lang,
                source_lang=self.source_lang,
            )
            if self.isInterruptionRequested():
                return
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit("所有翻译后端均失败或未启用")
        except Exception as exc:
            if self.isInterruptionRequested():
                return
            logger.exception("Translation failed")
            self.error_occurred.emit(str(exc))


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
                self.error_occurred.emit(
                    "请先在设置中配置 AI 后端（DeepSeek/OpenAI/Claude）"
                )
                return
            result = self.ai_backend.explain(self.text)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit("AI 解释失败，请检查 API 密钥")
        except Exception as exc:
            logger.exception("Explain failed")
            self.error_occurred.emit(str(exc))
