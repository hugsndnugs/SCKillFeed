import os
import sys
import csv
import logging
from constants import DEFAULT_CSV_NAME, APP_DIRNAME

logger = logging.getLogger(__name__)


def resolve_auto_log_path(raw: str) -> str:
    """Resolve a writable path for the automatic CSV log.

    Logic mirrors the GUI helper: absolute path is used directly. For
    relative paths, prefer executable dir when frozen and writable, else
    fall back to %LOCALAPPDATA%/SCKillFeed or the user's home.
    """
    if not raw:
        raw = DEFAULT_CSV_NAME

    try:
        if os.path.isabs(raw):
            return raw

        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            candidate = os.path.join(exe_dir, raw)
            if os.access(exe_dir, os.W_OK):
                return candidate
            # fallback to LOCALAPPDATA
            local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            app_dir = os.path.join(local_app, APP_DIRNAME)
            os.makedirs(app_dir, exist_ok=True)
            return os.path.join(app_dir, raw)

        # not frozen
        base = os.path.dirname(os.path.abspath(__file__))
        # __file__ is in lib/, prefer project root for script mode
        project_root = os.path.dirname(base)
        candidate = os.path.join(project_root, raw)
        if os.access(project_root, os.W_OK):
            return candidate

        local_app = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        app_dir = os.path.join(local_app, APP_DIRNAME)
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, raw)
    except Exception:
        # last-resort fallback
        return os.path.abspath(raw)


def append_kill_to_csv(path: str, kill_data: dict) -> None:
    """Append a kill event to CSV at path, creating header if needed.

    This is best-effort and will log exceptions but not raise.
    """
    try:
        d = os.path.dirname(path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

        need_header = not os.path.exists(path) or os.path.getsize(path) == 0

        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if need_header:
                writer.writerow(["timestamp", "killer", "victim", "weapon"])
            # tolerate string timestamps or datetime-like objects
            ts = kill_data.get("timestamp", "")
            if hasattr(ts, "isoformat"):
                ts_val = ts.isoformat()
            else:
                ts_val = str(ts)

            writer.writerow(
                [
                    ts_val,
                    kill_data.get("killer", ""),
                    kill_data.get("victim", ""),
                    kill_data.get("weapon", ""),
                ]
            )
    except Exception:
        logger.debug("append_kill_to_csv failed", exc_info=True)
