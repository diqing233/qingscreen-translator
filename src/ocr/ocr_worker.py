import logging
import mss
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QRect

logger = logging.getLogger(__name__)

class OCRWorker(QThread):
    result_ready = pyqtSignal(str, object)
    error_occurred = pyqtSignal(str)

    def __init__(self, region: QRect, parent=None):
        super().__init__(parent)
        self.region = region

    def run(self):
        try:
            img = self._capture()
            if img is None:
                self.error_occurred.emit('截图失败')
                return
            text = self._extract_text(img)
            self.result_ready.emit(text, self.region)
        except Exception as e:
            logger.exception('OCR failed')
            self.error_occurred.emit(str(e))

    def _capture(self):
        r = self.region
        with mss.mss() as sct:
            monitor = {
                'left': r.x(), 'top': r.y(),
                'width': max(r.width(), 10), 'height': max(r.height(), 10)
            }
            screenshot = sct.grab(monitor)
            img = np.array(screenshot)
            return img[:, :, :3]

    def _extract_text(self, img) -> str:
        # 方案1: RapidOCR（推荐，轻量，支持中英文）
        try:
            from rapidocr_onnxruntime import RapidOCR
            engine = RapidOCR()
            result, _ = engine(img)
            if result:
                return ' '.join([line[1] for line in result if line and len(line) > 1]).strip()
            return ''
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f'RapidOCR failed: {e}')

        # 方案2: EasyOCR
        try:
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
            result = reader.readtext(img)
            if result:
                return ' '.join([r[1] for r in result]).strip()
            return ''
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f'EasyOCR failed: {e}')

        # 方案3: PaddleOCR（Python <= 3.12）
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            results = ocr.ocr(img, cls=True)
            if not results or not results[0]:
                return ''
            lines = []
            for line in results[0]:
                if line and len(line) >= 2:
                    text_info = line[1]
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 1:
                        lines.append(str(text_info[0]))
            return ' '.join(lines).strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f'PaddleOCR failed: {e}')

        # 方案4: pytesseract（需系统安装 Tesseract）
        try:
            from PIL import Image
            import pytesseract
            pil_img = Image.fromarray(img)
            return pytesseract.image_to_string(pil_img, lang='chi_sim+eng').strip()
        except Exception as e:
            logger.warning(f'pytesseract failed: {e}')

        return ''


class TranslationWorker(QThread):
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, text: str, router, target_lang: str = 'zh-CN', parent=None):
        super().__init__(parent)
        self.text = text
        self.router = router
        self.target_lang = target_lang

    def run(self):
        try:
            result = self.router.translate(self.text, target_lang=self.target_lang)
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit('所有翻译后端均失败或未启用')
        except Exception as e:
            logger.exception('Translation failed')
            self.error_occurred.emit(str(e))


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
