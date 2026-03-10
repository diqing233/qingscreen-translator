import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

_app = QApplication.instance() or QApplication(sys.argv)

def _make_box():
    settings = MagicMock()
    settings.get.side_effect = lambda k, d=None: d
    from ui.translation_box import TranslationBox
    box = TranslationBox(QRect(100, 100, 200, 80), box_id=1, settings=settings)
    return box

def test_subtitle_win_initially_none():
    box = _make_box()
    assert box._subtitle_win is None
    assert box._subtitle_active is False

def test_show_subtitle_creates_win_and_shows():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    assert box._subtitle_win is not None
    assert box._subtitle_win.isVisible()
    assert box._subtitle_active is True

def test_hide_subtitle_hides_win():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    box.hide_subtitle()
    assert not box._subtitle_win.isVisible()
    assert box._subtitle_active is False

def test_subtitle_position_below_box():
    box = _make_box()
    box.show()
    box.show_subtitle("你好世界")
    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()
    assert sw.width() == box.width()

def test_subtitle_follows_box_on_move():
    box = _make_box()
    box.show()
    box.show_subtitle("移动测试")
    box.move(300, 200)
    sw = box._subtitle_win
    assert sw.x() == box.x()
    assert sw.y() == box.y() + box.height()

def test_toggle_subtitle():
    box = _make_box()
    box.show()
    box._last_translation = "测试译文"
    box._on_toggle_subtitle()
    assert box._subtitle_active is True
    box._on_toggle_subtitle()
    assert box._subtitle_active is False

def test_close_event_destroys_subtitle_win():
    box = _make_box()
    box.show()
    box.show_subtitle("关闭测试")
    assert box._subtitle_win is not None
    box.close()
    assert box._subtitle_win is None
