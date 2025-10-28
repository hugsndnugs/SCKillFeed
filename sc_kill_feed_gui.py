#!/usr/bin/env python3
"""
Star Citizen Kill Feed Tracker - GUI Version

A modern GUI application for tracking Star Citizen kill events
with real-time display, statistics, and data export capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import time
import threading
from datetime import datetime
import configparser
from collections import Counter, deque
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sc_kill_feed.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

from lib.io_helpers import resolve_auto_log_path, append_kill_to_csv
from lib.win32_helpers import (
    set_app_icon,
    apply_native_win32_borderless,
    set_foreground_hwnd,
    setup_taskbar_click_handler,
)
from lib.ui_helpers import (
    setup_styles,
    init_scaling,
    apply_font_scaling,
    increase_scale,
    decrease_scale,
    reset_scale,
    create_kill_feed_tab,
    create_statistics_tab,
    create_settings_tab,
    create_export_tab,
)
from lib.validation_helpers import validate_player_name
from lib.config_helpers import load_config, validate_and_apply_config, save_config
from lib import export_helpers
from lib import monitor_helpers

from constants import (
    KILL_LINE_RE,
    DEFAULT_FILE_CHECK_INTERVAL,
    DEFAULT_MAX_LINES_PER_CHECK,
    DEFAULT_MAX_STATISTICS_ENTRIES,
    DEFAULT_READ_BUFFER_SIZE,
    DEFAULT_CONFIG_FILENAME,
    COMMON_GAME_LOG_PATHS,
    DEFAULT_KILLS_DEQUE_MAXLEN,
    RECENT_KILLS_COUNT,
    DEFAULT_MAX_LOG_FILE_SIZE_BYTES,
    APP_TITLE,
    DEFAULT_WINDOW_GEOMETRY,
    THEME_BG_PRIMARY,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    THEME_ACCENT_DANGER,
    ASSETS_DIR,
    ICON_FILENAME,
    DEFAULT_CSV_NAME,
    FONT_FAMILY,
    DIALOG_SELECT_LOG_TITLE,
    DIALOG_EXPORT_TITLE,
    MSG_AUTO_DETECT_TITLE,
    MSG_AUTO_DETECT_FOUND_FMT,
    MSG_AUTO_DETECT_NOT_FOUND,
    MSG_SETTINGS_SAVED,
    MSG_ERROR_TITLE,
    MSG_WARNING_TITLE,
    MSG_SUCCESS_TITLE,
    MSG_INVALID_PLAYER_NAME,
    MSG_INVALID_LOG_PATH,
    MSG_CONFIGURE_FIRST,
    MSG_LOG_NOT_FOUND,
    MSG_NO_DATA_TO_EXPORT,
    MSG_SELECT_EXPORT_FORMAT,
    MSG_EXPORT_SUCCESS,
    MSG_EXPORT_DIR_NOT_FOUND_FMT,
    MSG_EXPORT_PERMISSION_FMT,
    MSG_EXPORT_ENCODING_FMT,
    MSG_EXPORT_FAILED_FMT,
    BUTTON_CLOSE_SYMBOL,
    BUTTON_MINIMIZE_SYMBOL,
    BUTTON_ZOOM_MINUS,
    BUTTON_RESET,
    BUTTON_ZOOM_PLUS,
    STATUS_READY,
    STATUS_MONITORING,
    STATUS_AUTO_STARTED,
    TIMER_CAPTION,
)


# Custom exception classes for better error handling
class KillFeedError(Exception):
    """Base exception for kill feed errors"""

    pass


class LogFileError(KillFeedError):
    """Log file related errors"""

    pass


class ConfigurationError(KillFeedError):
    """Configuration related errors"""

    pass


class StarCitizenKillFeedGUI:
    def __init__(self):
        # Create the primary Tk root. On Windows we keep a hidden Tk root and
        # show a borderless Toplevel as the visible app window. This pattern
        # preserves taskbar behavior while allowing a custom chrome.
        if sys.platform == "win32":
            self._tk_root = tk.Tk()
            # Keep the real root present for the OS (taskbar/alt-tab) but make
            # it visually invisible by setting alpha to 0.0. We do NOT withdraw
            # it; that would remove the taskbar entry. The Toplevel will follow
            # the root's map/unmap (iconify/deiconify) events so minimizing the
            # taskbar button affects the visible window.
            try:
                # Make the root fully transparent
                self._tk_root.attributes("-alpha", 0.0)
                # Lower it so the user doesn't accidentally focus it
                try:
                    self._tk_root.lower()
                except Exception:
                    pass
            except Exception:
                # If alpha isn't supported, fall back to withdrawing but note
                # that taskbar behavior may vary.
                try:
                    self._tk_root.withdraw()
                except Exception:
                    try:
                        self._tk_root.iconify()
                    except Exception:
                        pass

            # Create the visible window as a Toplevel attached to the hidden root
            self.root = tk.Toplevel(self._tk_root)
            self.root.title(APP_TITLE)
            self.root.geometry(DEFAULT_WINDOW_GEOMETRY)
            # When using a Toplevel, we'll allow borderless mode on Windows but
            # use the native-style technique later to keep taskbar entry.
            self._borderless_enabled = True
            # Make the visible Toplevel follow the hidden root's map/unmap so
            # minimizing the taskbar button hides the visible window and vice versa.
            # Also handle window state changes more reliably
            try:
                self._tk_root.bind("<Unmap>", self._on_root_unmap)
                self._tk_root.bind("<Map>", self._on_root_map)
                self._tk_root.bind("<FocusIn>", self._on_root_focus_in)
                self._tk_root.bind("<FocusOut>", self._on_root_focus_out)
            except Exception:
                pass
        else:
            self._tk_root = None
            self.root = tk.Tk()
            self.root.title(APP_TITLE)
            self.root.geometry(DEFAULT_WINDOW_GEOMETRY)
            # Replace standard window chrome with a custom title bar when possible.
            try:
                self.root.overrideredirect(True)
                self._borderless_enabled = True
            except Exception:
                # Some platforms or window managers may not support this; ignore
                self._borderless_enabled = False

        try:
            self.root.configure(bg=THEME_BG_PRIMARY)
        except Exception:
            pass

        # Configuration and runtime state
        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_path()
        # Load configuration via helper
        try:
            self.config = load_config(self.config_path)
            validate_and_apply_config(self.config, self)
        except Exception:
            logger.debug("load_config failed", exc_info=True)

        self.kills_data = deque(maxlen=DEFAULT_KILLS_DEQUE_MAXLEN)
        self.data_lock = threading.RLock()

        self.MAX_STATISTICS_ENTRIES = DEFAULT_MAX_STATISTICS_ENTRIES
        self.player_name = self.config["user"].get("ingame_name", "")
        self.log_file_path = self.config["user"].get("log_path", "")
        self.is_monitoring = False
        self.monitor_thread = None

        # Performance settings
        self.FILE_CHECK_INTERVAL = DEFAULT_FILE_CHECK_INTERVAL
        self.MAX_LINES_PER_CHECK = DEFAULT_MAX_LINES_PER_CHECK
        self.READ_BUFFER_SIZE = DEFAULT_READ_BUFFER_SIZE

        # UI update debouncing and thread-safety
        self._update_timer = None
        self._pending_updates = 0
        self._ui_update_lock = threading.Lock()
        self._last_update_time = 0

        # GUI scaling (1.0 = 100%)
        self.gui_scale = 1.0
        self._base_font_sizes = {}
        self._font_objects = {}
        self._base_style_paddings = {}

        # Last-kill timer
        self.last_kill_time = None
        self._timer_job = None

        # Statistics
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

        # Regex for parsing kill events - compiled once for efficiency
        self.KILL_LINE_RE = KILL_LINE_RE

        self.setup_ui()
        # Apply ttk styles via helper
        try:
            setup_styles()
        except Exception:
            logger.debug("setup_styles failed", exc_info=True)

        # Ensure the window title (taskbar text) is the application name and
        # attempt to set the taskbar icon from the assets .ico file. When we
        # use a hidden root + visible Toplevel on Windows the taskbar entry
        # is owned by the hidden root, so set both titles/icons where present.
        try:
            app_title = APP_TITLE
            try:
                self.root.title(app_title)
            except Exception:
                pass
            try:
                if getattr(self, "_tk_root", None):
                    try:
                        self._tk_root.title(app_title)
                    except Exception:
                        pass
            except Exception:
                pass

            # Try to load and apply the app icon
            try:
                base = os.path.dirname(os.path.abspath(__file__))
                ico_path = os.path.join(base, ASSETS_DIR, ICON_FILENAME)
                try:
                    set_app_icon(self.root, getattr(self, "_tk_root", None), ico_path)
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

        # On Windows, remove the standard window caption by changing the native
        # window style instead of using overrideredirect. This keeps a normal
        # taskbar entry while allowing a custom in-client title bar.
        try:
            if sys.platform == "win32":
                try:
                    # Delay the native style change slightly so the window is
                    # fully created and the window manager has a chance to register it.
                    # Some Windows compositions override style changes immediately
                    # after creation, so scheduling the change reduces race conditions.
                    self.root.after(
                        150, lambda: apply_native_win32_borderless(self.root)
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Initialize scaling/font baselines and start timer loop
        try:
            init_scaling(self)
        except Exception:
            logger.debug("Failed to initialize font scaling baseline", exc_info=True)
        # Apply any configured GUI scale immediately
        try:
            apply_font_scaling(self)
        except Exception:
            logger.debug("Failed to apply initial GUI scale", exc_info=True)

        # Start timer loop
        self._start_timer_loop()

        # Ensure config is saved on exit (persist scale/settings)
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            pass

        # Auto-start monitoring if we have a configured player name and a valid log path
        try:
            if (
                self.player_name
                and self.log_file_path
                and self.validate_file_path(self.log_file_path)
            ):
                try:
                    self.start_monitoring()
                    try:
                        self.status_var.set("Auto-started monitoring")
                        # After 5s, set the regular monitoring message
                        self.safe_after(
                            5000,
                            lambda: self.status_var.set(
                                "Monitoring started - Watching for kill events..."
                            ),
                        )
                    except Exception:
                        pass
                except Exception:
                    logger.debug("Auto-start monitoring failed", exc_info=True)
        except Exception:
            logger.debug("Auto-start check failed", exc_info=True)

    def _on_close(self):
        """Handler for window close to persist configuration before exit."""
        try:
            # Persist gui_scale to config
            try:
                self.config["user"]["gui_scale"] = str(self.gui_scale)
                try:
                    save_config(self.config, self.config_path)
                except Exception:
                    logger.debug("Failed to save gui_scale on close", exc_info=True)
            except Exception:
                logger.debug("Failed to save gui_scale on close", exc_info=True)
        finally:
            # Destroy the visible window and the hidden root (if present)
            try:
                try:
                    self.root.destroy()
                except Exception:
                    pass
                if getattr(self, "_tk_root", None):
                    try:
                        self._tk_root.destroy()
                    except Exception:
                        pass
            except Exception:
                pass

    def safe_after_idle(self, callback):
        """Safely call after_idle, handling both real Tkinter root and test mocks"""
        try:
            if hasattr(self.root, "after_idle"):
                self.root.after_idle(callback)
            else:
                # For testing scenarios with mock root objects
                callback()
        except AttributeError:
            # Fallback for testing scenarios
            callback()

    def safe_after(self, delay, callback):
        """Safely call after, handling both real Tkinter root and test mocks"""
        try:
            if hasattr(self.root, "after"):
                return self.root.after(delay, callback)
            else:
                # For testing scenarios with mock root objects, execute immediately
                callback()
                return None
        except AttributeError:
            # Fallback for testing scenarios
            callback()
            return None

    # --------------------- Scaling and timer helpers ---------------------
    def _start_timer_loop(self):
        """Start the periodic timer that updates the elapsed time since last kill."""
        # Use safe_after so tests without real root don't error
        if self._timer_job is not None:
            try:
                if hasattr(self.root, "after_cancel"):
                    self.root.after_cancel(self._timer_job)
            except Exception:
                pass
        # Schedule first tick immediately
        self._timer_job = self.safe_after(1000, self._timer_tick)

    def _timer_tick(self):
        """Update the timer display and reschedule itself."""
        try:
            if self.last_kill_time is None or self.last_kill_time == "":
                self.timer_var.set("--:--:--")
            else:
                delta = datetime.now() - self.last_kill_time
                # Format as H:MM:SS
                total_seconds = int(delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self.timer_var.set(f"{hours:d}:{minutes:02d}:{seconds:02d}")
        except Exception:
            logger.debug("Timer tick error", exc_info=True)
        finally:
            # Reschedule
            self._timer_job = self.safe_after(1000, self._timer_tick)

    def get_config_path(self):
        """Get the configuration file path"""
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(exe_dir, DEFAULT_CONFIG_FILENAME)

    def validate_file_path(self, file_path: str) -> bool:
        """Validate file path to prevent directory traversal attacks"""
        if not file_path or not isinstance(file_path, str):
            logger.warning("Invalid file path: empty or not a string")
            return False

        try:
            # Sanitize input by stripping whitespace
            file_path = file_path.strip()

            # Check for minimum length
            if len(file_path) < 3:
                logger.warning("File path too short")
                return False

            # Check if path contains suspicious patterns
            suspicious_patterns = [
                "..",
                "~",
                "$",
                "`",
                "|",
                "&",
                ";",
                "(",
                ")",
                "<",
                ">",
            ]
            for pattern in suspicious_patterns:
                if pattern in file_path:
                    logger.warning(f"Suspicious pattern '{pattern}' found in file path")
                    return False

            # Normalize the path to prevent directory traversal
            normalized_path = os.path.normpath(file_path)
            resolved_path = os.path.abspath(normalized_path)

            # Check if the resolved path is still within reasonable bounds
            if len(resolved_path) > 260:  # Windows path length limit
                logger.warning("File path too long")
                return False

            # Check if file exists and is a .log file
            if not os.path.exists(resolved_path):
                logger.warning(f"File does not exist: {resolved_path}")
                return False

            if not resolved_path.lower().endswith(".log"):
                logger.warning("File is not a .log file")
                return False

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(resolved_path):
                logger.warning("Path is not a file")
                return False

            # Check file size (warn if extremely large)
            file_size = os.path.getsize(resolved_path)
            if file_size > DEFAULT_MAX_LOG_FILE_SIZE_BYTES:
                logger.warning(
                    f"Log file is very large: {file_size / (1024*1024):.1f}MB"
                )

            logger.debug(f"File path validated successfully: {resolved_path}")
            return True

        except (OSError, ValueError) as e:
            logger.error(f"Error validating file path: {e}")
            return False

    def setup_ui(self):
        """Setup the main user interface with modern design"""
        # Custom title bar (replaces standard window chrome)
        title_bar = tk.Frame(self.root, bg=THEME_BG_PRIMARY, relief="flat")
        title_bar.pack(fill=tk.X)
        title_label = tk.Label(
            title_bar,
            text=APP_TITLE,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
            padx=10,
        )
        title_label.pack(side=tk.LEFT, pady=4)

        # Window control buttons (minimize, close)
        btn_frame = tk.Frame(title_bar, bg=THEME_BG_PRIMARY)
        btn_frame.pack(side=tk.RIGHT, padx=6, pady=2)

        def _make_title_button(text, command, fg="#ffffff"):
            return tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=THEME_BG_PRIMARY,
                fg=fg,
                bd=0,
                highlightthickness=0,
                activebackground="#1a1a1a",
                padx=8,
                pady=2,
            )

        close_btn = _make_title_button(
            BUTTON_CLOSE_SYMBOL, lambda: self._on_close(), fg=THEME_ACCENT_DANGER
        )
        close_btn.pack(side=tk.RIGHT, padx=(6, 0))
        minimize_btn = _make_title_button(
            BUTTON_MINIMIZE_SYMBOL, lambda: self._minimize_window()
        )
        minimize_btn.pack(side=tk.RIGHT)

        # Make title bar draggable
        def _start_move(event):
            try:
                self._drag_start_x = event.x_root
                self._drag_start_y = event.y_root
                self._win_start_x = self.root.winfo_x()
                self._win_start_y = self.root.winfo_y()
            except Exception:
                pass

        def _on_move(event):
            try:
                dx = event.x_root - self._drag_start_x
                dy = event.y_root - self._drag_start_y
                new_x = self._win_start_x + dx
                new_y = self._win_start_y + dy
                self.root.geometry(f"+{new_x}+{new_y}")
            except Exception:
                pass

        title_bar.bind("<ButtonPress-1>", _start_move)
        title_bar.bind("<B1-Motion>", _on_move)
        title_label.bind("<ButtonPress-1>", _start_move)
        title_label.bind("<B1-Motion>", _on_move)

        # Bring window to front when clicked (makes clicking the window raise it)
        def _on_click_raise(event):
            try:
                self._raise_and_focus()
            except Exception:
                pass

        try:
            # Use add="+" so we don't override the existing drag handlers
            title_bar.bind("<Button-1>", _on_click_raise, add="+")
            title_label.bind("<Button-1>", _on_click_raise, add="+")
        except Exception:
            pass

        # When restored from minimized state, re-enable borderless chrome if configured
        try:
            self.root.bind("<Map>", lambda e: self._on_root_map(e))
        except Exception:
            pass

        # Add periodic state synchronization for Windows hidden root setup
        if sys.platform == "win32" and getattr(self, "_tk_root", None):
            try:
                self._schedule_state_sync()
                # Setup taskbar click handler for more reliable interaction
                setup_taskbar_click_handler(self._tk_root, self._on_taskbar_click)
            except Exception:
                pass

        # Main container with padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header row above the tabs: place global controls here (e.g. Scale UI)
        try:
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=(0, 8))

            # Centered scale controls so they're available on all tabs
            try:
                scale_header = ttk.Frame(header_frame)
                # Center the controls horizontally
                scale_header.pack(anchor="center", pady=6)

                # Compact, centered controls (no label)
                try:
                    dec_btn = ttk.Button(
                        scale_header,
                        text=BUTTON_ZOOM_MINUS,
                        command=lambda: decrease_scale(self),
                        style="Scale.TButton",
                    )
                    dec_btn.pack(side=tk.LEFT, padx=6)
                    reset_btn = ttk.Button(
                        scale_header,
                        text=BUTTON_RESET,
                        command=lambda: reset_scale(self),
                        style="Scale.TButton",
                    )
                    reset_btn.pack(side=tk.LEFT, padx=6)
                    inc_btn = ttk.Button(
                        scale_header,
                        text=BUTTON_ZOOM_PLUS,
                        command=lambda: increase_scale(self),
                        style="Scale.TButton",
                    )
                    inc_btn.pack(side=tk.LEFT, padx=6)
                except Exception:
                    pass
            except Exception:
                pass
            except Exception:
                pass
        except Exception:
            pass

        # Ensure clicks in the main content area also raise/focus the window
        try:
            # Append the raise handler so widget-specific binds (e.g. dragging)
            # are preserved.
            main_frame.bind("<Button-1>", lambda e: self._raise_and_focus(), add="+")
        except Exception:
            pass

        # Bind globally so any click inside the application raises/focuses the
        # window. Use add="+" to avoid clobbering existing widget bindings.
        try:
            # bind_all affects all widgets in this Tk instance
            self.root.bind_all("<Button-1>", lambda e: self._raise_and_focus(), add="+")
        except Exception:
            pass

        # If we replaced the window chrome, add custom resize handling so users
        # can still resize the window by dragging edges/corners.
        if getattr(self, "_borderless_enabled", False):
            self._resizing = False
            self._resize_dir = None
            self._resize_start_x = 0
            self._resize_start_y = 0
            self._start_geom = (0, 0, 0, 0)  # x, y, w, h
            self._resize_border = 8

            # Bind root-level events for resize UX
            # Delegate actual handlers to window_helpers
            try:
                from lib.window_helpers import (
                    on_root_motion,
                    on_root_button_press,
                    on_root_button_release,
                    on_root_drag,
                )

                self.root.bind("<Motion>", lambda e: on_root_motion(self, e))
                self.root.bind(
                    "<ButtonPress-1>", lambda e: on_root_button_press(self, e)
                )
                self.root.bind(
                    "<ButtonRelease-1>", lambda e: on_root_button_release(self, e)
                )
                self.root.bind("<B1-Motion>", lambda e: on_root_drag(self, e))
            except Exception:
                # fall back to no-op handlers if import fails
                self.root.bind("<Motion>", lambda e: None)
                self.root.bind("<ButtonPress-1>", lambda e: None)
                self.root.bind("<ButtonRelease-1>", lambda e: None)
                self.root.bind("<B1-Motion>", lambda e: None)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs via helpers
        try:
            create_kill_feed_tab(self)
        except Exception:
            logger.debug("create_kill_feed_tab failed", exc_info=True)
        try:
            create_statistics_tab(self)
        except Exception:
            logger.debug("create_statistics_tab failed", exc_info=True)
        try:
            create_settings_tab(self)
        except Exception:
            logger.debug("create_settings_tab failed", exc_info=True)
        try:
            create_export_tab(self)
        except Exception:
            logger.debug("create_export_tab failed", exc_info=True)

        # Modern status bar
        status_frame = ttk.Frame(main_frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(15, 0))

        # Left side: status message
        self.status_var = tk.StringVar()
        self.status_var.set(STATUS_READY)
        # Status text should be larger by default (twice size at 100% scale)
        status_bar_left = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_SECONDARY,
            anchor="w",
            font=(FONT_FAMILY, 12),
            padx=15,
            pady=8,
        )
        status_bar_left.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Right side: running timer since last kill event (with caption)
        self.timer_var = tk.StringVar()
        self.timer_var.set("--:--:--")
        # Container to hold caption + timer value so they stay grouped on the right
        timer_container = ttk.Frame(status_frame)
        timer_container.pack(side=tk.RIGHT, padx=10, pady=4)

        timer_caption = tk.Label(
            timer_container,
            text=TIMER_CAPTION,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_SECONDARY,
            font=(FONT_FAMILY, 12),
        )
        timer_caption.pack(side=tk.LEFT, padx=(0, 8))

        timer_label = tk.Label(
            timer_container,
            textvariable=self.timer_var,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_SECONDARY,
            anchor="e",
            font=(FONT_FAMILY, 12),
        )
        timer_label.pack(side=tk.LEFT)

    def _minimize_window(self):
        """Minimize the window and try to ensure it has a taskbar entry on Windows."""
        try:
            if getattr(self, "_tk_root", None):
                # On Windows with hidden root, minimize the root window
                # This will trigger the Unmap event and hide the visible window
                try:
                    self._tk_root.iconify()
                    return
                except Exception:
                    try:
                        self._tk_root.withdraw()
                        return
                    except Exception:
                        pass
            else:
                # Fallback for non-Windows or when no hidden root
                try:
                    self.root.iconify()
                    return
                except Exception:
                    try:
                        self.root.withdraw()
                        return
                    except Exception:
                        return
        except Exception:
            # If anything unexpected happens, ignore to avoid crashing the UI
            return

    def _on_root_unmap(self, event=None):
        """Handle when the hidden root window is minimized (taskbar icon clicked)."""
        try:
            # Hide the visible window when the root is minimized
            self.root.withdraw()
        except Exception:
            pass

    def _on_root_map(self, event=None):
        """Handle when the hidden root window is restored (taskbar icon clicked)."""
        try:
            # Show and raise the visible window when the root is restored
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            # Re-enable borderless chrome after restoration
            if getattr(self, "_borderless_enabled", False):
                try:
                    # Delay slightly to allow WM to finish mapping
                    self.root.after(20, lambda: self.root.overrideredirect(True))
                except Exception:
                    try:
                        self.root.overrideredirect(True)
                    except Exception:
                        pass
        except Exception:
            pass

    def _on_root_focus_in(self, event=None):
        """Handle when the hidden root window gains focus."""
        try:
            # Ensure the visible window is shown and focused
            if not self.root.winfo_viewable():
                self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
        except Exception:
            pass

    def _on_root_focus_out(self, event=None):
        """Handle when the hidden root window loses focus."""
        try:
            # Optional: could hide window when losing focus, but usually not desired
            pass
        except Exception:
            pass

    def _sync_window_state(self):
        """Synchronize the visible window state with the hidden root window state."""
        try:
            if not getattr(self, "_tk_root", None):
                return
            
            # Check if the root window is visible/mapped
            try:
                root_state = self._tk_root.state()
                if root_state == "normal" or root_state == "zoomed":
                    # Root is visible, ensure our window is too
                    if not self.root.winfo_viewable():
                        self.root.deiconify()
                        self.root.lift()
                elif root_state == "iconic":
                    # Root is minimized, hide our window
                    if self.root.winfo_viewable():
                        self.root.withdraw()
            except Exception:
                pass
        except Exception:
            pass

    def _schedule_state_sync(self):
        """Schedule periodic state synchronization for Windows hidden root setup."""
        try:
            self._sync_window_state()
            # Schedule the next sync in 100ms
            self.root.after(100, self._schedule_state_sync)
        except Exception:
            pass

    def _on_taskbar_click(self):
        """Handle taskbar icon clicks for more reliable window state management."""
        try:
            if not getattr(self, "_tk_root", None):
                return
            
            # Check current state and toggle accordingly
            try:
                root_state = self._tk_root.state()
                if root_state == "iconic":
                    # Window is minimized, restore it
                    self._tk_root.deiconify()
                else:
                    # Window is visible, minimize it
                    self._tk_root.iconify()
            except Exception:
                pass
        except Exception:
            pass

    def _raise_and_focus(self, event=None):
        """Bring the window to the front and give it focus.

        Uses a short topmost toggle which reliably forces many window managers
        to raise the window even when using custom chrome/overrideredirect.
        Also tries a Win32 SetForegroundWindow call on Windows as a best-effort.
        """
        try:
            # Try simple lift + focus first
            try:
                self.root.lift()
            except Exception:
                pass

            try:
                self.root.focus_force()
            except Exception:
                pass

            # Pulse topmost on supported platforms to ensure the window is above
            try:
                self.root.attributes("-topmost", True)
                try:
                    self.root.after(50, lambda: self.root.attributes("-topmost", False))
                except Exception:
                    try:
                        self.root.attributes("-topmost", False)
                    except Exception:
                        pass
            except Exception:
                pass

            # On Windows try a stronger foreground-set if normal raise/focus didn't succeed
            try:
                if sys.platform == "win32":
                    try:
                        hwnd = None
                        try:
                            hwnd = (
                                int(self._tk_root.winfo_id())
                                if getattr(self, "_tk_root", None)
                                else int(self.root.winfo_id())
                            )
                        except Exception:
                            hwnd = None
                        if hwnd:
                            try:
                                set_foreground_hwnd(hwnd)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def browse_log_file(self):
        """Browse for Star Citizen log file"""
        file_path = filedialog.askopenfilename(
            title=DIALOG_SELECT_LOG_TITLE,
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
        )
        if file_path:
            self.log_path_var.set(file_path)

    def auto_detect_log(self):
        """Auto-detect Star Citizen log file"""
        common_paths = COMMON_GAME_LOG_PATHS

        for path in common_paths:
            if os.path.exists(path):
                self.log_path_var.set(path)
                messagebox.showinfo(
                    MSG_AUTO_DETECT_TITLE, MSG_AUTO_DETECT_FOUND_FMT.format(path=path)
                )
                return

        messagebox.showwarning(MSG_AUTO_DETECT_TITLE, MSG_AUTO_DETECT_NOT_FOUND)

    def save_settings(self):
        """Save current settings with improved validation"""
        player_name = self.player_name_var.get().strip()
        log_file_path = self.log_path_var.get().strip()

        # Validate player name
        if not validate_player_name(player_name):
            messagebox.showerror(MSG_ERROR_TITLE, MSG_INVALID_PLAYER_NAME)
            return

        # Validate log file path
        if not self.validate_file_path(log_file_path):
            messagebox.showerror(MSG_ERROR_TITLE, MSG_INVALID_LOG_PATH)
            return

        # Update instance variables
        self.player_name = player_name
        self.log_file_path = log_file_path

        # Update config
        self.config["user"]["ingame_name"] = self.player_name
        self.config["user"]["log_path"] = self.log_file_path
        try:
            save_config(self.config, self.config_path)
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            messagebox.showerror(MSG_ERROR_TITLE, str(e))

        try:
            self.status_var.set(MSG_SETTINGS_SAVED)
        except Exception:
            pass

        # Auto-start monitoring now that settings are saved and validated.
        try:
            if (
                not self.is_monitoring
                and self.player_name
                and self.log_file_path
                and self.validate_file_path(self.log_file_path)
            ):
                try:
                    self.start_monitoring()
                    try:
                        self.status_var.set(STATUS_AUTO_STARTED)
                        self.safe_after(
                            5000, lambda: self.status_var.set(STATUS_MONITORING)
                        )
                    except Exception:
                        pass
                except Exception:
                    logger.debug(
                        "Failed to auto-start monitoring after save_settings",
                        exc_info=True,
                    )
        except Exception:
            logger.debug(
                "Error while attempting to auto-start after save_settings",
                exc_info=True,
            )

        try:
            messagebox.showinfo(MSG_SUCCESS_TITLE, MSG_SETTINGS_SAVED)
        except Exception:
            # In tests or headless environments messagebox may not be available;
            # swallow exceptions so saving settings does not crash the app.
            pass

    def toggle_monitoring(self):
        """Toggle kill feed monitoring"""
        if not self.player_name or not self.log_file_path:
            messagebox.showerror(MSG_ERROR_TITLE, MSG_CONFIGURE_FIRST)
            return

        if not self.validate_file_path(self.log_file_path):
            messagebox.showerror(MSG_ERROR_TITLE, MSG_LOG_NOT_FOUND)
            return

        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring the log file"""
        self.is_monitoring = True
        try:
            self.status_var.set("Monitoring started - Watching for kill events...")
        except Exception:
            pass

        # Start monitoring thread (use monitor_helpers.monitor_log_file directly)
        self.monitor_thread = threading.Thread(
            target=monitor_helpers.monitor_log_file, args=(self,), daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring the log file"""
        self.is_monitoring = False
        try:
            self.status_var.set("Monitoring stopped")
        except Exception:
            pass

    def display_kill_event(self, kill_data):
        """Display kill event in the feed"""
        timestamp = kill_data["timestamp"].strftime("%H:%M:%S")
        victim = kill_data["victim"]
        killer = kill_data["killer"]
        weapon = kill_data["weapon"]

        # Determine colors based on player involvement
        # Suicides
        if killer == victim:
            if killer == self.player_name:
                event_text = f"[{timestamp}] YOU died (suicide) using {weapon}\n"
                tags = ["player_death"]
            else:
                event_text = f"[{timestamp}] {killer} died (suicide) using {weapon}\n"
                tags = ["other_kill"]
        elif killer == self.player_name:
            event_text = f"[{timestamp}] YOU killed {victim} using {weapon}\n"
            tags = ["player_kill"]
        elif victim == self.player_name:
            event_text = f"[{timestamp}] {killer} killed YOU using {weapon}\n"
            tags = ["player_death"]
        else:
            event_text = f"[{timestamp}] {killer} killed {victim} using {weapon}\n"
            tags = ["other_kill"]

        # Insert into text widget
        self.kill_feed_text.insert(tk.END, event_text, tags)
        self.kill_feed_text.see(tk.END)

    def _append_kill_to_csv(self, kill_data: dict):
        """Append a single kill event to the automatic CSV log.

        The CSV file path is read from config user.auto_log_csv (relative paths
        are resolved next to the script). If the file doesn't exist, a header
        row is written first.
        """
        try:
            raw = (
                self.config["user"].get("auto_log_csv", DEFAULT_CSV_NAME)
                or DEFAULT_CSV_NAME
            )
            csv_path = resolve_auto_log_path(raw)
            append_kill_to_csv(csv_path, kill_data)
            logger.debug("Automatic CSV log path: %s", csv_path)
        except Exception:
            # Don't allow CSV logging failures to impact the app
            logger.debug("Automatic CSV append failed", exc_info=True)

    def update_statistics_display(self):
        """Update the statistics display with improved thread safety"""
        # Thread-safe data access with deep copy to prevent race conditions
        with self.data_lock:
            # Create deep copies to avoid holding lock during UI updates
            stats_copy = {
                "total_kills": self.stats["total_kills"],
                "total_deaths": self.stats["total_deaths"],
                "kill_streak": self.stats["kill_streak"],
                "death_streak": self.stats["death_streak"],
                "max_kill_streak": self.stats["max_kill_streak"],
                "max_death_streak": self.stats["max_death_streak"],
                "weapons_used": self.stats["weapons_used"].copy(),
                "weapons_against": self.stats["weapons_against"].copy(),
                "victims": self.stats["victims"].copy(),
                "killers": self.stats["killers"].copy(),
            }
            recent_kills = list(self.kills_data)[
                -RECENT_KILLS_COUNT:
            ]  # Convert deque to list for slicing

        # Update main stats
        self.kills_label.config(text=f"Kills: {stats_copy['total_kills']}")
        self.deaths_label.config(text=f"Deaths: {stats_copy['total_deaths']}")

        # Calculate K/D ratio
        if stats_copy["total_deaths"] > 0:
            kd_ratio = stats_copy["total_kills"] / stats_copy["total_deaths"]
        else:
            kd_ratio = stats_copy["total_kills"] if stats_copy["total_kills"] > 0 else 0

        self.kd_ratio_label.config(text=f"K/D Ratio: {kd_ratio:.2f}")

        # Current streak
        current_streak = (
            stats_copy["kill_streak"]
            if stats_copy["kill_streak"] > 0
            else -stats_copy["death_streak"]
        )
        self.streak_label.config(text=f"Current Streak: {current_streak}")

        # Update weapons tree
        self.weapons_tree.delete(*self.weapons_tree.get_children())
        for weapon, count in stats_copy["weapons_used"].most_common(RECENT_KILLS_COUNT):
            self.weapons_tree.insert("", "end", text=weapon, values=(count,))

        # Update recent activity
        self.recent_tree.delete(*self.recent_tree.get_children())
        for kill in recent_kills:  # Show last 10 events
            time_str = kill["timestamp"].strftime("%H:%M:%S")
            if kill["killer"] == kill["victim"]:
                if kill["killer"] == self.player_name:
                    event = f"You died (suicide) ({kill['weapon']})"
                else:
                    event = f"{kill['killer']} died (suicide) ({kill['weapon']})"
            elif kill["killer"] == self.player_name:
                event = f"You killed {kill['victim']} ({kill['weapon']})"
            elif kill["victim"] == self.player_name:
                event = f"{kill['killer']} killed you ({kill['weapon']})"
            else:
                event = f"{kill['killer']} killed {kill['victim']} ({kill['weapon']})"

            self.recent_tree.insert("", "end", values=(time_str, event))

    def debounced_update_statistics(self):
        """Debounced statistics update to prevent excessive UI updates with thread safety"""
        # Ensure lock and related state exist so methods can run without requiring __init__.
        if not hasattr(self, "_ui_update_lock"):
            self._ui_update_lock = threading.Lock()
        if not hasattr(self, "_pending_updates"):
            self._pending_updates = 0
        if not hasattr(self, "_update_timer"):
            self._update_timer = None
        if not hasattr(self, "_last_update_time"):
            self._last_update_time = 0

        with self._ui_update_lock:
            self._pending_updates += 1
            current_time = time.time()

            # Cancel previous timer if it exists
            if self._update_timer:
                try:
                    if hasattr(self.root, "after_cancel"):
                        self.root.after_cancel(self._update_timer)
                except AttributeError:
                    # For testing scenarios, just ignore the cancel
                    pass

            # Compute delay but do not schedule while holding the lock
            delay = max(50, 100 - int((current_time - self._last_update_time) * 1000))

        # Schedule the callback outside the lock to prevent deadlock when
        # `after` executes the callback immediately
        timer = self.safe_after(delay, self._perform_statistics_update)

        # Store the timer id (if any) under the lock
        try:
            with self._ui_update_lock:
                self._update_timer = timer
        except Exception:
            self._update_timer = timer

    def _perform_statistics_update(self):
        """Actually perform the statistics update with thread safety"""
        # Ensure lock and related state exist so methods can run without requiring __init__.
        if not hasattr(self, "_ui_update_lock"):
            self._ui_update_lock = threading.Lock()
        if not hasattr(self, "_pending_updates"):
            self._pending_updates = 0

        with self._ui_update_lock:
            if getattr(self, "_pending_updates", 0) > 0:
                self.update_statistics_display()
                self._pending_updates = 0
                self._last_update_time = time.time()
            self._update_timer = None

    def clear_kill_feed(self):
        """Clear the kill feed display"""
        self.kill_feed_text.delete(1.0, tk.END)
        self.kills_data.clear()  # deque.clear() works the same as list.clear()
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
        self.update_statistics_display()
        self.status_var.set("Kill feed cleared")

    def export_data(self):
        """Export kill data to file"""
        if not self.kills_data:
            messagebox.showwarning(MSG_WARNING_TITLE, MSG_NO_DATA_TO_EXPORT)
            return

        # Get export format
        formats = []
        if self.export_csv_var.get():
            formats.append("CSV")
        if self.export_json_var.get():
            formats.append("JSON")

        if not formats:
            messagebox.showerror(MSG_ERROR_TITLE, MSG_SELECT_EXPORT_FORMAT)
            return

        # Choose save location
        file_path = filedialog.asksaveasfilename(
            title=DIALOG_EXPORT_TITLE,
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            if "CSV" in formats and file_path.endswith(".csv"):
                export_helpers.export_csv(self.kills_data, file_path)
            elif "JSON" in formats and file_path.endswith(".json"):
                export_helpers.export_json(
                    self.kills_data, self.stats, self.player_name, file_path
                )
            else:
                # Export both formats
                base_path = os.path.splitext(file_path)[0]
                if "CSV" in formats:
                    export_helpers.export_csv(self.kills_data, f"{base_path}.csv")
                if "JSON" in formats:
                    export_helpers.export_json(
                        self.kills_data,
                        self.stats,
                        self.player_name,
                        f"{base_path}.json",
                    )

            self.export_status.config(text=f"Data exported successfully to {file_path}")
            messagebox.showinfo(MSG_SUCCESS_TITLE, MSG_EXPORT_SUCCESS)

        except FileNotFoundError as e:
            messagebox.showerror(
                MSG_ERROR_TITLE, MSG_EXPORT_DIR_NOT_FOUND_FMT.format(err=str(e))
            )
        except PermissionError as e:
            messagebox.showerror(
                MSG_ERROR_TITLE, MSG_EXPORT_PERMISSION_FMT.format(err=str(e))
            )
        except UnicodeEncodeError as e:
            messagebox.showerror(
                MSG_ERROR_TITLE, MSG_EXPORT_ENCODING_FMT.format(err=str(e))
            )
        except Exception as e:
            messagebox.showerror(
                MSG_ERROR_TITLE, MSG_EXPORT_FAILED_FMT.format(err=str(e))
            )

    def run(self):
        """Start the GUI application"""
        # Run the mainloop on the real Tk root if we created one, otherwise
        # fall back to the visible window's loop.
        try:
            if getattr(self, "_tk_root", None):
                self._tk_root.mainloop()
                return
        except Exception:
            pass
        try:
            self.root.mainloop()
        except Exception:
            # As a last resort, call mainloop on tk
            try:
                tk.mainloop()
            except Exception:
                pass


def main():
    """Main entry point"""
    app = StarCitizenKillFeedGUI()
    app.run()


if __name__ == "__main__":
    main()
