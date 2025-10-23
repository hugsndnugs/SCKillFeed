import os
import tempfile
import threading
import time
import unittest

from sc_kill_feed_gui import StarCitizenKillFeedGUI


class MonitorRotationTest(unittest.TestCase):
    def test_truncate_and_detect_appended_kill_line(self):
        # Create temporary file and write initial content
        with tempfile.NamedTemporaryFile('w+', delete=False, encoding='utf-8') as tf:
            path = tf.name
            tf.write('Line A\nLine B\n')
            tf.flush()

        try:
            # Minimal instance bypassing __init__ to avoid Tk
            g = object.__new__(StarCitizenKillFeedGUI)
            g.log_file_path = path
            g.FILE_CHECK_INTERVAL = 0.01
            g.MAX_LINES_PER_CHECK = 100
            g.READ_BUFFER_SIZE = 8192
            g.is_monitoring = True
            g.data_lock = __import__('threading').RLock()
            g.kills_data = []

            # Use centralized regex constant
            from constants import KILL_LINE_RE
            g.KILL_LINE_RE = KILL_LINE_RE

            processed = []
            evt = threading.Event()

            def fake_process(line):
                processed.append(line)
                evt.set()

            g.process_kill_event = fake_process

            # Start monitor in background
            t = threading.Thread(target=g.monitor_log_file, daemon=True)
            t.start()

            # Allow monitor to initialize and seek to end
            time.sleep(0.05)

            # Truncate the file (simulate rotation/truncation)
            with open(path, 'w', encoding='utf-8') as f:
                f.write('')
                f.flush()

            # Wait a bit for the monitor to detect truncation
            time.sleep(0.05)

            # Append a kill line to the truncated file
            kill_line = "<2025-10-10T00:38:41.559Z> [Notice] <Actor Death> CActor::Kill: 'Victim2' [333] in zone 'Z' killed by 'Killer2' [444] using 'weapon_y'"
            with open(path, 'a', encoding='utf-8') as f:
                f.write(kill_line + '\n')
                f.flush()

            got = evt.wait(timeout=2.0)

            # Stop monitor
            g.is_monitoring = False
            t.join(timeout=1.0)

            self.assertTrue(got, "Monitor did not detect appended kill line after truncation")
            self.assertGreaterEqual(len(processed), 1)
            self.assertIn('<Actor Death>', processed[0])

        finally:
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
