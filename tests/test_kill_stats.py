import threading
from collections import Counter, deque
from lib.kill_stats import update_statistics, limit_statistics_size


class MockGUI:
    def __init__(self):
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
        self.data_lock = threading.RLock()
        self.MAX_STATISTICS_ENTRIES = 5


def test_update_statistics_player_kill_and_death():
    gui = MockGUI()
    # Player1 kills Enemy1
    kill = {"victim": "Enemy1", "killer": "Player1", "weapon": "Laser"}
    update_statistics(gui, kill)
    assert gui.stats["total_kills"] == 1
    assert gui.stats["kill_streak"] == 1
    assert gui.stats["weapons_used"]["Laser"] == 1

    # Enemy2 kills Player1
    kill2 = {"victim": "Player1", "killer": "Enemy2", "weapon": "Pistol"}
    update_statistics(gui, kill2)
    assert gui.stats["total_deaths"] == 1
    assert gui.stats["death_streak"] == 1
    assert gui.stats["kill_streak"] == 0


def test_update_statistics_suicide():
    gui = MockGUI()
    kill = {"victim": "Player1", "killer": "Player1", "weapon": "Grenade"}
    update_statistics(gui, kill)
    assert gui.stats["total_deaths"] == 1
    assert gui.stats["death_streak"] == 1
    # Suicides should not increment total_kills
    assert gui.stats["total_kills"] == 0


def test_limit_statistics_size_trims_counters():
    gui = MockGUI()
    # populate the weapons_used counter with more than MAX_STATISTICS_ENTRIES entries
    for i in range(10):
        gui.stats["weapons_used"][f"W{i}"] = i + 1
    assert len(gui.stats["weapons_used"]) == 10
    limit_statistics_size(gui)
    # Should be trimmed to at most MAX_STATISTICS_ENTRIES
    assert len(gui.stats["weapons_used"]) <= gui.MAX_STATISTICS_ENTRIES
