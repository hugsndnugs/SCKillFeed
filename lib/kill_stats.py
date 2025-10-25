"""Statistics update helpers extracted from the GUI.

These functions operate on a GUI-like object exposing the minimal state
required (stats dict, player_name, MAX_STATISTICS_ENTRIES, data_lock and
associated attributes). They are defensive and best-effort so they can be
unit-tested independently of the full Tk UI.
"""

import logging
from collections import Counter
from typing import Dict

logger = logging.getLogger(__name__)


def limit_statistics_size(gui) -> None:
    """Trim Counter-based statistics on the gui to prevent unbounded growth.

    Keeps only the most_common N entries for each counter, where N is taken
    from gui.MAX_STATISTICS_ENTRIES if present, else falls back to 1000.
    """
    try:
        max_entries = getattr(gui, "MAX_STATISTICS_ENTRIES", 1000)

        for key in ("weapons_used", "weapons_against", "victims", "killers"):
            try:
                counter = gui.stats.get(key)
                if isinstance(counter, Counter) and len(counter) > max_entries:
                    most_common = counter.most_common(max_entries)
                    counter.clear()
                    for name, cnt in most_common:
                        counter[name] = cnt
            except Exception:
                # Ignore per-counter failures and continue with others
                logger.debug("Failed to trim counter %s", key, exc_info=True)

        logger.debug("Statistics counters size limited to %d entries", max_entries)
    except Exception:
        logger.debug("limit_statistics_size failed", exc_info=True)


def update_statistics(gui, kill_data: Dict[str, str]) -> None:
    """Update the statistics on the gui based on a single kill_data dict.

    Expected kill_data keys: 'victim', 'killer', 'weapon'. The function
    updates counters and player-centric stats (total_kills, total_deaths,
    streaks) and calls limit_statistics_size periodically.
    """
    try:
        victim = kill_data.get("victim", "")
        killer = kill_data.get("killer", "")
        weapon = kill_data.get("weapon", "")

        # Update counters
        try:
            gui.stats["weapons_used"][weapon] += 1
            gui.stats["weapons_against"][weapon] += 1
            gui.stats["victims"][victim] += 1
            gui.stats["killers"][killer] += 1
        except Exception:
            # Try to ensure the counters exist minimally
            gui.stats.setdefault("weapons_used", Counter())[weapon] += 1
            gui.stats.setdefault("weapons_against", Counter())[weapon] += 1
            gui.stats.setdefault("victims", Counter())[victim] += 1
            gui.stats.setdefault("killers", Counter())[killer] += 1

        # Periodically limit statistics size to prevent memory leaks.
        # This checks a coarse-grained frequency (every 100 entries)
        try:
            total_entries = (
                len(gui.stats.get("weapons_used", {}))
                + len(gui.stats.get("weapons_against", {}))
                + len(gui.stats.get("victims", {}))
                + len(gui.stats.get("killers", {}))
            )
            if total_entries % 100 == 0:
                limit_statistics_size(gui)
        except Exception:
            # ignore size-trim failures
            pass

        # Handle suicides first
        try:
            if killer == victim:
                if killer == getattr(gui, "player_name", None):
                    gui.stats["total_deaths"] += 1
                    gui.stats["death_streak"] += 1
                    gui.stats["kill_streak"] = 0
                    gui.stats["max_death_streak"] = max(
                        gui.stats.get("max_death_streak", 0), gui.stats["death_streak"]
                    )
                # Non-player suicides don't affect player's kill/death counts
                return
        except Exception:
            logger.debug("suicide handling failed", exc_info=True)

        # Non-suicide involvement: update player-centric stats
        try:
            player = getattr(gui, "player_name", None)
            if killer == player:
                gui.stats["total_kills"] += 1
                gui.stats["kill_streak"] += 1
                gui.stats["death_streak"] = 0
                gui.stats["max_kill_streak"] = max(
                    gui.stats.get("max_kill_streak", 0), gui.stats["kill_streak"]
                )
            elif victim == player:
                gui.stats["total_deaths"] += 1
                gui.stats["death_streak"] += 1
                gui.stats["kill_streak"] = 0
                gui.stats["max_death_streak"] = max(
                    gui.stats.get("max_death_streak", 0), gui.stats["death_streak"]
                )
        except Exception:
            logger.debug("player involvement update failed", exc_info=True)

    except Exception:
        logger.error("Error updating statistics", exc_info=True)
