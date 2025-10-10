import os
import tempfile
import unittest

from sc_kill_feed import create_csv_writer


class CSVWriteTest(unittest.TestCase):
    def test_create_csv_in_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            writer, f, path, enabled = create_csv_writer(tmpdir)
            self.assertTrue(enabled)
            self.assertIsNotNone(writer)
            self.assertTrue(os.path.isfile(path))
            # Clean up
            try:
                f.close()
            except Exception:
                pass

    def test_fallback_to_home_when_unwritable(self):
        # On most OSes we can't reliably create an unwritable dir, but we can simulate by
        # passing a path that doesn't exist and that we can't create. Use a path under
        # the root that is almost certainly not writable, such as C:\Windows\System32\nonexistent_dir\
        # For cross-platform, we'll create a directory and remove write perms if possible.
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory and remove write permissions if platform supports it
            no_write_dir = os.path.join(tmpdir, 'nowrite')
            os.mkdir(no_write_dir)
            try:
                # Try to remove write permissions
                os.chmod(no_write_dir, 0o400)
            except Exception:
                # If chmod fails (e.g., on Windows), skip permission modification but still run test
                pass

            writer, f, path, enabled = create_csv_writer(no_write_dir)
            # We expect enabled to be True in most environments because fallback to home will succeed
            self.assertTrue(enabled)
            self.assertIsNotNone(writer)
            try:
                f.close()
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
