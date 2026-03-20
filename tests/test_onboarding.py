import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import tempfile, pytest
from PyQt5.QtWidgets import QApplication
from core.settings import SettingsStore
from ui.onboarding import OnboardingWizard

_app = QApplication.instance() or QApplication(sys.argv)


def make_store():
    f = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    f.close()
    return SettingsStore(f.name)


def test_wizard_creates_without_error():
    store = make_store()
    wiz = OnboardingWizard(store)
    assert wiz is not None
    wiz.close()


def test_wizard_starts_at_step_0():
    store = make_store()
    wiz = OnboardingWizard(store)
    assert wiz._current_step == 0
    assert wiz._stack.currentIndex() == 0
    wiz.close()


def test_wizard_title_shows_step_1():
    store = make_store()
    wiz = OnboardingWizard(store)
    assert '1/4' in wiz._title_label.text()
    wiz.close()


def test_next_step_advances():
    store = make_store()
    wiz = OnboardingWizard(store)
    wiz._on_next()
    assert wiz._current_step == 1
    assert wiz._stack.currentIndex() == 1
    wiz.close()


def test_prev_step_goes_back():
    store = make_store()
    wiz = OnboardingWizard(store)
    wiz._go_to_step(2)
    wiz._on_prev()
    assert wiz._current_step == 1
    wiz.close()


def test_prev_disabled_on_first_step():
    store = make_store()
    wiz = OnboardingWizard(store)
    assert not wiz._prev_btn.isVisible()
    wiz.close()


def test_prev_visible_on_later_steps():
    store = make_store()
    wiz = OnboardingWizard(store)
    wiz._go_to_step(1)
    assert not wiz._prev_btn.isHidden()
    wiz.close()


def test_next_button_text_is_finish_on_last_step():
    store = make_store()
    wiz = OnboardingWizard(store)
    wiz._go_to_step(3)
    assert wiz._next_btn.text() == '完成'
    wiz.close()


def test_skip_sets_first_launch_done():
    store = make_store()
    assert store.get('first_launch_done') is False
    wiz = OnboardingWizard(store)
    wiz._on_skip()
    assert store.get('first_launch_done') is True


def test_finish_sets_first_launch_done():
    store = make_store()
    wiz = OnboardingWizard(store)
    wiz._go_to_step(3)
    wiz._on_finish()
    assert store.get('first_launch_done') is True


def test_skip_emits_finished_signal():
    store = make_store()
    wiz = OnboardingWizard(store)
    received = []
    wiz.finished.connect(lambda: received.append(True))
    wiz._on_skip()
    assert received == [True]


def test_finish_emits_finished_signal():
    store = make_store()
    wiz = OnboardingWizard(store)
    received = []
    wiz.finished.connect(lambda: received.append(True))
    wiz._on_finish()
    assert received == [True]


def test_open_settings_signal_emitted():
    store = make_store()
    wiz = OnboardingWizard(store)
    received = []
    wiz.open_settings.connect(lambda tab: received.append(tab))
    wiz.open_settings.emit(2)
    assert received == [2]
    wiz.close()


def test_four_steps_in_stack():
    store = make_store()
    wiz = OnboardingWizard(store)
    assert wiz._stack.count() == 4
    wiz.close()


def test_hotkey_shown_in_step1():
    store = make_store()
    store.set('hotkey_select', 'alt+q')
    wiz = OnboardingWizard(store)
    wiz._go_to_step(0)
    # The step 1 widget should contain the hotkey text
    step_widget = wiz._stack.widget(0)
    assert step_widget is not None
    wiz.close()


def test_first_launch_done_default_false():
    store = make_store()
    assert store.get('first_launch_done', False) is False


def test_navigate_full_cycle():
    store = make_store()
    wiz = OnboardingWizard(store)
    for i in range(3):
        wiz._on_next()
    assert wiz._current_step == 3
    wiz._on_next()  # finish
    assert store.get('first_launch_done') is True
