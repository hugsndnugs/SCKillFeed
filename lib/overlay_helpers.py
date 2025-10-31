"""Kill Tracker Overlay - A real-time transparent overlay for tracking kills, deaths, K/D, and streaks.

This module provides a sleek, always-on-top overlay window that displays game statistics
in real-time. Designed for streamers and competitive players with customizable themes
and minimal performance impact.
"""

import tkinter as tk
from tkinter import font
import logging
import sys
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# Theme definitions
OVERLAY_THEMES = {
    "dark": {
        "bg": "#0a0a0a",
        "fg": "#ffffff",
        "accent_kill": "#00ff88",
        "accent_death": "#ff4757",
        "accent_kd": "#00d4ff",
        "accent_streak": "#ffa502",
        "border": "#1a1a1a",
        "alpha": 0.92,
    },
    "light": {
        "bg": "#ffffff",
        "fg": "#1a1a1a",
        "accent_kill": "#00aa55",
        "accent_death": "#cc3333",
        "accent_kd": "#0088cc",
        "accent_streak": "#ff8800",
        "border": "#e0e0e0",
        "alpha": 0.95,
    },
    "neon": {
        "bg": "#000011",
        "fg": "#00ffff",
        "accent_kill": "#00ff00",
        "accent_death": "#ff0066",
        "accent_kd": "#6600ff",
        "accent_streak": "#ffff00",
        "border": "#003333",
        "alpha": 0.88,
    },
    "minimal": {
        "bg": "#1a1a1a",
        "fg": "#cccccc",
        "accent_kill": "#88ff88",
        "accent_death": "#ff8888",
        "accent_kd": "#88ccff",
        "accent_streak": "#ffcc88",
        "border": "#333333",
        "alpha": 0.85,
    },
}


class KillTrackerOverlay:
    """A transparent, always-on-top overlay window for displaying kill statistics."""

    def __init__(self, gui, theme: str = "dark", position: Tuple[int, int] = (50, 50)):
        """Initialize the overlay window.

        Args:
            gui: The main GUI instance that holds statistics
            theme: Theme name (dark, light, neon, minimal)
            position: Initial position (x, y) on screen
        """
        self.gui = gui
        self.theme_name = theme
        self.theme = OVERLAY_THEMES.get(theme, OVERLAY_THEMES["dark"])
        self.position = position
        self.is_visible = False
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._win_start_x = 0
        self._win_start_y = 0
        self._dragging = False
        self._custom_opacity = None  # User-set opacity override
        self._locked = False  # Lock state to prevent dragging

        # Create overlay window
        self.root = tk.Toplevel()
        self.root.title("Kill Tracker Overlay")
        self.root.withdraw()  # Start hidden

        # Configure window properties for overlay
        self._setup_overlay_window()

        # Create UI
        self._create_ui()

        # Update position and size (compact size for overlay)
        self.root.geometry(f"180x150+{position[0]}+{position[1]}")
        # Make sure window doesn't resize
        self.root.resizable(False, False)

    def _setup_overlay_window(self):
        """Configure window to be transparent, always-on-top, and borderless."""
        try:
            # Remove window decorations
            self.root.overrideredirect(True)

            # Always on top
            self.root.attributes("-topmost", True)

            # Set transparency
            alpha = self.theme.get("alpha", 0.92)
            try:
                self.root.attributes("-alpha", alpha)
            except Exception:
                logger.debug("Alpha transparency not supported, using opaque window")

            # Make window background transparent (on Windows)
            if sys.platform == "win32":
                try:
                    # Use a specific color as transparent
                    self.root.config(bg=self.theme["bg"])
                    # Note: -transparentcolor requires careful color matching
                except Exception:
                    pass

            # Disable focus stealing (click-through on some platforms)
            # Note: Full click-through requires platform-specific APIs
            try:
                self.root.attributes("-disabled", False)
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"Error setting up overlay window: {e}", exc_info=True)

    def _create_ui(self):
        """Create the overlay UI elements."""
        # Main container with padding and rounded appearance
        main_frame = tk.Frame(
            self.root,
            bg=self.theme["bg"],
            highlightbackground=self.theme["border"],
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title/header (shows it's draggable, with lock indicator)
        lock_icon = "🔒" if self._locked else "🔓"
        header = tk.Label(
            main_frame,
            text=f"{lock_icon} ⚔ KILL TRACKER",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 7, "bold"),
            pady=1,
        )
        header.pack()

        # Separator
        separator = tk.Frame(
            main_frame, bg=self.theme["border"], height=1, pady=2
        )
        separator.pack(fill=tk.X, pady=1)

        # Stats container
        stats_container = tk.Frame(main_frame, bg=self.theme["bg"])
        stats_container.pack(fill=tk.BOTH, expand=True)

        # Kills
        kills_frame = tk.Frame(stats_container, bg=self.theme["bg"])
        kills_frame.pack(fill=tk.X, pady=1)

        tk.Label(
            kills_frame,
            text="Kills:",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 8),
            anchor="w",
            width=8,
        ).pack(side=tk.LEFT)

        self.kills_label = tk.Label(
            kills_frame,
            text="0",
            bg=self.theme["bg"],
            fg=self.theme["accent_kill"],
            font=("Segoe UI", 10, "bold"),
            width=6,
            anchor="e",
        )
        self.kills_label.pack(side=tk.RIGHT)

        # Deaths
        deaths_frame = tk.Frame(stats_container, bg=self.theme["bg"])
        deaths_frame.pack(fill=tk.X, pady=1)

        tk.Label(
            deaths_frame,
            text="Deaths:",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 8),
            anchor="w",
            width=8,
        ).pack(side=tk.LEFT)

        self.deaths_label = tk.Label(
            deaths_frame,
            text="0",
            bg=self.theme["bg"],
            fg=self.theme["accent_death"],
            font=("Segoe UI", 10, "bold"),
            width=6,
            anchor="e",
        )
        self.deaths_label.pack(side=tk.RIGHT)

        # K/D Ratio
        kd_frame = tk.Frame(stats_container, bg=self.theme["bg"])
        kd_frame.pack(fill=tk.X, pady=1)

        tk.Label(
            kd_frame,
            text="K/D:",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 8),
            anchor="w",
            width=8,
        ).pack(side=tk.LEFT)

        self.kd_label = tk.Label(
            kd_frame,
            text="0.00",
            bg=self.theme["bg"],
            fg=self.theme["accent_kd"],
            font=("Segoe UI", 10, "bold"),
            width=6,
            anchor="e",
        )
        self.kd_label.pack(side=tk.RIGHT)

        # Streak
        streak_frame = tk.Frame(stats_container, bg=self.theme["bg"])
        streak_frame.pack(fill=tk.X, pady=1)

        tk.Label(
            streak_frame,
            text="Streak:",
            bg=self.theme["bg"],
            fg=self.theme["fg"],
            font=("Segoe UI", 8),
            anchor="w",
            width=8,
        ).pack(side=tk.LEFT)

        self.streak_label = tk.Label(
            streak_frame,
            text="0",
            bg=self.theme["bg"],
            fg=self.theme["accent_streak"],
            font=("Segoe UI", 10, "bold"),
            width=6,
            anchor="e",
        )
        self.streak_label.pack(side=tk.RIGHT)

        # Make entire window draggable
        self._setup_dragging()

    def _setup_dragging(self):
        """Make the overlay window draggable by clicking anywhere, unless locked."""
        def start_drag(event):
            # Don't allow dragging if locked
            if self._locked:
                return
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
            try:
                self._win_start_x = self.root.winfo_x()
                self._win_start_y = self.root.winfo_y()
            except Exception:
                pass
            self._dragging = True

        def on_drag(event):
            # Don't allow dragging if locked
            if self._locked:
                return
            if self._dragging:
                try:
                    dx = event.x_root - self._drag_start_x
                    dy = event.y_root - self._drag_start_y
                    new_x = self._win_start_x + dx
                    new_y = self._win_start_y + dy
                    self.root.geometry(f"+{new_x}+{new_y}")
                    # Update stored position
                    self.position = (new_x, new_y)
                except Exception:
                    pass

        def stop_drag(event):
            if not self._locked:
                self._dragging = False
                # Save position to config
                self._save_position()

        # Bind to all widgets
        for widget in [self.root] + self._get_all_widgets(self.root):
            widget.bind("<ButtonPress-1>", start_drag)
            widget.bind("<B1-Motion>", on_drag)
            widget.bind("<ButtonRelease-1>", stop_drag)
    
    def set_locked(self, locked: bool):
        """Set the lock state of the overlay.
        
        Args:
            locked: True to lock (prevent dragging), False to unlock (allow dragging)
        """
        self._locked = locked
        # Update header to show lock status
        self._update_lock_indicator()
    
    def toggle_lock(self):
        """Toggle the lock state."""
        self.set_locked(not self._locked)
        return self._locked
    
    def _update_lock_indicator(self):
        """Update the header to show lock/unlock status."""
        try:
            # Find the header label
            for widget in self.root.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        try:
                            text = child.cget("text")
                            if "KILL TRACKER" in text:
                                # Update text to show lock status
                                lock_icon = "🔒" if self._locked else "🔓"
                                # Remove old lock icon if present and extract base text
                                base_text = text.replace("🔒", "").replace("🔓", "").strip()
                                # Keep the sword emoji and text
                                if "⚔" in base_text:
                                    child.config(text=f"{lock_icon} {base_text}")
                                else:
                                    child.config(text=f"{lock_icon} ⚔ {base_text}")
                                break
                        except Exception:
                            continue
        except Exception:
            pass

    def _get_all_widgets(self, parent):
        """Get all child widgets recursively."""
        widgets = []
        try:
            for child in parent.winfo_children():
                widgets.append(child)
                widgets.extend(self._get_all_widgets(child))
        except Exception:
            pass
        return widgets

    def show(self):
        """Show the overlay window."""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.is_visible = True
        except Exception as e:
            logger.debug(f"Error showing overlay: {e}", exc_info=True)

    def hide(self):
        """Hide the overlay window."""
        try:
            self.root.withdraw()
            self.is_visible = False
        except Exception as e:
            logger.debug(f"Error hiding overlay: {e}", exc_info=True)

    def toggle(self):
        """Toggle overlay visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def update_stats(self):
        """Update the overlay statistics from the GUI's stats."""
        try:
            with self.gui.data_lock:
                stats_copy = {
                    "total_kills": self.gui.stats.get("total_kills", 0),
                    "total_deaths": self.gui.stats.get("total_deaths", 0),
                    "kill_streak": self.gui.stats.get("kill_streak", 0),
                    "death_streak": self.gui.stats.get("death_streak", 0),
                }

            # Update kills
            self.kills_label.config(text=str(stats_copy["total_kills"]))

            # Update deaths
            self.deaths_label.config(text=str(stats_copy["total_deaths"]))

            # Calculate and update K/D ratio
            if stats_copy["total_deaths"] > 0:
                kd_ratio = stats_copy["total_kills"] / stats_copy["total_deaths"]
            else:
                kd_ratio = (
                    stats_copy["total_kills"] if stats_copy["total_kills"] > 0 else 0.0
                )
            self.kd_label.config(text=f"{kd_ratio:.2f}")

            # Update streak (positive for kill streak, negative for death streak)
            current_streak = (
                stats_copy["kill_streak"]
                if stats_copy["kill_streak"] > 0
                else -stats_copy["death_streak"]
            )
            self.streak_label.config(text=str(current_streak))

        except Exception as e:
            logger.debug(f"Error updating overlay stats: {e}", exc_info=True)

    def set_opacity(self, opacity: float):
        """Set the overlay window opacity.
        
        Args:
            opacity: Opacity value between 0.3 and 1.0 (0.3 = 30% visible, 1.0 = fully opaque)
        """
        try:
            # Clamp opacity between 0.3 and 1.0
            opacity = max(0.3, min(1.0, float(opacity)))
            self.root.attributes("-alpha", opacity)
            # Store opacity for theme changes
            self._custom_opacity = opacity
        except Exception as e:
            logger.debug(f"Error setting overlay opacity: {e}", exc_info=True)
    
    def change_theme(self, theme_name: str):
        """Change the overlay theme."""
        if theme_name not in OVERLAY_THEMES:
            logger.warning(f"Unknown theme: {theme_name}, using 'dark'")
            theme_name = "dark"

        self.theme_name = theme_name
        self.theme = OVERLAY_THEMES[theme_name]

        # Recreate UI with new theme
        try:
            # Destroy existing widgets
            for widget in self.root.winfo_children():
                widget.destroy()

            # Recreate UI
            self._create_ui()

            # Update transparency - use custom opacity if set, otherwise theme default
            try:
                if hasattr(self, "_custom_opacity"):
                    self.root.attributes("-alpha", self._custom_opacity)
                else:
                    self.root.attributes("-alpha", self.theme.get("alpha", 0.92))
            except Exception:
                pass
            
            # Ensure proper size
            self.root.geometry(f"180x150+{self.position[0]}+{self.position[1]}")
            self.root.resizable(False, False)

            # Update lock indicator after theme change
            self._update_lock_indicator()

            # Update stats display
            self.update_stats()

        except Exception as e:
            logger.debug(f"Error changing theme: {e}", exc_info=True)

    def set_position(self, x: int, y: int):
        """Set the overlay position."""
        try:
            self.position = (x, y)
            self.root.geometry(f"180x150+{x}+{y}")
        except Exception as e:
            logger.debug(f"Error setting position: {e}", exc_info=True)

    def _save_position(self):
        """Save current position to config."""
        try:
            if hasattr(self.gui, "config") and hasattr(self.gui, "config_path"):
                self.gui.config.setdefault("overlay", {})
                self.gui.config["overlay"]["position_x"] = str(self.position[0])
                self.gui.config["overlay"]["position_y"] = str(self.position[1])
                from lib.config_helpers import save_config
                save_config(self.gui.config, self.gui.config_path)
        except Exception as e:
            logger.debug(f"Error saving overlay position: {e}", exc_info=True)

    def destroy(self):
        """Destroy the overlay window."""
        try:
            self.root.destroy()
        except Exception:
            pass


def create_overlay(gui, theme: str = "dark", position: Optional[Tuple[int, int]] = None) -> KillTrackerOverlay:
    """Create and return a new KillTrackerOverlay instance.

    Args:
        gui: The main GUI instance
        theme: Theme name (default: "dark")
        position: Optional (x, y) position tuple

    Returns:
        KillTrackerOverlay instance
    """
    if position is None:
        # Default position: top-right area
        try:
            screen_width = gui.root.winfo_screenwidth()
            position = (screen_width - 200, 50)
        except Exception:
            position = (50, 50)

    overlay = KillTrackerOverlay(gui, theme=theme, position=position)
    return overlay

