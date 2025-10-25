"""Monitoring helpers to run the log-file monitoring loop outside the GUI file."""

import os
import time
import logging

logger = logging.getLogger(__name__)


def monitor_log_file(gui):
    """Monitor the log file for kill events. Expects a gui instance with
    attributes used by the original method (is_monitoring, log_file_path,
    READ_BUFFER_SIZE, MAX_LINES_PER_CHECK, FILE_CHECK_INTERVAL, etc.) and
    methods like process_kill_event and safe_after.
    """
    logger.info(f"Starting log file monitoring: {gui.log_file_path}")

    try:
        with open(
            gui.log_file_path,
            "r",
            encoding="utf-8",
            errors="ignore",
            buffering=gui.READ_BUFFER_SIZE,
        ) as f:
            f.seek(0, os.SEEK_END)
            last_position = f.tell()
            consecutive_errors = 0
            max_consecutive_errors = 5

            while gui.is_monitoring:
                try:
                    try:
                        current_size = os.path.getsize(gui.log_file_path)
                    except OSError:
                        current_size = 0

                    if current_size < last_position:
                        logger.info(
                            "Log file was truncated or rotated, resetting to end"
                        )
                        f.seek(0, os.SEEK_END)
                        last_position = f.tell()
                    elif current_size > last_position:
                        f.seek(last_position)
                        lines_read = 0
                        lines_buffer = []

                        while (
                            lines_read < gui.MAX_LINES_PER_CHECK and gui.is_monitoring
                        ):
                            line = f.readline()
                            if not line:
                                break
                            lines_buffer.append(line)
                            lines_read += 1

                        for line in lines_buffer:
                            if "<Actor Death>" in line:
                                # Prefer calling a GUI-provided process_kill_event if present
                                # (tests and older code may set this). Fallback to the
                                # shared kill_processing helper if the GUI doesn't expose it.
                                if hasattr(gui, "process_kill_event"):
                                    try:
                                        gui.process_kill_event(line.strip())
                                    except Exception:
                                        logger.debug(
                                            "GUI process_kill_event failed",
                                            exc_info=True,
                                        )
                                else:
                                    try:
                                        from lib import kill_processing as _kp

                                        _kp.process_kill_event(gui, line.strip())
                                    except Exception:
                                        logger.debug(
                                            "kill_processing failed", exc_info=True
                                        )

                        last_position = f.tell()
                        consecutive_errors = 0
                    else:
                        time.sleep(gui.FILE_CHECK_INTERVAL)

                except (OSError, IOError) as e:
                    consecutive_errors += 1
                    logger.warning(
                        f"File access error (attempt {consecutive_errors}): {e}"
                    )

                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            "Too many consecutive file access errors, stopping monitoring"
                        )
                        try:
                            gui.safe_after(
                                0,
                                lambda: gui.status_var.set(
                                    "Too many file access errors, monitoring stopped"
                                ),
                            )
                        except Exception:
                            pass
                        break

                    time.sleep(gui.FILE_CHECK_INTERVAL * 5)

    except FileNotFoundError as e:
        error_msg = f"Log file not found: {str(e)}"
        logger.error(error_msg)
        try:
            gui.safe_after(0, lambda: gui.status_var.set(error_msg))
        except Exception:
            pass
    except PermissionError as e:
        error_msg = f"Permission denied accessing log file: {str(e)}"
        logger.error(error_msg)
        try:
            gui.safe_after(0, lambda: gui.status_var.set(error_msg))
        except Exception:
            pass
    except UnicodeDecodeError as e:
        error_msg = f"Error reading log file encoding: {str(e)}"
        logger.error(error_msg)
        try:
            gui.safe_after(0, lambda: gui.status_var.set(error_msg))
        except Exception:
            pass
    except Exception as e:
        error_msg = f"Unexpected error monitoring file: {str(e)}"
        logger.error(error_msg, exc_info=True)
        try:
            gui.safe_after(0, lambda: gui.status_var.set(error_msg))
        except Exception:
            pass
    finally:
        logger.info("Log file monitoring stopped")
