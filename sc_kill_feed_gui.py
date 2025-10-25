#!/usr/bin/env python3
"""
Star Citizen Kill Feed Tracker - GUI Version

A modern GUI application for tracking Star Citizen kill events
with real-time display, statistics, and data export capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import tkinter.font as tkfont
import os
import re
import sys
import time
import threading
import csv
from datetime import datetime
import configparser
from typing import Optional, Tuple, Dict, List
from collections import defaultdict, Counter, deque
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("sc_kill_feed.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

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
    DEBOUNCE_BASE_MS,
    DEBOUNCE_MIN_MS,
    DEFAULT_MAX_CONSECUTIVE_FILE_ERRORS,
    DEFAULT_MAX_LOG_FILE_SIZE_BYTES,
    MIN_STATISTICS_ENTRIES,
    MAX_STATISTICS_ENTRIES_LIMIT,
    MIN_MAX_LINES_PER_CHECK,
    MAX_MAX_LINES_PER_CHECK,
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
        self.root = tk.Tk()
        self.root.title("Star Citizen Kill Feed Tracker")
        self.root.geometry("1400x900")
        self.root.configure(bg="#0a0a0a")

        # Configuration and runtime state
        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_path()
        self.load_config()

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
        self.setup_styles()

        # Initialize scaling/font baselines and start timer loop
        try:
            self._init_scaling()
        except Exception:
            logger.debug("Failed to initialize font scaling baseline", exc_info=True)
        # Apply any configured GUI scale immediately
        try:
            self._apply_font_scaling()
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
                # Start monitoring in background
                try:
                    self.start_monitoring()
                    # Show a small auto-start status message, then revert to normal monitoring text
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
                self.save_config()
            except Exception:
                logger.debug("Failed to save gui_scale on close", exc_info=True)
        finally:
            try:
                self.root.destroy()
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
    def _init_scaling(self):
        """Capture baseline font sizes for named Tk fonts so scaling is predictable."""
        # Common Tk named fonts to attempt to scale
        font_names = [
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
        ]
        for name in font_names:
            try:
                f = tkfont.nametofont(name)
                self._base_font_sizes[name] = f.cget("size")
            except Exception:
                # Not all named fonts exist on all platforms/themes
                continue
        # Also capture fonts used directly by widgets (tuple fonts etc.)
        try:
            self._capture_widget_fonts(self.root)
        except Exception:
            logger.debug("Failed to capture widget fonts", exc_info=True)

        # Capture fonts and paddings used by ttk styles so tabs/buttons scale
        try:
            style = ttk.Style()
            # Common styles that define fonts/padding in this app
            style_names = [
                "TButton",
                "Success.TButton",
                "Danger.TButton",
                "Small.TButton",
                "Scale.TButton",
                "TNotebook.Tab",
                "TLabel",
                "Title.TLabel",
                "Subtitle.TLabel",
                "Treeview",
                "TEntry",
                "TLabelframe",
                "TLabelframe.Label",
            ]

            for name in style_names:
                try:
                    # Try to read font from style
                    font_spec = style.lookup(name, "font")
                    if font_spec:
                        try:
                            fobj = tkfont.Font(font=font_spec)
                            fname = fobj.name
                            if fname not in self._base_font_sizes:
                                try:
                                    base_size = int(fobj.cget("size"))
                                except Exception:
                                    base_size = 10
                                self._base_font_sizes[fname] = base_size
                                self._font_objects[fname] = fobj
                                # Assign font object back to style so widgets use it
                                try:
                                    style.configure(name, font=fobj)
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    # Capture padding if present
                    cfg = style.configure(name)
                    pad = cfg.get("padding") if isinstance(cfg, dict) else None
                    if pad:
                        # Normalize padding to tuple of ints
                        try:
                            if isinstance(pad, (list, tuple)):
                                base_pad = tuple(int(x) for x in pad)
                            else:
                                # single value
                                base_pad = (int(pad),)
                            self._base_style_paddings[name] = base_pad
                        except Exception:
                            # ignore padding parse errors
                            pass
                except Exception:
                    continue
        except Exception:
            logger.debug("Failed to capture ttk style fonts/paddings", exc_info=True)

    def _capture_widget_fonts(self, widget):
        """Recursively traverse widget tree and capture any font objects used.

        Stores base sizes in self._base_font_sizes keyed by font name, and
        keeps tkfont.Font objects in self._font_objects.
        """
        try:
            children = widget.winfo_children()
        except Exception:
            return

        for child in children:
            # Recurse first
            self._capture_widget_fonts(child)

            try:
                font_spec = child.cget("font")
            except Exception:
                continue

            if not font_spec:
                continue

            try:
                fobj = tkfont.Font(font=font_spec)
                fname = fobj.name
                if fname not in self._base_font_sizes:
                    # Some font sizes may be negative (pixels vs points); store absolute
                    base_size = fobj.cget("size")
                    try:
                        base_size = int(base_size)
                    except Exception:
                        # fallback if font returns empty or non-int
                        base_size = 10
                    self._base_font_sizes[fname] = base_size
                    # Try to assign this Font object back to the widget so
                    # future reconfiguration updates the widget appearance.
                    try:
                        child.configure(font=fobj)
                    except Exception:
                        # Some widgets may not accept direct font assignment
                        pass
                    self._font_objects[fname] = fobj
            except Exception:
                # ignore fonts we can't parse
                continue

    def _apply_font_scaling(self):
        """Apply the current gui_scale to captured named fonts and tk scaling."""
        try:
            # Set Tk's internal scaling (affects some widgets)
            try:
                self.root.tk.call("tk", "scaling", self.gui_scale)
            except Exception:
                pass

            # First, scale any captured font objects we've assigned to widgets
            for fname, fobj in list(self._font_objects.items()):
                try:
                    base_size = self._base_font_sizes.get(fname, fobj.cget("size"))
                    new_size = max(6, int(round(int(base_size) * self.gui_scale)))
                    fobj.configure(size=new_size)
                except Exception:
                    continue

            # Fallback: scale named fonts captured earlier (if any) that we didn't
            # capture as Font objects assigned to widgets.
            for name, base_size in self._base_font_sizes.items():
                if name in self._font_objects:
                    continue
                try:
                    f = tkfont.nametofont(name)
                    new_size = max(6, int(round(int(base_size) * self.gui_scale)))
                    f.configure(size=new_size)
                except Exception:
                    continue
        except Exception:
            logger.debug("Failed to apply font scaling", exc_info=True)

    def increase_scale(self):
        """Increase GUI scale by 0.1 (clamped)."""
        self.gui_scale = min(2.0, round(self.gui_scale + 0.1, 2))
        self._apply_font_scaling()
        # Persist scale
        try:
            self.config["user"]["gui_scale"] = str(self.gui_scale)
            self.save_config()
        except Exception:
            logger.debug("Failed to persist gui_scale on increase", exc_info=True)

    def decrease_scale(self):
        """Decrease GUI scale by 0.1 (clamped)."""
        self.gui_scale = max(0.5, round(self.gui_scale - 0.1, 2))
        self._apply_font_scaling()
        try:
            self.config["user"]["gui_scale"] = str(self.gui_scale)
            self.save_config()
        except Exception:
            logger.debug("Failed to persist gui_scale on decrease", exc_info=True)

    def reset_scale(self):
        """Reset GUI scale to 1.0"""
        self.gui_scale = 1.0
        self._apply_font_scaling()
        try:
            self.config["user"]["gui_scale"] = str(self.gui_scale)
            self.save_config()
        except Exception:
            logger.debug("Failed to persist gui_scale on reset", exc_info=True)

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
            if file_size > 100 * 1024 * 1024:  # 100MB
                logger.warning(
                    f"Log file is very large: {file_size / (1024*1024):.1f}MB"
                )

            logger.debug(f"File path validated successfully: {resolved_path}")
            return True

        except (OSError, ValueError) as e:
            logger.error(f"Error validating file path: {e}")
            return False

    def validate_player_name(self, player_name: str) -> bool:
        """Validate player name input"""
        if not player_name or not isinstance(player_name, str):
            logger.warning("Invalid player name: empty or not a string")
            return False

        # Sanitize input
        player_name = player_name.strip()

        # Check length
        if len(player_name) < 1 or len(player_name) > 50:
            logger.warning(f"Player name length invalid: {len(player_name)}")
            return False

        # Check for suspicious characters
        suspicious_chars = ["<", ">", "&", '"', "'", "\\", "/", "|", ";", "`", "$"]
        for char in suspicious_chars:
            if char in player_name:
                logger.warning(f"Suspicious character '{char}' found in player name")
                return False

        logger.debug(f"Player name validated successfully: {player_name}")
        return True

    def load_config(self):
        """Load configuration from file with validation and defaults"""
        if os.path.exists(self.config_path):
            try:
                self.config.read(self.config_path, encoding="utf-8")
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                self.config.clear()

        # Ensure required sections exist
        if "user" not in self.config:
            self.config["user"] = {}

        # Set default values if not present
        defaults = {
            "user": {
                "ingame_name": "",
                "log_path": "",
                "file_check_interval": "0.1",
                "max_lines_per_check": "100",
                "max_statistics_entries": "1000",
                "gui_scale": "1.0",
            }
        }

        for section, options in defaults.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in options.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
                    logger.debug(f"Set default value for {section}.{key}: {value}")

        # Validate and fix configuration values
        self.validate_config()

    def validate_config(self):
        """Validate configuration values and fix invalid ones"""
        try:
            # Validate file check interval
            try:
                interval = float(self.config["user"].get("file_check_interval", "0.1"))
                if interval < 0.01 or interval > 1.0:
                    logger.warning(
                        f"Invalid file_check_interval: {interval}, setting to default 0.1"
                    )
                    self.config["user"]["file_check_interval"] = "0.1"
                    self.FILE_CHECK_INTERVAL = 0.1
                else:
                    self.FILE_CHECK_INTERVAL = interval
            except ValueError:
                logger.warning(
                    "Invalid file_check_interval format, setting to default 0.1"
                )
                self.config["user"]["file_check_interval"] = "0.1"
                self.FILE_CHECK_INTERVAL = 0.1

            # Validate max lines per check
            try:
                max_lines = int(self.config["user"].get("max_lines_per_check", "100"))
                if max_lines < 1 or max_lines > 1000:
                    logger.warning(
                        f"Invalid max_lines_per_check: {max_lines}, setting to default 100"
                    )
                    self.config["user"]["max_lines_per_check"] = "100"
                    self.MAX_LINES_PER_CHECK = 100
                else:
                    self.MAX_LINES_PER_CHECK = max_lines
            except ValueError:
                logger.warning(
                    "Invalid max_lines_per_check format, setting to default 100"
                )
                self.config["user"]["max_lines_per_check"] = "100"
                self.MAX_LINES_PER_CHECK = 100

            # Validate max statistics entries
            try:
                max_stats = int(
                    self.config["user"].get("max_statistics_entries", "1000")
                )
                if max_stats < 100 or max_stats > 10000:
                    logger.warning(
                        f"Invalid max_statistics_entries: {max_stats}, setting to default 1000"
                    )
                    self.config["user"]["max_statistics_entries"] = "1000"
                    self.MAX_STATISTICS_ENTRIES = 1000
                else:
                    self.MAX_STATISTICS_ENTRIES = max_stats
            except ValueError:
                logger.warning(
                    "Invalid max_statistics_entries format, setting to default 1000"
                )
                self.config["user"]["max_statistics_entries"] = "1000"
                self.MAX_STATISTICS_ENTRIES = 1000

            # Validate GUI scale
            try:
                scale = float(self.config["user"].get("gui_scale", "1.0"))
                # Clamp reasonable bounds
                if scale < 0.5 or scale > 2.0:
                    logger.warning(
                        f"Invalid gui_scale: {scale}, setting to default 1.0"
                    )
                    self.config["user"]["gui_scale"] = "1.0"
                    self.gui_scale = 1.0
                else:
                    self.gui_scale = scale
            except ValueError:
                logger.warning("Invalid gui_scale format, setting to default 1.0")
                self.config["user"]["gui_scale"] = "1.0"
                self.gui_scale = 1.0

            logger.debug("Configuration validation completed")

        except Exception as e:
            logger.error(f"Error validating configuration: {e}", exc_info=True)

    def save_config(self):
        """Save configuration to file with error handling"""
        try:
            # Create directory if it doesn't exist
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_path, "w") as f:
                self.config.write(f)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}", exc_info=True)
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def setup_styles(self):
        """Setup modern dark theme styling with contemporary design"""
        style = ttk.Style()
        style.theme_use("clam")

        # Modern color palette
        colors = {
            "bg_primary": "#0a0a0a",  # Deep black
            "bg_secondary": "#0a0a0a",  # Dark gray
            "bg_tertiary": "#0a0a0a",  # Medium gray
            "accent_primary": "#00d4ff",  # Cyan blue
            "accent_secondary": "#ff6b35",  # Orange
            "accent_success": "#00ff88",  # Green
            "accent_danger": "#ff4757",  # Red
            "accent_warning": "#ffa502",  # Yellow
            "text_primary": "#ffffff",  # White
            "text_secondary": "#b0b0b0",  # Light gray
            "text_muted": "#808080",  # Medium gray
        }

        # Configure notebook styling
        style.configure("TNotebook", background=colors["bg_secondary"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            padding=[25, 15],
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", colors["accent_primary"]),
                ("active", colors["bg_tertiary"]),
            ],
        )

        # Configure frames
        style.configure("TFrame", background=colors["bg_secondary"])
        style.configure("Card.TFrame", background=colors["bg_tertiary"], relief="flat")

        # Configure labels
        style.configure(
            "TLabel",
            background=colors["bg_secondary"],
            foreground=colors["text_primary"],
        )
        style.configure(
            "Title.TLabel",
            background=colors["bg_secondary"],
            foreground=colors["accent_primary"],
            font=("Segoe UI", 24, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=colors["bg_secondary"],
            foreground=colors["text_secondary"],
            font=("Segoe UI", 12),
        )

        # Configure buttons with modern styling
        style.configure(
            "TButton",
            background=colors["accent_primary"],
            foreground=colors["bg_primary"],
            font=("Segoe UI", 10, "bold"),
            padding=[20, 10],
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("active", colors["accent_secondary"]),
                ("pressed", colors["accent_secondary"]),
            ],
        )

        # Configure success/danger buttons
        style.configure(
            "Success.TButton",
            background=colors["accent_success"],
            foreground=colors["bg_primary"],
        )
        style.map("Success.TButton", background=[("active", "#00cc6a")])

        style.configure(
            "Danger.TButton",
            background=colors["accent_danger"],
            foreground=colors["text_primary"],
        )
        style.map("Danger.TButton", background=[("active", "#ff3742")])

        # Small button style for compact controls (e.g., Start/Stop)
        # Increased default font size by ~25% (9 -> 11)
        style.configure(
            "Small.TButton",
            background=colors["accent_primary"],
            foreground=colors["bg_primary"],
            font=("Segoe UI", 11, "bold"),
            padding=[8, 6],
            relief="flat",
        )
        style.map(
            "Small.TButton",
            background=[
                ("active", colors["accent_secondary"]),
                ("pressed", colors["accent_secondary"]),
            ],
        )

        # Scale control button style: small, grey text on black background
        # Increased font size by ~25% (9 -> 11)
        style.configure(
            "Scale.TButton",
            background=colors["bg_primary"],
            foreground="#b0b0b0",
            font=("Segoe UI", 11),
            padding=[6, 4],
            relief="flat",
        )
        style.map(
            "Scale.TButton", background=[("active", "#111111"), ("pressed", "#222222")]
        )

        # Configure treeview with modern styling
        style.configure(
            "Treeview",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            fieldbackground=colors["bg_tertiary"],
            font=("Segoe UI", 9),
        )
        style.map("Treeview", background=[("selected", colors["accent_primary"])])

        # Configure entry fields
        style.configure(
            "TEntry",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            fieldbackground=colors["bg_tertiary"],
            font=("Segoe UI", 10),
            padding=[10, 8],
        )
        style.configure(
            "TCombobox",
            background=colors["bg_tertiary"],
            foreground=colors["text_primary"],
            fieldbackground=colors["bg_tertiary"],
        )

        # Configure label frames
        style.configure(
            "TLabelframe",
            background=colors["bg_secondary"],
            foreground=colors["text_primary"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "TLabelframe.Label",
            background=colors["bg_secondary"],
            foreground=colors["accent_primary"],
            font=("Segoe UI", 11, "bold"),
        )

    def setup_ui(self):
        """Setup the main user interface with modern design"""
        # Main container with padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.create_kill_feed_tab()
        self.create_statistics_tab()
        self.create_settings_tab()
        self.create_export_tab()

        # Modern status bar
        status_frame = ttk.Frame(main_frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(15, 0))

        # Left side: status message
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Configure settings to start monitoring")
        # Status text should be larger by default (twice size at 100% scale)
        status_bar_left = tk.Label(
            status_frame,
            textvariable=self.status_var,
            bg="#0a0a0a",
            fg="#b0b0b0",
            anchor="w",
            font=("Segoe UI", 12),
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
            text="Time since last kill/death:",
            bg="#0a0a0a",
            fg="#b0b0b0",
            font=("Segoe UI", 12),
        )
        timer_caption.pack(side=tk.LEFT, padx=(0, 8))

        timer_label = tk.Label(
            timer_container,
            textvariable=self.timer_var,
            bg="#0a0a0a",
            fg="#b0b0b0",
            anchor="e",
            font=("Segoe UI", 12),
        )
        timer_label.pack(side=tk.LEFT)

    def create_kill_feed_tab(self):
        """Create the real-time kill feed tab with modern design"""
        kill_feed_frame = ttk.Frame(self.notebook)
        self.notebook.add(kill_feed_frame, text="🎯 Kill Feed")

        # Control panel with modern card design
        control_frame = ttk.Frame(kill_feed_frame, style="Card.TFrame")
        control_frame.pack(fill=tk.X, padx=15, pady=15)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=15, pady=15)

        # Scale controls (centered) - allow user to scale the entire GUI
        scale_frame = ttk.Frame(control_frame)
        scale_frame.pack(side=tk.LEFT, expand=True)

        # Label for scale controls
        scale_label = tk.Label(
            scale_frame,
            text="Scale UI",
            bg="#0a0a0a",
            fg="#ffffff",
            font=("Segoe UI", 10),
        )
        scale_label.pack(side=tk.TOP, pady=(4, 6))

        btn_row = ttk.Frame(scale_frame)
        btn_row.pack(side=tk.TOP)

        dec_btn = ttk.Button(
            btn_row, text="A-", command=self.decrease_scale, style="Scale.TButton"
        )
        dec_btn.pack(side=tk.LEFT, padx=6)
        reset_btn = ttk.Button(
            btn_row, text="Reset", command=self.reset_scale, style="Scale.TButton"
        )
        reset_btn.pack(side=tk.LEFT, padx=6)
        inc_btn = ttk.Button(
            btn_row, text="A+", command=self.increase_scale, style="Scale.TButton"
        )
        inc_btn.pack(side=tk.LEFT, padx=6)

        # Player info intentionally omitted from Kill Feed tab (kept in Settings)

        # Kill feed display with modern styling
        feed_frame = ttk.Frame(kill_feed_frame, style="Card.TFrame")
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Feed header
        feed_header = tk.Label(
            feed_frame,
            text="📊 Live Combat Feed",
            bg="#2a2a2a",
            fg="#00d4ff",
            font=("Segoe UI", 12, "bold"),
            pady=10,
        )
        feed_header.pack(fill=tk.X)

        self.kill_feed_text = scrolledtext.ScrolledText(
            feed_frame,
            bg="#1a1a1a",
            fg="#ffffff",
            font=("Consolas", 11),
            wrap=tk.WORD,
            padx=15,
            pady=10,
            insertbackground="#00d4ff",
            selectbackground="#00d4ff",
            selectforeground="#1a1a1a",
        )
        self.kill_feed_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create and register Font objects for the kill-feed text and tags so they scale
        try:
            # Base kill feed font
            self.kill_feed_font = tkfont.Font(font=self.kill_feed_text.cget("font"))
            self.kill_feed_text.configure(font=self.kill_feed_font)
            self._font_objects[self.kill_feed_font.name] = self.kill_feed_font
            try:
                self._base_font_sizes[self.kill_feed_font.name] = int(
                    self.kill_feed_font.cget("size")
                )
            except Exception:
                self._base_font_sizes[self.kill_feed_font.name] = 11

            # Tag fonts (player_kill, player_death, weapon, timestamp)
            self.kill_feed_tag_fonts = {}

            fk = tkfont.Font(family="Consolas", size=11, weight="bold")
            self.kill_feed_tag_fonts["player_kill"] = fk
            self.kill_feed_text.tag_configure(
                "player_kill", foreground="#00ff88", font=fk
            )
            self._font_objects[fk.name] = fk
            self._base_font_sizes[fk.name] = 11

            fd = tkfont.Font(family="Consolas", size=11, weight="bold")
            self.kill_feed_tag_fonts["player_death"] = fd
            self.kill_feed_text.tag_configure(
                "player_death", foreground="#ff4757", font=fd
            )
            self._font_objects[fd.name] = fd
            self._base_font_sizes[fd.name] = 11

            fw = tkfont.Font(family="Consolas", size=11, slant="italic")
            self.kill_feed_tag_fonts["weapon"] = fw
            self.kill_feed_text.tag_configure("weapon", foreground="#00d4ff", font=fw)
            self._font_objects[fw.name] = fw
            self._base_font_sizes[fw.name] = 11

            ft = tkfont.Font(family="Consolas", size=10)
            self.kill_feed_tag_fonts["timestamp"] = ft
            self.kill_feed_text.tag_configure(
                "timestamp", foreground="#808080", font=ft
            )
            self._font_objects[ft.name] = ft
            self._base_font_sizes[ft.name] = 10

            # Other tag without font
            self.kill_feed_text.tag_configure("other_kill", foreground="#b0b0b0")
        except Exception:
            self.kill_feed_text.tag_configure("player_kill", foreground="#00ff88")
            self.kill_feed_text.tag_configure("player_death", foreground="#ff4757")
            self.kill_feed_text.tag_configure("other_kill", foreground="#b0b0b0")
            self.kill_feed_text.tag_configure("weapon", foreground="#00d4ff")
            self.kill_feed_text.tag_configure("timestamp", foreground="#808080")

    def create_statistics_tab(self):
        """Create the statistics dashboard tab with modern design"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📈 Statistics")

        # Main stats grid with modern layout
        main_stats_frame = ttk.Frame(stats_frame)
        main_stats_frame.pack(fill=tk.X, padx=15, pady=15)

        # K/D Ratio and Streaks with modern card design
        kd_frame = ttk.LabelFrame(
            main_stats_frame, text="⚔️ Combat Statistics", style="TLabelframe"
        )
        kd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Stats container with better spacing
        stats_container = ttk.Frame(kd_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.kills_label = tk.Label(
            stats_container,
            text="💀 Kills: 0",
            bg="#0a0a0a",
            fg="#00ff88",
            font=("Segoe UI", 16, "bold"),
            pady=8,
        )
        self.kills_label.pack(fill=tk.X, pady=5)

        self.deaths_label = tk.Label(
            stats_container,
            text="💀 Deaths: 0",
            bg="#0a0a0a",
            fg="#ff4757",
            font=("Segoe UI", 16, "bold"),
            pady=8,
        )
        self.deaths_label.pack(fill=tk.X, pady=5)

        self.kd_ratio_label = tk.Label(
            stats_container,
            text="📊 K/D Ratio: 0.00",
            bg="#0a0a0a",
            fg="#00d4ff",
            font=("Segoe UI", 14, "bold"),
            pady=8,
        )
        self.kd_ratio_label.pack(fill=tk.X, pady=5)

        self.streak_label = tk.Label(
            stats_container,
            text="🔥 Current Streak: 0",
            bg="#0a0a0a",
            fg="#ffa502",
            font=("Segoe UI", 14, "bold"),
            pady=8,
        )
        self.streak_label.pack(fill=tk.X, pady=5)

        # Weapons stats with modern design
        weapons_frame = ttk.LabelFrame(
            main_stats_frame, text="🔫 Weapon Statistics", style="TLabelframe"
        )
        weapons_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.weapons_tree = ttk.Treeview(
            weapons_frame, columns=("count",), show="tree headings", height=8
        )
        self.weapons_tree.heading("#0", text="Weapon")
        self.weapons_tree.heading("count", text="Kills")
        self.weapons_tree.column("#0", width=200)
        self.weapons_tree.column("count", width=80)
        self.weapons_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Recent activity with modern design
        recent_frame = ttk.LabelFrame(
            stats_frame, text="📋 Recent Activity", style="TLabelframe"
        )
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.recent_tree = ttk.Treeview(
            recent_frame, columns=("time", "event"), show="headings", height=10
        )
        self.recent_tree.heading("time", text="Time")
        self.recent_tree.heading("event", text="Event")
        self.recent_tree.column("time", width=100)
        self.recent_tree.column("event", width=400)
        self.recent_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    def create_settings_tab(self):
        """Create the settings configuration tab with modern design"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")

        # Player name setting with modern design
        name_frame = ttk.LabelFrame(
            settings_frame, text="👤 Player Configuration", style="TLabelframe"
        )
        name_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            name_frame,
            text="Your In-Game Name:",
            bg="#0a0a0a",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))
        self.player_name_var = tk.StringVar(value=self.player_name)
        player_entry = ttk.Entry(
            name_frame, textvariable=self.player_name_var, width=50
        )
        player_entry.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Log file setting with modern design
        log_frame = ttk.LabelFrame(
            settings_frame, text="📁 Log File Configuration", style="TLabelframe"
        )
        log_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            log_frame,
            text="Star Citizen Game.log Path:",
            bg="#0a0a0a",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))

        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        self.log_path_var = tk.StringVar(value=self.log_file_path)
        log_entry = ttk.Entry(log_path_frame, textvariable=self.log_path_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_button = ttk.Button(
            log_path_frame, text="🔍 Browse", command=self.browse_log_file
        )
        browse_button.pack(side=tk.RIGHT)

        # Auto-detect button with modern styling
        auto_detect_button = ttk.Button(
            log_frame,
            text="🔍 Auto-detect Game.log",
            command=self.auto_detect_log,
            style="TButton",
        )
        auto_detect_button.pack(pady=15)

        # Save settings button with modern styling
        save_button = ttk.Button(
            settings_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            style="Success.TButton",
        )
        save_button.pack(pady=25)

    def create_export_tab(self):
        """Create the data export tab with modern design"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="📤 Export Data")

        # Export options with modern design
        options_frame = ttk.LabelFrame(
            export_frame, text="📋 Export Options", style="TLabelframe"
        )
        options_frame.pack(fill=tk.X, padx=15, pady=15)

        self.export_csv_var = tk.BooleanVar(value=True)
        csv_check = ttk.Checkbutton(
            options_frame, text="📊 Export as CSV", variable=self.export_csv_var
        )
        csv_check.pack(anchor="w", padx=15, pady=10)

        self.export_json_var = tk.BooleanVar(value=False)
        json_check = ttk.Checkbutton(
            options_frame, text="📄 Export as JSON", variable=self.export_json_var
        )
        json_check.pack(anchor="w", padx=15, pady=10)

        # Export button with modern styling
        export_button = ttk.Button(
            export_frame,
            text="📤 Export Data",
            command=self.export_data,
            style="Success.TButton",
        )
        export_button.pack(pady=25)

        # Export status with modern styling
        self.export_status = tk.Label(
            export_frame,
            text="",
            bg="#0a0a0a",
            fg="#0a0a0a",
            font=("Segoe UI", 10),
            pady=10,
        )
        self.export_status.pack(pady=15)

    def browse_log_file(self):
        """Browse for Star Citizen log file"""
        file_path = filedialog.askopenfilename(
            title="Select Star Citizen Game.log",
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
                messagebox.showinfo("Auto-detect", f"Found Game.log at:\n{path}")
                return

        messagebox.showwarning(
            "Auto-detect",
            "Could not auto-detect Game.log file.\nPlease browse manually.",
        )

    def save_settings(self):
        """Save current settings with improved validation"""
        player_name = self.player_name_var.get().strip()
        log_file_path = self.log_path_var.get().strip()

        # Validate player name
        if not self.validate_player_name(player_name):
            messagebox.showerror(
                "Error",
                "Please enter a valid in-game name (1-50 characters, no special characters).",
            )
            return

        # Validate log file path
        if not self.validate_file_path(log_file_path):
            messagebox.showerror(
                "Error",
                "Please select a valid Game.log file. The file must exist and be a .log file.",
            )
            return

        # Update instance variables
        self.player_name = player_name
        self.log_file_path = log_file_path

        # Update config
        self.config["user"]["ingame_name"] = self.player_name
        self.config["user"]["log_path"] = self.log_file_path
        self.save_config()

        try:
            self.status_var.set("Settings saved successfully")
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
                        self.status_var.set("Auto-started monitoring")
                        self.safe_after(
                            5000,
                            lambda: self.status_var.set(
                                "Monitoring started - Watching for kill events..."
                            ),
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

        messagebox.showinfo("Success", "Settings saved successfully!")

    def toggle_monitoring(self):
        """Toggle kill feed monitoring"""
        if not self.player_name or not self.log_file_path:
            messagebox.showerror("Error", "Please configure your settings first.")
            return

        if not self.validate_file_path(self.log_file_path):
            messagebox.showerror(
                "Error", "Game.log file not found or invalid. Please check the path."
            )
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

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self.monitor_log_file, daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop monitoring the log file"""
        self.is_monitoring = False
        try:
            self.status_var.set("Monitoring stopped")
        except Exception:
            pass

    def monitor_log_file(self):
        """Monitor the log file for kill events with improved performance and error recovery"""
        logger.info(f"Starting log file monitoring: {self.log_file_path}")

        try:
            with open(
                self.log_file_path,
                "r",
                encoding="utf-8",
                errors="ignore",
                buffering=self.READ_BUFFER_SIZE,
            ) as f:
                f.seek(0, os.SEEK_END)
                last_position = f.tell()
                consecutive_errors = 0
                max_consecutive_errors = 5

                while self.is_monitoring:
                    try:
                        # Check if file has grown. Use file size from the filesystem
                        # instead of the file object's tell() which doesn't change
                        # when another process appends to the file.
                        try:
                            current_size = os.path.getsize(self.log_file_path)
                        except OSError:
                            # If file was removed/rotated between checks, treat as truncated
                            current_size = 0

                        if current_size < last_position:
                            # File was truncated or rotated, reset to end
                            logger.info(
                                "Log file was truncated or rotated, resetting to end"
                            )
                            f.seek(0, os.SEEK_END)
                            last_position = f.tell()
                        elif current_size > last_position:
                            # File has new content, read it efficiently
                            f.seek(last_position)
                            lines_read = 0
                            lines_buffer = []

                            # Read multiple lines at once for better performance
                            while (
                                lines_read < self.MAX_LINES_PER_CHECK
                                and self.is_monitoring
                            ):
                                line = f.readline()
                                if not line:
                                    break

                                lines_buffer.append(line)
                                lines_read += 1

                            # Process all buffered lines
                            for line in lines_buffer:
                                if "<Actor Death>" in line:
                                    self.process_kill_event(line.strip())

                            last_position = f.tell()
                            consecutive_errors = 0  # Reset error counter on success
                        else:
                            # No new content, sleep briefly
                            time.sleep(self.FILE_CHECK_INTERVAL)

                    except (OSError, IOError) as e:
                        consecutive_errors += 1
                        logger.warning(
                            f"File access error (attempt {consecutive_errors}): {e}"
                        )

                        if consecutive_errors >= max_consecutive_errors:
                            logger.error(
                                f"Too many consecutive file access errors, stopping monitoring"
                            )
                            self.safe_after(
                                0,
                                lambda: self.status_var.set(
                                    f"Too many file access errors, monitoring stopped"
                                ),
                            )
                            break

                        # Wait longer before retrying
                        time.sleep(self.FILE_CHECK_INTERVAL * 5)

        except FileNotFoundError as e:
            error_msg = f"Log file not found: {str(e)}"
            logger.error(error_msg)
            self.safe_after(0, lambda: self.status_var.set(error_msg))
        except PermissionError as e:
            error_msg = f"Permission denied accessing log file: {str(e)}"
            logger.error(error_msg)
            self.safe_after(0, lambda: self.status_var.set(error_msg))
        except UnicodeDecodeError as e:
            error_msg = f"Error reading log file encoding: {str(e)}"
            logger.error(error_msg)
            self.safe_after(0, lambda: self.status_var.set(error_msg))
        except Exception as e:
            error_msg = f"Unexpected error monitoring file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.safe_after(0, lambda: self.status_var.set(error_msg))
        finally:
            logger.info("Log file monitoring stopped")

    def limit_statistics_size(self):
        """Limit the size of statistics counters to prevent memory leaks"""
        try:
            # Limit weapons_used counter
            if len(self.stats["weapons_used"]) > self.MAX_STATISTICS_ENTRIES:
                # Keep only the most common weapons
                most_common = self.stats["weapons_used"].most_common(
                    self.MAX_STATISTICS_ENTRIES
                )
                self.stats["weapons_used"].clear()
                for weapon, count in most_common:
                    self.stats["weapons_used"][weapon] = count

            # Limit weapons_against counter
            if len(self.stats["weapons_against"]) > self.MAX_STATISTICS_ENTRIES:
                most_common = self.stats["weapons_against"].most_common(
                    self.MAX_STATISTICS_ENTRIES
                )
                self.stats["weapons_against"].clear()
                for weapon, count in most_common:
                    self.stats["weapons_against"][weapon] = count

            # Limit victims counter
            if len(self.stats["victims"]) > self.MAX_STATISTICS_ENTRIES:
                most_common = self.stats["victims"].most_common(
                    self.MAX_STATISTICS_ENTRIES
                )
                self.stats["victims"].clear()
                for victim, count in most_common:
                    self.stats["victims"][victim] = count

            # Limit killers counter
            if len(self.stats["killers"]) > self.MAX_STATISTICS_ENTRIES:
                most_common = self.stats["killers"].most_common(
                    self.MAX_STATISTICS_ENTRIES
                )
                self.stats["killers"].clear()
                for killer, count in most_common:
                    self.stats["killers"][killer] = count

            logger.debug("Statistics counters size limited to prevent memory leaks")

        except Exception as e:
            logger.error(f"Error limiting statistics size: {e}", exc_info=True)

    def process_kill_event(self, line: str):
        """Process a kill event line with improved error handling"""
        try:
            match = self.KILL_LINE_RE.search(line)
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
                self.last_kill_time = timestamp
                # Update timer immediately on main thread
                try:
                    self.safe_after(0, lambda: self.timer_var.set("0:00:00"))
                except Exception:
                    # If timer_var not yet available, ignore
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
            with self.data_lock:
                self.kills_data.append(kill_data)
                self.update_statistics(kill_data)

            # Update UI in main thread with debouncing and thread safety
            self.safe_after_idle(lambda: self.display_kill_event(kill_data))
            self.debounced_update_statistics()

            logger.debug(
                f"Processed kill event: {killer} killed {victim} with {weapon}"
            )

        except Exception as e:
            logger.error(
                f"Error processing kill event line: {line[:100]}... Error: {e}",
                exc_info=True,
            )

    def update_statistics(self, kill_data):
        """Update statistics based on kill data"""
        victim = kill_data["victim"]
        killer = kill_data["killer"]
        weapon = kill_data["weapon"]

        # Update counters
        self.stats["weapons_used"][weapon] += 1
        self.stats["weapons_against"][weapon] += 1
        self.stats["victims"][victim] += 1
        self.stats["killers"][killer] += 1

        # Periodically limit statistics size to prevent memory leaks
        total_entries = (
            len(self.stats["weapons_used"])
            + len(self.stats["weapons_against"])
            + len(self.stats["victims"])
            + len(self.stats["killers"])
        )
        if total_entries % 100 == 0:  # Check every 100 entries
            self.limit_statistics_size()

        # Handle suicides first
        if killer == victim:
            if killer == self.player_name:
                # Player suicide counts as a death for the player
                self.stats["total_deaths"] += 1
                self.stats["death_streak"] += 1
                self.stats["kill_streak"] = 0
                self.stats["max_death_streak"] = max(
                    self.stats["max_death_streak"], self.stats["death_streak"]
                )
            # For non-player suicides, do not affect player's kill/death counts
            return

        # Check if player was involved (non-suicide)
        if killer == self.player_name:
            self.stats["total_kills"] += 1
            self.stats["kill_streak"] += 1
            self.stats["death_streak"] = 0
            self.stats["max_kill_streak"] = max(
                self.stats["max_kill_streak"], self.stats["kill_streak"]
            )
        elif victim == self.player_name:
            self.stats["total_deaths"] += 1
            self.stats["death_streak"] += 1
            self.stats["kill_streak"] = 0
            self.stats["max_death_streak"] = max(
                self.stats["max_death_streak"], self.stats["death_streak"]
            )

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

    # Update statistics display

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
                -10:
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
        for weapon, count in stats_copy["weapons_used"].most_common(10):
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
            messagebox.showwarning("Warning", "No data to export.")
            return

        # Get export format
        formats = []
        if self.export_csv_var.get():
            formats.append("CSV")
        if self.export_json_var.get():
            formats.append("JSON")

        if not formats:
            messagebox.showerror("Error", "Please select at least one export format.")
            return

        # Choose save location
        file_path = filedialog.asksaveasfilename(
            title="Export Kill Data",
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
                self.export_csv(file_path)
            elif "JSON" in formats and file_path.endswith(".json"):
                self.export_json(file_path)
            else:
                # Export both formats
                base_path = os.path.splitext(file_path)[0]
                if "CSV" in formats:
                    self.export_csv(f"{base_path}.csv")
                if "JSON" in formats:
                    self.export_json(f"{base_path}.json")

            self.export_status.config(text=f"Data exported successfully to {file_path}")
            messagebox.showinfo("Success", "Data exported successfully!")

        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Export directory not found: {str(e)}")
        except PermissionError as e:
            messagebox.showerror(
                "Error", f"Permission denied writing export file: {str(e)}"
            )
        except UnicodeEncodeError as e:
            messagebox.showerror("Error", f"Error encoding export data: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def export_csv(self, file_path):
        """Export data as CSV"""
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "killer", "victim", "weapon"])
            for kill in self.kills_data:
                writer.writerow(
                    [
                        kill["timestamp"].isoformat(),
                        kill["killer"],
                        kill["victim"],
                        kill["weapon"],
                    ]
                )

    def export_json(self, file_path):
        """Export data as JSON"""
        data = {
            "player_name": self.player_name,
            "export_time": datetime.now().isoformat(),
            "statistics": {
                "total_kills": self.stats["total_kills"],
                "total_deaths": self.stats["total_deaths"],
                "kill_death_ratio": self.stats["total_kills"]
                / max(self.stats["total_deaths"], 1),
                "max_kill_streak": self.stats["max_kill_streak"],
                "max_death_streak": self.stats["max_death_streak"],
            },
            "kill_events": [
                {
                    "timestamp": kill["timestamp"].isoformat(),
                    "killer": kill["killer"],
                    "victim": kill["victim"],
                    "weapon": kill["weapon"],
                }
                for kill in self.kills_data
            ],
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = StarCitizenKillFeedGUI()
    app.run()


if __name__ == "__main__":
    main()
