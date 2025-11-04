"""Configuration helpers: load, save and validate/apply config values.

These helpers operate on a `configparser.ConfigParser` and a GUI-like
object (the GUI class instance) when necessary so logic can be tested
and reused outside the large GUI file.
"""

import os
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str):
    """Load configuration from path and ensure defaults exist.

    Returns a ConfigParser instance with defaults filled in.
    """
    import configparser

    config = configparser.ConfigParser()
    try:
        if os.path.exists(config_path):
            try:
                config.read(config_path, encoding="utf-8")
                logger.info("Configuration loaded successfully")
            except Exception:
                logger.error("Error loading configuration, starting with empty config")
                config.clear()
    except Exception:
        logger.error("Unexpected error reading configuration", exc_info=True)

    if "user" not in config:
        config["user"] = {}

    defaults = {
        "ingame_name": "",
        "log_path": "",
        "auto_log_enabled": "true",
        "auto_log_csv": "kill_log.csv",
        "file_check_interval": "0.1",
        "max_lines_per_check": "100",
        "max_statistics_entries": "1000",
        "gui_scale": "1.0",
    }

    for key, value in defaults.items():
        if key not in config["user"]:
            config["user"][key] = value

    # Overlay defaults
    if "overlay" not in config:
        config["overlay"] = {}
    
    overlay_defaults = {
        "enabled": "false",
        "theme": "dark",
        "opacity": "0.92",
        "locked": "false",
        "position_x": "0",
        "position_y": "0",
    }
    
    for key, value in overlay_defaults.items():
        if key not in config["overlay"]:
            config["overlay"][key] = value

    return config


def validate_and_apply_config(config, gui):
    """Validate values in config['user'] and apply them to the GUI instance.

    This mutates the gui instance's attributes (FILE_CHECK_INTERVAL, MAX_LINES_PER_CHECK,
    MAX_STATISTICS_ENTRIES, gui_scale) to keep behavior identical to previous
    implementation but moves logic into a testable helper.
    """
    try:
        # file_check_interval
        try:
            interval = float(config["user"].get("file_check_interval", "0.1"))
            if interval < 0.01 or interval > 1.0:
                config["user"]["file_check_interval"] = "0.1"
                gui.FILE_CHECK_INTERVAL = 0.1
            else:
                gui.FILE_CHECK_INTERVAL = interval
        except Exception:
            config["user"]["file_check_interval"] = "0.1"
            gui.FILE_CHECK_INTERVAL = 0.1

        # max_lines_per_check
        try:
            max_lines = int(config["user"].get("max_lines_per_check", "100"))
            if max_lines < 1 or max_lines > 1000:
                config["user"]["max_lines_per_check"] = "100"
                gui.MAX_LINES_PER_CHECK = 100
            else:
                gui.MAX_LINES_PER_CHECK = max_lines
        except Exception:
            config["user"]["max_lines_per_check"] = "100"
            gui.MAX_LINES_PER_CHECK = 100

        # max_statistics_entries
        try:
            max_stats = int(config["user"].get("max_statistics_entries", "1000"))
            if max_stats < 100 or max_stats > 10000:
                config["user"]["max_statistics_entries"] = "1000"
                gui.MAX_STATISTICS_ENTRIES = 1000
            else:
                gui.MAX_STATISTICS_ENTRIES = max_stats
        except Exception:
            config["user"]["max_statistics_entries"] = "1000"
            gui.MAX_STATISTICS_ENTRIES = 1000

        # gui_scale
        try:
            scale = float(config["user"].get("gui_scale", "1.0"))
            if scale < 0.5 or scale > 2.0:
                config["user"]["gui_scale"] = "1.0"
                gui.gui_scale = 1.0
            else:
                gui.gui_scale = scale
        except Exception:
            config["user"]["gui_scale"] = "1.0"
            gui.gui_scale = 1.0

    except Exception:
        logger.debug("Configuration validation failed", exc_info=True)


def save_config(config, config_path: str):
    """Persist the ConfigParser to disk, creating dirs if needed."""
    try:
        config_dir = os.path.dirname(config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as fh:
            config.write(fh)
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        raise
