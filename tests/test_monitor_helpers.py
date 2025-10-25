import threading
import time
import os

from lib import monitor_helpers


class FakeStatusVar:
    def __init__(self):
        self.value = None

    def set(self, v):
        self.value = v


class FakeGUI:
    def __init__(self, path):
        self.log_file_path = path
        self.READ_BUFFER_SIZE = 1
        self.MAX_LINES_PER_CHECK = 100
        self.FILE_CHECK_INTERVAL = 0.01
        self.is_monitoring = True
        self.processed = []
        self.status_var = FakeStatusVar()

    def process_kill_event(self, line):
        self.processed.append(line)

    def safe_after(self, delay, fn):
        # call immediately for tests
        fn()


def test_monitor_log_file_detects_death_event(tmp_path):
    log = tmp_path / "test.log"
    # start with an empty file
    log.write_text("")

    gui = FakeGUI(str(log))

    t = threading.Thread(target=monitor_helpers.monitor_log_file, args=(gui,))
    t.daemon = True
    t.start()

    # give thread a moment to open and seek to end
    time.sleep(0.05)

    # append a normal line and a kill event
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("Some other event\n")
        fh.write("<Actor Death> Player1 killed Player2\n")
        fh.flush()
        os.fsync(fh.fileno())

    # allow monitor to pick up the new lines
    time.sleep(0.1)

    # stop monitoring and join thread
    gui.is_monitoring = False
    t.join(timeout=2)

    # processed should contain the kill event (stripped)
    assert any("<Actor Death>" in s for s in gui.processed)


def test_monitor_log_file_handles_missing_file(tmp_path):
    # point to a non-existent file and ensure status_var gets set
    fake_path = str(tmp_path / "doesnotexist.log")
    gui = FakeGUI(fake_path)
    # ensure the file is missing
    if os.path.exists(fake_path):
        os.remove(fake_path)

    # should return/finish and set status_var via safe_after
    monitor_helpers.monitor_log_file(gui)
    assert gui.status_var.value is not None
