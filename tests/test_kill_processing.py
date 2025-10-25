import threading
import configparser
from collections import Counter, deque
from lib.kill_processing import process_kill_event
from constants import KILL_LINE_RE


class MockGUI:
    def __init__(self):
        self.KILL_LINE_RE = KILL_LINE_RE
        self.data_lock = threading.RLock()
        self.kills_data = deque()
        self.stats = {
            "total_kills": 0,
            "total_deaths": 0,
            "kill_streak": 0,
            "death_streak": 0,
            "max_kill_streak": 0,
            "max_death_streak": 0,
            "weapons_used": Counter(),
            "weapons_against": Counter(),
            "victims": Counter(),
            "killers": Counter(),
        }
        self.player_name = "Player1"
        self.config = configparser.ConfigParser()
        self.config["user"] = {"auto_log_enabled": "false"}
        self.safe_after = lambda *args, **kwargs: None
        self.safe_after_idle = lambda f: f()
        self.debounced_update_statistics = lambda: None
        self._append_kill_to_csv = lambda kd: None
        self.displayed = []

    def update_statistics(self, kill_data):
        victim = kill_data["victim"]
        killer = kill_data["killer"]
        weapon = kill_data["weapon"]

        self.stats["weapons_used"][weapon] += 1
        self.stats["weapons_against"][weapon] += 1
        self.stats["victims"][victim] += 1
        self.stats["killers"][killer] += 1

        if killer == victim:
            return
        if killer == self.player_name:
            self.stats["total_kills"] += 1
        elif victim == self.player_name:
            self.stats["total_deaths"] += 1

    def display_kill_event(self, kd):
        self.displayed.append(kd)


def test_process_kill_event_appends_and_updates_stats():
    gui = MockGUI()
    # Construct a line matching the KILL_LINE_RE used by the app
    line = (
        "<Actor Death> CActor::Kill: 'Enemy1' [0x123] in zone 'Area51' "
        "killed by 'Player1' [0x456] using 'Laser'"
    )

    process_kill_event(gui, line)

    assert len(gui.kills_data) == 1
    kill = gui.kills_data[0]
    assert kill["killer"] == "Player1"
    assert kill["victim"] == "Enemy1"
    assert kill["weapon"] == "Laser"
    assert gui.stats["weapons_used"]["Laser"] == 1
    assert gui.displayed, "display_kill_event should have been called"
