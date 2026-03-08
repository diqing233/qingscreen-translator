import logging
from typing import Dict
from PyQt5.QtCore import QRect, QObject, pyqtSignal

logger = logging.getLogger(__name__)


class BoxManager(QObject):
    translate_box = pyqtSignal(object)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._boxes: Dict[int, object] = {}
        self._next_id = 1

    def create_box(self, rect: QRect):
        from ui.translation_box import TranslationBox
        box = TranslationBox(rect, self._next_id, self.settings)
        self._boxes[self._next_id] = box
        self._next_id += 1
        box.translate_requested.connect(self.translate_box.emit)
        box.close_requested.connect(self._remove_box)
        box.show()
        return box

    def _remove_box(self, box):
        bid = box.box_id
        if bid in self._boxes:
            self._boxes[bid].hide()
            self._boxes[bid].deleteLater()
            del self._boxes[bid]
            logger.debug(f'Box {bid} removed')

    def hide_all(self):
        for b in self._boxes.values():
            b.hide()

    def show_all(self):
        for b in self._boxes.values():
            b.show()

    def clear_all(self):
        for box in list(self._boxes.values()):
            self._remove_box(box)

    def toggle_all_visibility(self):
        """切换所有框的显示/隐藏状态（用于快捷键）"""
        if not self._boxes:
            return
        # 若有任意框可见则全部隐藏，否则全部显示
        any_visible = any(b.isVisible() for b in self._boxes.values())
        if any_visible:
            for b in self._boxes.values():
                b.hide()
        else:
            for b in self._boxes.values():
                b.show()
