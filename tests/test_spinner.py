import time
from src.agent.ui import Spinner


def test_spinner_initialization():
    spinner = Spinner("Testing", show_timer=True, auto_status=True)
    assert spinner.message == "Testing"
    assert spinner.show_timer is True
    assert spinner.auto_status is True
    assert spinner.diagnostic_tag == ""


def test_spinner_update_message_and_tag():
    spinner = Spinner("Initial", show_timer=True)
    spinner.update_message("Updated Message")
    assert spinner.message == "Updated Message"

    spinner.set_diagnostic_tag("[OpenRouter OK]")
    assert spinner.diagnostic_tag == "[OpenRouter OK]"


def test_spinner_start_and_stop():
    spinner = Spinner("Reflecting", show_timer=True, auto_status=True)
    spinner.start()
    assert spinner.thread is not None
    assert spinner.thread.is_alive()
    time.sleep(0.3)
    spinner.stop()
    assert spinner.stop_event.is_set()
    assert not spinner.thread.is_alive()
