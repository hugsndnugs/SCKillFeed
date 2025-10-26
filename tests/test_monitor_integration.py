import os
import tempfile
import threading
import time
import unittest

from sc_kill_feed_gui import StarCitizenKillFeedGUI


class MonitorIntegrationTest(unittest.TestCase):
    def test_monitor_detects_appended_kill_line(self):
        # Create temporary file and write initial content
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tf:
            path = tf.name
            tf.write("Initial log line\n")
            tf.flush()

        try:
            # Create a minimal instance bypassing __init__ to avoid real Tk
            g = object.__new__(StarCitizenKillFeedGUI)

            # Minimal attributes required by monitor_log_file
            g.log_file_path = path
            g.FILE_CHECK_INTERVAL = 0.01
            g.MAX_LINES_PER_CHECK = 100
            g.READ_BUFFER_SIZE = 8192
            g.is_monitoring = True
            g.data_lock = __import__("threading").RLock()
            g.kills_data = []

            # Use centralized regex constant
            from constants import KILL_LINE_RE

            g.KILL_LINE_RE = KILL_LINE_RE

            # Replace process_kill_event to capture calls and signal
            processed = []
            evt = threading.Event()

            def fake_process(line):
                processed.append(line)
                evt.set()

            g.process_kill_event = fake_process

            # Start monitor in background thread
            t = threading.Thread(target=g.monitor_log_file, daemon=True)
            t.start()

            # Give monitor a moment to start and seek to end
            time.sleep(0.05)

            # Append a kill line to the file and flush
            kill_line = "<2025-10-10T00:38:41.559Z> [Notice] <Actor Death> CActor::Kill: 'Victim1' [111] in zone 'Z' killed by 'Killer1' [222] using 'weapon_x'"
            with open(path, "a", encoding="utf-8") as f:
                f.write(kill_line + "\n")
                f.flush()

            # Wait for the monitor to process the line
            got = evt.wait(timeout=2.0)

            # Stop monitoring
            g.is_monitoring = False
            t.join(timeout=1.0)

            self.assertTrue(got, "Monitor did not detect appended kill line in time")
            self.assertGreaterEqual(len(processed), 1)
            self.assertIn("<Actor Death>", processed[0])

        finally:
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
