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

# Monitoring behavior
DEFAULT_MAX_LOG_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB

# Application strings and assets
APP_TITLE = "Star Citizen Kill Feed Tracker"
ASSETS_DIR = "assets"
ICON_FILENAME = "sckt-icon.ico"
DEFAULT_WINDOW_GEOMETRY = "1400x900"

# Application defaults
DEFAULT_CSV_NAME = "kill_log.csv"
APP_DIRNAME = "SCKillFeed"

# UI theme palette
THEME_BG_PRIMARY = "#0a0a0a"
THEME_BG_SECONDARY = "#0a0a0a"
THEME_BG_TERTIARY = "#0a0a0a"
THEME_ACCENT_PRIMARY = "#00d4ff"
THEME_ACCENT_SECONDARY = "#ff6b35"
THEME_ACCENT_SUCCESS = "#00ff88"
THEME_ACCENT_DANGER = "#ff4757"
THEME_ACCENT_WARNING = "#ffa502"
THEME_TEXT_PRIMARY = "#ffffff"
THEME_TEXT_SECONDARY = "#b0b0b0"
THEME_TEXT_MUTED = "#808080"

# Fonts
FONT_FAMILY = "Segoe UI"

# Misc UI constants
STYLE_SCALE_BUTTON = "Scale.TButton"
STYLE_SMALL_BUTTON = "Small.TButton"
STYLE_CARD_FRAME = "Card.TFrame"

_logger = logging.getLogger(__name__)
STATS_STREAK_TEMPLATE = "🔥 Current Streak: {n}"

# More UI captions and messages centralized for easy localization/testing
DIALOG_SELECT_LOG_TITLE = "Select Star Citizen Game.log"
DIALOG_EXPORT_TITLE = "Export Kill Data"
MSG_AUTO_DETECT_TITLE = "Auto-detect"
MSG_AUTO_DETECT_FOUND_FMT = "Found Game.log at:\n{path}"
MSG_AUTO_DETECT_NOT_FOUND = (
    "Could not auto-detect Game.log file.\nPlease browse manually."
)
MSG_SETTINGS_SAVED = "Settings saved successfully!"
MSG_ERROR_TITLE = "Error"
MSG_WARNING_TITLE = "Warning"
MSG_SUCCESS_TITLE = "Success"
MSG_INVALID_PLAYER_NAME = (
    "Please enter a valid in-game name (1-50 characters, no special characters)."
)
MSG_INVALID_LOG_PATH = (
    "Please select a valid Game.log file. The file must exist and be a .log file."
)
MSG_CONFIGURE_FIRST = "Please configure your settings first."
MSG_LOG_NOT_FOUND = "Game.log file not found or invalid. Please check the path."
MSG_NO_DATA_TO_EXPORT = "No data to export."
MSG_SELECT_EXPORT_FORMAT = "Please select at least one export format."
MSG_EXPORT_SUCCESS = "Data exported successfully!"
MSG_EXPORT_DIR_NOT_FOUND_FMT = "Export directory not found: {err}"
MSG_EXPORT_PERMISSION_FMT = "Permission denied writing export file: {err}"
MSG_EXPORT_ENCODING_FMT = "Error encoding export data: {err}"
MSG_EXPORT_FAILED_FMT = "Failed to export data: {err}"

# Button and label text
BUTTON_CLOSE_SYMBOL = "✕"
BUTTON_MINIMIZE_SYMBOL = "—"
BUTTON_ZOOM_MINUS = "Zoom -"
BUTTON_RESET = "Reset"
BUTTON_ZOOM_PLUS = "Zoom +"
BUTTON_AUTO_DETECT_TEXT = "🔍 Auto-detect Game.log"
BUTTON_SAVE_SETTINGS_TEXT = "💾 Save Settings"
BUTTON_EXPORT_TEXT = "📤 Export Data"

# Status and captions
STATUS_READY = "Ready - Configure settings to start monitoring"
STATUS_MONITORING = "Monitoring started - Watching for kill events..."
STATUS_AUTO_STARTED = "Auto-started monitoring"
TIMER_CAPTION = "Time since last kill/death:"

# Short templates for stats labels
STATS_KILLS_TEMPLATE = "💀 Kills: {n}"
STATS_DEATHS_TEMPLATE = "💀 Deaths: {n}"
STATS_KD_TEMPLATE = "📊 K/D Ratio: {v:.2f}"

# Tab and frame captions
TAB_KILL_FEED = "🎯 Kill Feed"
TAB_LIVE_FEED = "📊 Live Combat Feed"
TAB_STATISTICS = "📈 Statistics"
TAB_LIFETIME_STATS = "📊 Lifetime Stats"
TAB_SETTINGS = "⚙️ Settings"
TAB_EXPORT = "📤 Export Data"

# Labels and group titles
LABEL_COMBAT_STATISTICS = "⚔️ Combat Statistics"
LABEL_WEAPON_STATISTICS = "🔫 Weapon Statistics"
LABEL_RECENT_ACTIVITY = "📋 Recent Activity"
LABEL_LIFETIME_METRICS = "📊 Lifetime Metrics"
LABEL_LIFETIME_WEAPONS = "🔫 Lifetime Weapon Statistics"
LABEL_LIFETIME_PVP = "👥 Player vs Player"
LABEL_LIFETIME_TRENDS = "📈 Performance Trends"
LABEL_LIFETIME_STREAKS = "🔥 Streak Statistics"
LABEL_PLAYER_CONFIG = "👤 Player Configuration"
LABEL_LOG_CONFIG = "📁 Log File Configuration"
LABEL_EXPORT_OPTIONS = "📋 Export Options"

# Column / heading text
HEADING_WEAPON = "Weapon"
HEADING_KILLS = "Kills"
HEADING_TIME = "Time"
HEADING_EVENT = "Event"

# Misc small labels
LABEL_YOUR_INGAME_NAME = "Your In-Game Name:"
LABEL_GAME_LOG_PATH = "Star Citizen Game.log Path:"
BUTTON_BROWSE_TEXT = "🔍 Browse"
BUTTON_REFRESH_LIFETIME = "🔄 Refresh Stats"
BUTTON_EXPORT_LIFETIME = "📤 Export Lifetime Report"
CHECK_CSV_TEXT = "📊 Export as CSV"
CHECK_JSON_TEXT = "📄 Export as JSON"

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
