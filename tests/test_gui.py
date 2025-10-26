import os
import tempfile
import unittest
import json
from datetime import datetime

from sc_kill_feed_gui import StarCitizenKillFeedGUI


class _Stub:
    def __init__(self):
        self.last_text = ""

    def config(self, **kwargs):
        # Capture config updates like label text
        self.last_text = kwargs.get("text", self.last_text)


class _FakeRoot:
    def after(self, delay, func):
        # Immediately execute callbacks for tests
        func()


class _FakeText:
    def __init__(self):
        self.content = ""

    def insert(self, where, text, tags=None):
        self.content += text

    def see(self, where):
        pass

    def tag_configure(self, *args, **kwargs):
        pass

    def delete(self, a, b):
        self.content = ""


class _FakeTree:
    def __init__(self):
        self.items = []

    def delete(self, *args):
        self.items.clear()

    def insert(self, parent, idx, text=None, values=None, **kwargs):
        self.items.append((text or values, values))

    def get_children(self):
        return list(range(len(self.items)))


def make_stub_gui(player_name="Player1"):
    # Create an instance without calling __init__ to avoid tkinter creation
    g = object.__new__(StarCitizenKillFeedGUI)
    # Minimal attributes required by methods under test
    g.player_name = player_name
    g.kills_data = []
    g.data_lock = __import__("threading").RLock()  # Add missing data_lock attribute
    g.stats = {
        "total_kills": 0,
        "total_deaths": 0,
        "kill_streak": 0,
        "death_streak": 0,
        "max_kill_streak": 0,
        "max_death_streak": 0,
        "weapons_used": __import__("collections").Counter(),
        "weapons_against": __import__("collections").Counter(),
        "victims": __import__("collections").Counter(),
        "killers": __import__("collections").Counter(),
    }
    # Use centralized regex from constants
    from constants import KILL_LINE_RE

    g.KILL_LINE_RE = KILL_LINE_RE

    g.root = _FakeRoot()
    g.kill_feed_text = _FakeText()
    g.kills_label = _Stub()
    g.deaths_label = _Stub()
    g.kd_ratio_label = _Stub()
    g.streak_label = _Stub()
    g.weapons_tree = _FakeTree()
    g.recent_tree = _FakeTree()
    g.status_var = type("SV", (), {"set": lambda self, v: None})()
    return g


class GUITest(unittest.TestCase):
    def test_process_kill_event_parses_and_updates(self):
        g = make_stub_gui(player_name="Ponder_OG")
        # Sample line similar to test_parse
        line = "<2025-10-10T00:38:41.559Z> [Notice] <Actor Death> CActor::Kill: 'Vagabondy' [202153878531] in zone 'Hangar_SmallFront_GrimHEX_6589113285541' killed by 'Ponder_OG' [200146291288] using 'volt_smg_energy_01_black01_6589113021365' [Class volt_smg_energy_01_black01]"
        # Call the processor
        g.process_kill_event(line)

        # One kill recorded
        self.assertEqual(len(g.kills_data), 1)
        kd = g.kills_data[0]
        self.assertEqual(kd["victim"], "Vagabondy")
        self.assertEqual(kd["killer"], "Ponder_OG")
        self.assertEqual(kd["weapon"], "volt_smg_energy_01_black01_6589113021365")

        # Stats updated: player was killer -> total_kills = 1
        self.assertEqual(g.stats["total_kills"], 1)
        self.assertEqual(g.stats["kill_streak"], 1)

    def test_update_statistics_counts_death_and_suicide(self):
        g = make_stub_gui(player_name="PlayerX")

        # Player killed someone
        kd1 = {"victim": "Other", "killer": "PlayerX", "weapon": "gun"}
        g.update_statistics(kd1)
        self.assertEqual(g.stats["total_kills"], 1)

        # Player died
        kd2 = {"victim": "PlayerX", "killer": "Enemy", "weapon": "gun2"}
        g.update_statistics(kd2)
        self.assertEqual(g.stats["total_deaths"], 1)

        # Suicide by player
        kd3 = {"victim": "PlayerX", "killer": "PlayerX", "weapon": "boom"}
        g.update_statistics(kd3)
        self.assertEqual(g.stats["total_deaths"], 2)

    def test_export_csv_and_json(self):
        g = make_stub_gui(player_name="PlayerY")
        now = datetime.now()
        g.kills_data = [
            {"timestamp": now, "victim": "A", "killer": "B", "weapon": "w1"},
            {"timestamp": now, "victim": "C", "killer": "PlayerY", "weapon": "w2"},
        ]
        g.stats["total_kills"] = 1
        g.stats["total_deaths"] = 0

        with tempfile.TemporaryDirectory() as td:
            csv_path = os.path.join(td, "out.csv")
            json_path = os.path.join(td, "out.json")

            g.export_csv(csv_path)
            self.assertTrue(os.path.isfile(csv_path))
            with open(csv_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("killer", content)
                self.assertIn("PlayerY", content)

            g.export_json(json_path)
            self.assertTrue(os.path.isfile(json_path))
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertIn("kill_events", data)
                self.assertEqual(data["statistics"]["total_kills"], 1)


if __name__ == "__main__":
    unittest.main()
