import unittest
import configparser

from sc_kill_feed_gui import StarCitizenKillFeedGUI
from lib.config_helpers import validate_and_apply_config


class ConfigValidationTests(unittest.TestCase):
    def test_validate_config_defaults_on_empty_user_section(self):
        g = object.__new__(StarCitizenKillFeedGUI)
        g.config = configparser.ConfigParser()
        # Ensure the 'user' section exists but is empty to mimic load_config behavior
        g.config["user"] = {}

        # Run validation via helper
        validate_and_apply_config(g.config, g)

        self.assertEqual(g.FILE_CHECK_INTERVAL, 0.1)
        self.assertEqual(g.MAX_LINES_PER_CHECK, 100)
        self.assertEqual(g.MAX_STATISTICS_ENTRIES, 1000)

    def test_validate_config_corrects_invalid_values(self):
        g = object.__new__(StarCitizenKillFeedGUI)
        g.config = configparser.ConfigParser()
        g.config["user"] = {
            "file_check_interval": "not-a-number",
            "max_lines_per_check": "-5",
            "max_statistics_entries": "9999999",
        }

        validate_and_apply_config(g.config, g)

        # Invalid values should be corrected to safe defaults
        self.assertEqual(g.FILE_CHECK_INTERVAL, 0.1)
        self.assertEqual(g.MAX_LINES_PER_CHECK, 100)
        self.assertEqual(g.MAX_STATISTICS_ENTRIES, 1000)


if __name__ == "__main__":
    unittest.main()
