import re
import os
import configparser
import logging

# Centralized regular expression for parsing kill lines from Game.log
KILL_LINE_RE = re.compile(
    r"<Actor Death>\s+CActor::Kill:\s*'(?P<victim>[^']+)'\s*\[[^\]]+\]\s*in zone '[^']+'\s*killed by\s*'(?P<killer>[^']+)'\s*\[[^\]]+\]\s*using\s*'(?P<weapon>[^']+)'",
    re.IGNORECASE,
)

# Monitoring and application defaults
MIN_STATISTICS_ENTRIES = 100
MAX_STATISTICS_ENTRIES_LIMIT = 10000
MIN_MAX_LINES_PER_CHECK = 1
MAX_MAX_LINES_PER_CHECK = 1000

DEFAULT_FILE_CHECK_INTERVAL = 0.1
DEFAULT_MAX_LINES_PER_CHECK = 100
DEFAULT_MAX_STATISTICS_ENTRIES = 1000
DEFAULT_READ_BUFFER_SIZE = 8192

# Default config filename used by the application
DEFAULT_CONFIG_FILENAME = "sc-kill-feed.cfg"

# Common locations to auto-detect Game.log on Windows
COMMON_GAME_LOG_PATHS = [
    os.path.expanduser("~/AppData/Local/Star Citizen/LIVE/Game.log"),
    os.path.expanduser("~/Documents/Star Citizen/LIVE/Game.log"),
    "C:/Program Files/Roberts Space Industries/StarCitizen/LIVE/Game.log",
]

# Other common magic values centralized
DEFAULT_KILLS_DEQUE_MAXLEN = 10000
RECENT_KILLS_COUNT = 10

# Debounce timing (milliseconds)
DEBOUNCE_BASE_MS = 100
DEBOUNCE_MIN_MS = 50

# Monitoring behavior
DEFAULT_MAX_CONSECUTIVE_FILE_ERRORS = 5
DEFAULT_MAX_LOG_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

_logger = logging.getLogger(__name__)

# Attempt to read a local config file and override a small set of runtime
# defaults. This keeps the application behaviour discoverable by inspecting
# `sc-kill-feed.cfg` while still providing safe fallbacks when the file or
# keys are missing or invalid.
try:
    _config = configparser.ConfigParser()
    if os.path.exists(DEFAULT_CONFIG_FILENAME):
        _config.read(DEFAULT_CONFIG_FILENAME)
        if "user" in _config:
            _user = _config["user"]

            def _get_float(key, fallback, minv=None, maxv=None):
                val = _user.get(key, fallback=None)
                if val is None:
                    return fallback
                try:
                    f = float(val)
                except Exception:
                    _logger.debug(
                        "Invalid float for %s in config, using fallback %s",
                        key,
                        fallback,
                    )
                    return fallback
                if minv is not None and f < minv:
                    return fallback
                if maxv is not None and f > maxv:
                    return fallback
                return f

            def _get_int(key, fallback, minv=None, maxv=None):
                val = _user.get(key, fallback=None)
                if val is None:
                    return fallback
                try:
                    i = int(float(val))
                except Exception:
                    _logger.debug(
                        "Invalid int for %s in config, using fallback %s", key, fallback
                    )
                    return fallback
                if minv is not None and i < minv:
                    return fallback
                if maxv is not None and i > maxv:
                    return fallback
                return i

            # Safely override defaults when present and valid
            DEFAULT_FILE_CHECK_INTERVAL = _get_float(
                "file_check_interval", DEFAULT_FILE_CHECK_INTERVAL, minv=0.01, maxv=10.0
            )
            DEFAULT_MAX_LINES_PER_CHECK = _get_int(
                "max_lines_per_check",
                DEFAULT_MAX_LINES_PER_CHECK,
                minv=MIN_MAX_LINES_PER_CHECK,
                maxv=MAX_MAX_LINES_PER_CHECK,
            )
            DEFAULT_MAX_STATISTICS_ENTRIES = _get_int(
                "max_statistics_entries",
                DEFAULT_MAX_STATISTICS_ENTRIES,
                minv=MIN_STATISTICS_ENTRIES,
                maxv=MAX_STATISTICS_ENTRIES_LIMIT,
            )
except Exception:
    # Non-fatal: if something goes wrong while reading the config file, keep
    # the hard-coded defaults and continue. Debug log for local troubleshooting.
    _logger.debug(
        "Failed to read/parse %s; using built-in defaults",
        DEFAULT_CONFIG_FILENAME,
        exc_info=True,
    )
