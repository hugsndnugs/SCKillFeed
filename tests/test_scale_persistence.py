import unittest
import tempfile
import os
import configparser

from sc_kill_feed_gui import StarCitizenKillFeedGUI


class ScalePersistenceTests(unittest.TestCase):
    def test_validate_config_reads_gui_scale(self):
        g = object.__new__(StarCitizenKillFeedGUI)
        g.config = configparser.ConfigParser()
        g.config["user"] = {"gui_scale": "1.37"}

        # Should set gui_scale to float value without requiring full init
        g.validate_config()
        self.assertAlmostEqual(g.gui_scale, 1.37)

    def test_save_and_load_persists_gui_scale(self):
        # Create a temporary file for config
        fd, path = tempfile.mkstemp(suffix=".cfg")
        os.close(fd)
        try:
            g = object.__new__(StarCitizenKillFeedGUI)
            g.config = configparser.ConfigParser()
            g.config["user"] = {"gui_scale": "1.5"}
            g.config_path = path

            # Save the config
            g.save_config()

            # Create another instance and load
            h = object.__new__(StarCitizenKillFeedGUI)
            h.config = configparser.ConfigParser()
            h.config_path = path
            h.load_config()

            # Loaded config should contain gui_scale and validate_config should parse it
            h.validate_config()
            self.assertAlmostEqual(h.gui_scale, 1.5)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
