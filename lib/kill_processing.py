import logging
from datetime import datetime
from lib import kill_stats

logger = logging.getLogger(__name__)


def process_kill_event(gui, line: str):
    """Process a kill event line and update the provided GUI-like object.

    This function is a thin extraction of the original method that lived on
    the GUI class. It operates on an object that exposes the minimal set of
    attributes/methods used by the logic (KILL_LINE_RE, data_lock, kills_data,
    update_statistics, display_kill_event, safe_after, safe_after_idle,
    debounced_update_statistics, _append_kill_to_csv, config, player_name).
    """
    try:
        match = gui.KILL_LINE_RE.search(line)
        if not match:
            return

        victim = match.group("victim").strip()
        killer = match.group("killer").strip()
        weapon = match.group("weapon").strip()

        # Validate extracted data
        if not all([victim, killer, weapon]):
            logger.warning(
                f"Invalid kill event data - victim: '{victim}', killer: '{killer}', weapon: '{weapon}'"
            )
            return

        timestamp = datetime.now()
        # Update last kill timestamp for timer display
        try:
            gui.last_kill_time = timestamp
            try:
                # Attempt to reset timer on the UI thread; ignore if not present
                gui.safe_after(0, lambda: setattr(gui, "timer_var", "0:00:00"))
            except Exception:
                pass
        except Exception:
            logger.debug("Could not set last_kill_time", exc_info=True)

        # Store kill data
        kill_data = {
            "timestamp": timestamp,
            "victim": victim,
            "killer": killer,
            "weapon": weapon,
        }

        # Thread-safe data access
        try:
            with gui.data_lock:
                gui.kills_data.append(kill_data)
                try:
                    # Prefer the extracted statistics helper rather than
                    # relying on a GUI instance method.
                    kill_stats.update_statistics(gui, kill_data)
                except Exception:
                    # Best-effort: try a minimal counter update to keep things consistent.
                    try:
                        gui.stats["weapons_used"][weapon] += 1
                        gui.stats["weapons_against"][weapon] += 1
                        gui.stats["victims"][victim] += 1
                        gui.stats["killers"][killer] += 1
                    except Exception:
                        pass
        except Exception:
            # If data_lock isn't available or append fails, continue
            try:
                gui.kills_data.append(kill_data)
            except Exception:
                logger.debug("Failed to append kill to gui.kills_data", exc_info=True)

        # Automatic CSV logging (append each kill to a persistent CSV)
        try:
            auto_enabled = gui.config["user"].getboolean(
                "auto_log_enabled", fallback=True
            )
        except Exception:
            auto_enabled = True
        if auto_enabled:
            try:
                gui._append_kill_to_csv(kill_data)
            except Exception:
                logger.debug("Failed to append kill to CSV", exc_info=True)

        # Update UI in main thread with debouncing and thread safety
        try:
            gui.safe_after_idle(lambda: gui.display_kill_event(kill_data))
        except Exception:
            try:
                gui.display_kill_event(kill_data)
            except Exception:
                pass

        try:
            gui.debounced_update_statistics()
        except Exception:
            pass

        logger.debug(f"Processed kill event: {killer} killed {victim} with {weapon}")

    except Exception as e:
        logger.error(
            f"Error processing kill event line: {line[:100]}... Error: {e}",
            exc_info=True,
        )
