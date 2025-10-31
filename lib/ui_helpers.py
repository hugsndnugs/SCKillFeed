"""UI-related helpers (styles, small utilities) extracted from GUI.

This module centralizes ttk style configuration using constants from
`constants.py` so the rest of the app can request a consistent theme.
"""

import logging
import tkinter as tk
from tkinter import ttk, scrolledtext

import tkinter.font as tkfont

from constants import (
    THEME_BG_PRIMARY,
    THEME_BG_SECONDARY,
    THEME_BG_TERTIARY,
    THEME_ACCENT_PRIMARY,
    THEME_ACCENT_SECONDARY,
    THEME_ACCENT_SUCCESS,
    THEME_ACCENT_DANGER,
    THEME_ACCENT_WARNING,
    THEME_TEXT_PRIMARY,
    THEME_TEXT_SECONDARY,
    THEME_TEXT_MUTED,
    FONT_FAMILY,
    STYLE_SCALE_BUTTON,
    STYLE_SMALL_BUTTON,
    STYLE_CARD_FRAME,
    BUTTON_AUTO_DETECT_TEXT,
    BUTTON_SAVE_SETTINGS_TEXT,
    BUTTON_EXPORT_TEXT,
    STATS_KILLS_TEMPLATE,
    STATS_STREAK_TEMPLATE,
    STATS_DEATHS_TEMPLATE,
    STATS_KD_TEMPLATE,
    TAB_KILL_FEED,
    TAB_LIVE_FEED,
    TAB_STATISTICS,
    TAB_SETTINGS,
    TAB_EXPORT,
    LABEL_COMBAT_STATISTICS,
    LABEL_WEAPON_STATISTICS,
    LABEL_RECENT_ACTIVITY,
    LABEL_PLAYER_CONFIG,
    LABEL_LOG_CONFIG,
    LABEL_EXPORT_OPTIONS,
    HEADING_WEAPON,
    HEADING_KILLS,
    HEADING_TIME,
    HEADING_EVENT,
    LABEL_YOUR_INGAME_NAME,
    LABEL_GAME_LOG_PATH,
    BUTTON_BROWSE_TEXT,
    CHECK_CSV_TEXT,
    CHECK_JSON_TEXT,
)

from lib.config_helpers import save_config

logger = logging.getLogger(__name__)


def setup_styles():
    """Setup modern dark theme styling with constants.

    This function is best-effort and catches errors from platforms or
    ttk backends that don't support particular options.
    """
    try:
        style = ttk.Style()
        # prefer a clean base theme that's available cross-platform
        try:
            style.theme_use("clam")
        except Exception:
            # fallback to default if clam isn't available
            pass

        # Notebook
        style.configure("TNotebook", background=THEME_BG_SECONDARY, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME_BG_TERTIARY,
            foreground=THEME_TEXT_PRIMARY,
            padding=[12, 7],
            font=(FONT_FAMILY, 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", THEME_ACCENT_PRIMARY),
                ("active", THEME_BG_TERTIARY),
            ],
        )

        # Frames / cards
        style.configure("TFrame", background=THEME_BG_SECONDARY)
        style.configure(STYLE_CARD_FRAME, background=THEME_BG_TERTIARY, relief="flat")

        # Labels
        style.configure(
            "TLabel", background=THEME_BG_SECONDARY, foreground=THEME_TEXT_PRIMARY
        )
        style.configure(
            "Title.TLabel",
            background=THEME_BG_SECONDARY,
            foreground=THEME_ACCENT_PRIMARY,
            font=(FONT_FAMILY, 24, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=THEME_BG_SECONDARY,
            foreground=THEME_TEXT_SECONDARY,
            font=(FONT_FAMILY, 12),
        )

        # Buttons
        style.configure(
            "TButton",
            background=THEME_ACCENT_PRIMARY,
            foreground=THEME_BG_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
            padding=[20, 10],
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("active", THEME_ACCENT_SECONDARY),
                ("pressed", THEME_ACCENT_SECONDARY),
            ],
        )

        style.configure(
            "Success.TButton",
            background=THEME_ACCENT_SUCCESS,
            foreground=THEME_BG_PRIMARY,
        )
        style.map("Success.TButton", background=[("active", "#00cc6a")])

        style.configure(
            "Danger.TButton",
            background=THEME_ACCENT_DANGER,
            foreground=THEME_TEXT_PRIMARY,
        )
        style.map("Danger.TButton", background=[("active", "#ff3742")])

        style.configure(
            STYLE_SMALL_BUTTON,
            background=THEME_ACCENT_PRIMARY,
            foreground=THEME_BG_PRIMARY,
            font=(FONT_FAMILY, 11, "bold"),
            padding=[8, 6],
            relief="flat",
        )
        style.map(
            STYLE_SMALL_BUTTON,
            background=[
                ("active", THEME_ACCENT_SECONDARY),
                ("pressed", THEME_ACCENT_SECONDARY),
            ],
        )

        style.configure(
            STYLE_SCALE_BUTTON,
            background=THEME_BG_PRIMARY,
            foreground=THEME_TEXT_SECONDARY,
            font=(FONT_FAMILY, 11),
            padding=[6, 4],
            relief="flat",
        )
        style.map(
            STYLE_SCALE_BUTTON,
            background=[("active", "#111111"), ("pressed", "#222222")],
        )

        # Treeview / list styling (may not be supported on all platforms)
        try:
            style.configure(
                "Treeview",
                background=THEME_BG_TERTIARY,
                foreground=THEME_TEXT_PRIMARY,
                fieldbackground=THEME_BG_TERTIARY,
                font=(FONT_FAMILY, 9),
            )
            style.map("Treeview", background=[("selected", THEME_ACCENT_PRIMARY)])
            # Treeview heading styling - this controls the column header cells
            style.configure(
                "Treeview.Heading",
                background=THEME_BG_PRIMARY,
                foreground=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 9, "bold"),
            )
            style.map("Treeview.Heading", background=[("active", THEME_BG_PRIMARY)])
        except Exception:
            pass

        # Entry / Combobox styling
        try:
            style.configure(
                "TEntry",
                background=THEME_BG_TERTIARY,
                foreground=THEME_TEXT_PRIMARY,
                fieldbackground=THEME_BG_TERTIARY,
                font=(FONT_FAMILY, 10),
                padding=[10, 8],
            )
            style.configure(
                "TCombobox",
                background=THEME_BG_TERTIARY,
                foreground=THEME_TEXT_PRIMARY,
                fieldbackground=THEME_BG_TERTIARY,
            )
        except Exception:
            pass

        # Checkbutton styling
        try:
            style.configure(
                "TCheckbutton",
                background=THEME_BG_SECONDARY,
                foreground=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 10),
            )
            style.map(
                "TCheckbutton",
                background=[("active", THEME_BG_SECONDARY)],
                foreground=[("active", THEME_TEXT_PRIMARY)],
            )
        except Exception:
            pass

        # Radiobutton styling
        try:
            style.configure(
                "TRadiobutton",
                background=THEME_BG_SECONDARY,
                foreground=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 10),
            )
            style.map(
                "TRadiobutton",
                background=[("active", THEME_BG_SECONDARY), ("selected", THEME_BG_SECONDARY)],
                foreground=[("active", THEME_TEXT_PRIMARY)],
            )
        except Exception:
            pass

        # Labelframe tweaks
        try:
            style.configure(
                "TLabelframe",
                background=THEME_BG_SECONDARY,
                foreground=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 11, "bold"),
            )
            style.configure(
                "TLabelframe.Label",
                background=THEME_BG_SECONDARY,
                foreground=THEME_ACCENT_PRIMARY,
                font=(FONT_FAMILY, 11, "bold"),
            )
        except Exception:
            pass

    except Exception:
        logger.debug("setup_styles failed", exc_info=True)


def init_scaling(gui):
    """Capture baseline font sizes and style paddings for a GUI instance.

    This mirrors the GUI's _init_scaling and _capture_widget_fonts behavior
    but operates on the GUI instance so the logic is testable here.
    """
    try:
        # Preserve any fonts/styles that may have been created by UI
        # construction code (for example tag-specific Font objects that are
        # created when building the kill-feed). Don't clobber existing
        # dictionaries if they were already populated.
        gui._base_font_sizes = getattr(gui, "_base_font_sizes", {}) or {}
        gui._font_objects = getattr(gui, "_font_objects", {}) or {}
        gui._base_style_paddings = getattr(gui, "_base_style_paddings", {}) or {}

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
        import tkinter.font as tkfont

        for name in font_names:
            try:
                f = tkfont.nametofont(name)
                gui._base_font_sizes[name] = f.cget("size")
            except Exception:
                continue

        try:
            _capture_widget_fonts(gui, gui.root)
        except Exception:
            logger.debug("Failed to capture widget fonts", exc_info=True)

        try:
            style = ttk.Style()
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

            import tkinter.font as tkfont

            for name in style_names:
                try:
                    font_spec = style.lookup(name, "font")
                    if font_spec:
                        try:
                            fobj = tkfont.Font(font=font_spec)
                            fname = fobj.name
                            if fname not in gui._base_font_sizes:
                                try:
                                    base_size = int(fobj.cget("size"))
                                except Exception:
                                    base_size = 10
                                gui._base_font_sizes[fname] = base_size
                                gui._font_objects[fname] = fobj
                                try:
                                    style.configure(name, font=fobj)
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    cfg = style.configure(name)
                    pad = cfg.get("padding") if isinstance(cfg, dict) else None
                    if pad:
                        try:
                            if isinstance(pad, (list, tuple)):
                                base_pad = tuple(int(x) for x in pad)
                            else:
                                base_pad = (int(pad),)
                            gui._base_style_paddings[name] = base_pad
                        except Exception:
                            pass
                except Exception:
                    continue
        except Exception:
            logger.debug("Failed to capture ttk style fonts/paddings", exc_info=True)
    except Exception:
        logger.debug("init_scaling failed", exc_info=True)


def _capture_widget_fonts(gui, widget):
    """Recursively capture fonts from widgets and assign Font objects where possible."""
    try:
        children = widget.winfo_children()
    except Exception:
        return

    import tkinter.font as tkfont

    for child in children:
        _capture_widget_fonts(gui, child)
        try:
            font_spec = child.cget("font")
        except Exception:
            continue

        if not font_spec:
            continue

        try:
            fobj = tkfont.Font(font=font_spec)
            fname = fobj.name
            if fname not in gui._base_font_sizes:
                base_size = fobj.cget("size")
                try:
                    base_size = int(base_size)
                except Exception:
                    base_size = 10
                gui._base_font_sizes[fname] = base_size
                try:
                    child.configure(font=fobj)
                except Exception:
                    pass
                gui._font_objects[fname] = fobj
        except Exception:
            continue


def apply_font_scaling(gui):
    """Apply `gui.gui_scale` to captured fonts and Tk scaling."""
    try:
        try:
            gui.root.tk.call("tk", "scaling", gui.gui_scale)
        except Exception:
            pass

        for fname, fobj in list(getattr(gui, "_font_objects", {}).items()):
            try:
                base_size = gui._base_font_sizes.get(fname, fobj.cget("size"))
                new_size = max(6, int(round(int(base_size) * gui.gui_scale)))
                fobj.configure(size=new_size)
            except Exception:
                continue

        import tkinter.font as tkfont

        for name, base_size in getattr(gui, "_base_font_sizes", {}).items():
            if name in getattr(gui, "_font_objects", {}):
                continue
            try:
                f = tkfont.nametofont(name)
                new_size = max(6, int(round(int(base_size) * gui.gui_scale)))
                f.configure(size=new_size)
            except Exception:
                continue
    except Exception:
        logger.debug("apply_font_scaling failed", exc_info=True)


def increase_scale(gui):
    """Increase GUI scale by 0.1 and persist via gui.save_config()."""
    try:
        gui.gui_scale = min(2.0, round(gui.gui_scale + 0.1, 2))
        apply_font_scaling(gui)
        try:
            gui.config["user"]["gui_scale"] = str(gui.gui_scale)
            save_config(gui.config, getattr(gui, "config_path", ""))
        except Exception:
            logger.debug("Failed to persist gui_scale on increase", exc_info=True)
    except Exception:
        logger.debug("increase_scale failed", exc_info=True)


def decrease_scale(gui):
    """Decrease GUI scale by 0.1 and persist via gui.save_config()."""
    try:
        gui.gui_scale = max(0.5, round(gui.gui_scale - 0.1, 2))
        apply_font_scaling(gui)
        try:
            gui.config["user"]["gui_scale"] = str(gui.gui_scale)
            save_config(gui.config, getattr(gui, "config_path", ""))
        except Exception:
            logger.debug("Failed to persist gui_scale on decrease", exc_info=True)
    except Exception:
        logger.debug("decrease_scale failed", exc_info=True)


def reset_scale(gui):
    """Reset GUI scale to 1.0 and persist via gui.save_config()."""
    try:
        gui.gui_scale = 1.0
        apply_font_scaling(gui)
        try:
            gui.config["user"]["gui_scale"] = str(gui.gui_scale)
            save_config(gui.config, getattr(gui, "config_path", ""))
        except Exception:
            logger.debug("Failed to persist gui_scale on reset", exc_info=True)
    except Exception:
        logger.debug("reset_scale failed", exc_info=True)


def create_kill_feed_tab(gui):
    """Create the real-time kill feed tab on the given gui instance."""
    try:
        kill_feed_frame = ttk.Frame(gui.notebook)
        gui.notebook.add(kill_feed_frame, text=TAB_KILL_FEED)

        # Control panel with modern card design
        control_frame = ttk.Frame(kill_feed_frame, style=STYLE_CARD_FRAME)
        control_frame.pack(fill=tk.X, padx=15, pady=15)

        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=15, pady=15)

        # Kill feed display with modern styling
        feed_frame = ttk.Frame(kill_feed_frame, style=STYLE_CARD_FRAME)
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        # Feed header
        feed_header = tk.Label(
            feed_frame,
            text=TAB_LIVE_FEED,
            bg=THEME_BG_TERTIARY,
            fg=THEME_ACCENT_PRIMARY,
            font=(FONT_FAMILY, 12, "bold"),
            pady=10,
        )
        feed_header.pack(fill=tk.X)

        gui.kill_feed_text = scrolledtext.ScrolledText(
            feed_frame,
            bg=THEME_BG_TERTIARY,
            fg=THEME_TEXT_PRIMARY,
            font=("Consolas", 11),
            wrap=tk.WORD,
            padx=15,
            pady=10,
            insertbackground=THEME_ACCENT_PRIMARY,
            selectbackground=THEME_ACCENT_PRIMARY,
            selectforeground=THEME_BG_TERTIARY,
        )
        gui.kill_feed_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Create and register Font objects for the kill-feed text and tags so they scale
        try:
            gui.kill_feed_font = tkfont.Font(font=gui.kill_feed_text.cget("font"))
            gui.kill_feed_text.configure(font=gui.kill_feed_font)
            gui._font_objects[gui.kill_feed_font.name] = gui.kill_feed_font
            try:
                gui._base_font_sizes[gui.kill_feed_font.name] = int(
                    gui.kill_feed_font.cget("size")
                )
            except Exception:
                gui._base_font_sizes[gui.kill_feed_font.name] = 11

            gui.kill_feed_tag_fonts = {}

            fk = tkfont.Font(family="Consolas", size=11, weight="bold")
            gui.kill_feed_tag_fonts["player_kill"] = fk
            gui.kill_feed_text.tag_configure(
                "player_kill", foreground=THEME_ACCENT_SUCCESS, font=fk
            )
            gui._font_objects[fk.name] = fk
            gui._base_font_sizes[fk.name] = 11

            fd = tkfont.Font(family="Consolas", size=11, weight="bold")
            gui.kill_feed_tag_fonts["player_death"] = fd
            gui.kill_feed_text.tag_configure(
                "player_death", foreground=THEME_ACCENT_DANGER, font=fd
            )
            gui._font_objects[fd.name] = fd
            gui._base_font_sizes[fd.name] = 11

            fw = tkfont.Font(family="Consolas", size=11, slant="italic")
            gui.kill_feed_tag_fonts["weapon"] = fw
            gui.kill_feed_text.tag_configure(
                "weapon", foreground=THEME_ACCENT_PRIMARY, font=fw
            )
            gui._font_objects[fw.name] = fw
            gui._base_font_sizes[fw.name] = 11

            ft = tkfont.Font(family="Consolas", size=10)
            gui.kill_feed_tag_fonts["timestamp"] = ft
            gui.kill_feed_text.tag_configure(
                "timestamp", foreground=THEME_TEXT_MUTED, font=ft
            )
            gui._font_objects[ft.name] = ft
            gui._base_font_sizes[ft.name] = 10

            gui.kill_feed_text.tag_configure(
                "other_kill", foreground=THEME_TEXT_SECONDARY
            )
        except Exception:
            gui.kill_feed_text.tag_configure(
                "player_kill", foreground=THEME_ACCENT_SUCCESS
            )
            gui.kill_feed_text.tag_configure(
                "player_death", foreground=THEME_ACCENT_DANGER
            )
            gui.kill_feed_text.tag_configure(
                "other_kill", foreground=THEME_TEXT_SECONDARY
            )
            gui.kill_feed_text.tag_configure("weapon", foreground=THEME_ACCENT_PRIMARY)
            gui.kill_feed_text.tag_configure("timestamp", foreground=THEME_TEXT_MUTED)
    except Exception:
        logger.debug("create_kill_feed_tab failed", exc_info=True)


def create_statistics_tab(gui):
    """Create the statistics dashboard tab on the given gui instance."""
    try:
        stats_frame = ttk.Frame(gui.notebook)
        gui.notebook.add(stats_frame, text=TAB_STATISTICS)

        main_stats_frame = ttk.Frame(stats_frame)
        main_stats_frame.pack(fill=tk.X, padx=15, pady=15)

        kd_frame = ttk.LabelFrame(
            main_stats_frame, text=LABEL_COMBAT_STATISTICS, style="TLabelframe"
        )
        kd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        stats_container = ttk.Frame(kd_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        gui.kills_label = tk.Label(
            stats_container,
            text=STATS_KILLS_TEMPLATE.format(n=0),
            bg=THEME_BG_PRIMARY,
            fg=THEME_ACCENT_SUCCESS,
            font=(FONT_FAMILY, 16, "bold"),
            pady=8,
        )
        gui.kills_label.pack(fill=tk.X, pady=5)

        gui.deaths_label = tk.Label(
            stats_container,
            text=STATS_DEATHS_TEMPLATE.format(n=0),
            bg=THEME_BG_PRIMARY,
            fg=THEME_ACCENT_DANGER,
            font=(FONT_FAMILY, 16, "bold"),
            pady=8,
        )
        gui.deaths_label.pack(fill=tk.X, pady=5)

        gui.kd_ratio_label = tk.Label(
            stats_container,
            text=STATS_KD_TEMPLATE.format(v=0.0),
            bg=THEME_BG_PRIMARY,
            fg=THEME_ACCENT_PRIMARY,
            font=(FONT_FAMILY, 14, "bold"),
            pady=8,
        )
        gui.kd_ratio_label.pack(fill=tk.X, pady=5)

        gui.streak_label = tk.Label(
            stats_container,
            text=STATS_STREAK_TEMPLATE.format(n=0),
            bg=THEME_BG_PRIMARY,
            fg=THEME_ACCENT_WARNING,
            font=(FONT_FAMILY, 14, "bold"),
            pady=8,
        )
        gui.streak_label.pack(fill=tk.X, pady=5)

        weapons_frame = ttk.LabelFrame(
            main_stats_frame, text=LABEL_WEAPON_STATISTICS, style="TLabelframe"
        )
        weapons_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        gui.weapons_tree = ttk.Treeview(
            weapons_frame, columns=("count",), show="tree headings", height=8
        )
        gui.weapons_tree.heading("#0", text=HEADING_WEAPON)
        gui.weapons_tree.heading("count", text=HEADING_KILLS)
        gui.weapons_tree.column("#0", width=200)
        gui.weapons_tree.column("count", width=80)
        gui.weapons_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        recent_frame = ttk.LabelFrame(
            stats_frame, text=LABEL_RECENT_ACTIVITY, style="TLabelframe"
        )
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        gui.recent_tree = ttk.Treeview(
            recent_frame, columns=("time", "event"), show="headings", height=10
        )
        gui.recent_tree.heading("time", text=HEADING_TIME)
        gui.recent_tree.heading("event", text=HEADING_EVENT)
        gui.recent_tree.column("time", width=100)
        gui.recent_tree.column("event", width=400)
        gui.recent_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    except Exception:
        logger.debug("create_statistics_tab failed", exc_info=True)


def create_settings_tab(gui):
    """Create the settings tab on the given gui instance."""
    try:
        settings_frame = ttk.Frame(gui.notebook)
        gui.notebook.add(settings_frame, text=TAB_SETTINGS)

        name_frame = ttk.LabelFrame(
            settings_frame, text=LABEL_PLAYER_CONFIG, style="TLabelframe"
        )
        name_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            name_frame,
            text=LABEL_YOUR_INGAME_NAME,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))
        gui.player_name_var = tk.StringVar(value=gui.player_name)
        player_entry = ttk.Entry(name_frame, textvariable=gui.player_name_var, width=50)
        player_entry.pack(fill=tk.X, padx=15, pady=(0, 15))

        log_frame = ttk.LabelFrame(
            settings_frame, text=LABEL_LOG_CONFIG, style="TLabelframe"
        )
        log_frame.pack(fill=tk.X, padx=15, pady=15)

        tk.Label(
            log_frame,
            text=LABEL_GAME_LOG_PATH,
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))

        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        gui.log_path_var = tk.StringVar(value=gui.log_file_path)
        log_entry = ttk.Entry(log_path_frame, textvariable=gui.log_path_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_button = ttk.Button(
            log_path_frame, text=BUTTON_BROWSE_TEXT, command=gui.browse_log_file
        )
        browse_button.pack(side=tk.RIGHT)

        auto_detect_button = ttk.Button(
            log_frame,
            text=BUTTON_AUTO_DETECT_TEXT,
            command=gui.auto_detect_log,
            style="TButton",
        )
        auto_detect_button.pack(pady=15)

        save_button = ttk.Button(
            settings_frame,
            text=BUTTON_SAVE_SETTINGS_TEXT,
            command=gui.save_settings,
            style="Success.TButton",
        )
        save_button.pack(pady=25)

        # Overlay settings section
        # Create overlay frame first to ensure it's always visible
        overlay_frame = ttk.LabelFrame(
            settings_frame, text="🎯 Kill Tracker Overlay", style="TLabelframe"
        )
        overlay_frame.pack(fill=tk.X, padx=15, pady=15)
        
        try:
            # Ensure overlay section exists in config
            if "overlay" not in gui.config:
                gui.config["overlay"] = {}

            # Overlay toggle
            overlay_toggle_frame = ttk.Frame(overlay_frame)
            overlay_toggle_frame.pack(fill=tk.X, padx=15, pady=(15, 5))

            tk.Label(
                overlay_toggle_frame,
                text="Show Overlay:",
                bg=THEME_BG_PRIMARY,
                fg=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 10, "bold"),
            ).pack(side=tk.LEFT, padx=(0, 10))

            overlay_enabled = (
                gui.config["overlay"].get("enabled", "false").lower() == "true"
            )
            gui.overlay_enabled_var = tk.BooleanVar(value=overlay_enabled)

            def on_overlay_toggle():
                try:
                    gui.toggle_overlay()
                except Exception as e:
                    logger.debug("Error toggling overlay", exc_info=True)
                    import tkinter.messagebox as msgbox
                    try:
                        msgbox.showerror("Error", f"Failed to toggle overlay: {e}")
                    except Exception:
                        pass

            overlay_toggle_btn = ttk.Button(
                overlay_toggle_frame,
                text="Toggle Overlay",
                command=on_overlay_toggle,
                style="TButton",
            )
            overlay_toggle_btn.pack(side=tk.LEFT)

            # Lock overlay control
            lock_frame = tk.Frame(overlay_frame, bg=THEME_BG_SECONDARY)
            lock_frame.pack(fill=tk.X, padx=15, pady=(5, 5))

            tk.Label(
                lock_frame,
                text="Lock Position:",
                bg=THEME_BG_SECONDARY,
                fg=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 9),
                anchor="w",
            ).pack(side=tk.LEFT, padx=(0, 10))

            # Get current lock state from config
            try:
                overlay_locked = gui.config["overlay"].get("locked", "false").lower() == "true"
            except Exception:
                overlay_locked = False

            gui.overlay_locked_var = tk.BooleanVar(value=overlay_locked)

            def on_lock_toggle():
                try:
                    if hasattr(gui, "overlay") and gui.overlay:
                        # Get the new state from the checkbox
                        new_locked = gui.overlay_locked_var.get()
                        gui.overlay.set_locked(new_locked)
                        gui.config.setdefault("overlay", {})
                        gui.config["overlay"]["locked"] = "true" if new_locked else "false"
                        from lib.config_helpers import save_config
                        save_config(gui.config, gui.config_path)
                except Exception as e:
                    logger.debug("Error toggling overlay lock", exc_info=True)

            lock_check = ttk.Checkbutton(
                lock_frame,
                text="🔒 Lock overlay position (prevents dragging)",
                variable=gui.overlay_locked_var,
                command=on_lock_toggle,
            )
            lock_check.pack(side=tk.LEFT)
            
            # Apply initial lock state if overlay already exists
            try:
                if hasattr(gui, "overlay") and gui.overlay:
                    gui.overlay.set_locked(overlay_locked)
            except Exception:
                pass

            # Theme selection
            theme_label_frame = ttk.Frame(overlay_frame)
            theme_label_frame.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(
                theme_label_frame,
                text="Overlay Theme:",
                bg=THEME_BG_PRIMARY,
                fg=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 10, "bold"),
            ).pack(anchor="w", pady=(5, 5))

            # Use regular Frame for better background control
            theme_frame = tk.Frame(overlay_frame, bg=THEME_BG_SECONDARY)
            theme_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

            try:
                from lib.overlay_helpers import OVERLAY_THEMES

                current_theme = gui.config["overlay"].get("theme", "dark")
                gui.overlay_theme_var = tk.StringVar(value=current_theme)

                # Create a custom style for overlay theme radio buttons to ensure dark background
                try:
                    overlay_radio_style = ttk.Style()
                    overlay_radio_style.configure(
                        "OverlayTheme.TRadiobutton",
                        background=THEME_BG_SECONDARY,
                        foreground=THEME_TEXT_PRIMARY,
                        font=(FONT_FAMILY, 10),
                    )
                    overlay_radio_style.map(
                        "OverlayTheme.TRadiobutton",
                        background=[
                            ("active", THEME_BG_SECONDARY),
                            ("selected", THEME_BG_SECONDARY),
                        ],
                        foreground=[("active", THEME_TEXT_PRIMARY)],
                    )
                except Exception:
                    overlay_radio_style = None

                for theme_name in OVERLAY_THEMES.keys():
                    theme_btn = ttk.Radiobutton(
                        theme_frame,
                        text=theme_name.capitalize(),
                        variable=gui.overlay_theme_var,
                        value=theme_name,
                        command=lambda t=theme_name: gui.change_overlay_theme(t),
                        style="OverlayTheme.TRadiobutton" if overlay_radio_style else None,
                    )
                    theme_btn.pack(side=tk.LEFT, padx=(0, 10))
            except Exception as e:
                logger.debug(f"Error creating theme selector: {e}", exc_info=True)
                tk.Label(
                    theme_frame,
                    text="Error loading themes",
                    bg=THEME_BG_PRIMARY,
                    fg=THEME_ACCENT_DANGER,
                    font=(FONT_FAMILY, 9),
                ).pack()

            # Opacity control
            opacity_label_frame = ttk.Frame(overlay_frame)
            opacity_label_frame.pack(fill=tk.X, padx=15, pady=5)

            tk.Label(
                opacity_label_frame,
                text="Overlay Opacity:",
                bg=THEME_BG_PRIMARY,
                fg=THEME_TEXT_PRIMARY,
                font=(FONT_FAMILY, 10, "bold"),
            ).pack(anchor="w", pady=(5, 5))

            opacity_control_frame = tk.Frame(overlay_frame, bg=THEME_BG_SECONDARY)
            opacity_control_frame.pack(fill=tk.X, padx=15, pady=(0, 5))

            # Get current opacity from config (default 0.92)
            try:
                current_opacity = float(gui.config["overlay"].get("opacity", "0.92"))
                # Clamp between 0.3 and 1.0
                current_opacity = max(0.3, min(1.0, current_opacity))
            except (ValueError, TypeError):
                current_opacity = 0.92

            gui.overlay_opacity_var = tk.DoubleVar(value=current_opacity)

            opacity_scale = ttk.Scale(
                opacity_control_frame,
                from_=0.3,
                to=1.0,
                variable=gui.overlay_opacity_var,
                orient=tk.HORIZONTAL,
                length=300,
            )
            opacity_scale.pack(side=tk.LEFT, padx=(0, 10))

            opacity_value_var = tk.StringVar(value=f"{int(current_opacity * 100)}%")
            opacity_value_label = tk.Label(
                opacity_control_frame,
                textvariable=opacity_value_var,
                bg=THEME_BG_SECONDARY,
                fg=THEME_TEXT_SECONDARY,
                font=(FONT_FAMILY, 9),
                width=5,
            )
            opacity_value_label.pack(side=tk.LEFT)

            # Update opacity when scale changes
            def update_opacity(*args):
                try:
                    val = gui.overlay_opacity_var.get()
                    opacity_value_var.set(f"{int(val * 100)}%")
                    # Update overlay if it exists
                    if hasattr(gui, "overlay") and gui.overlay:
                        gui.change_overlay_opacity(val)
                except Exception as e:
                    logger.debug(f"Error updating opacity: {e}", exc_info=True)

            gui.overlay_opacity_var.trace("w", update_opacity)
            # Also bind to scale release for immediate feedback
            opacity_scale.configure(command=lambda v: update_opacity())

            # Info text
            info_label = tk.Label(
                overlay_frame,
                text="💡 Tip: Click and drag the overlay to reposition it. The overlay stays on top of other windows.",
                bg=THEME_BG_PRIMARY,
                fg=THEME_TEXT_SECONDARY,
                font=(FONT_FAMILY, 9),
                justify=tk.LEFT,
                wraplength=600,
            )
            info_label.pack(anchor="w", padx=15, pady=(0, 15))
        except Exception as e:
            logger.error(f"Error creating overlay settings section: {e}", exc_info=True)
            # Show error in the already-created overlay frame
            error_label = tk.Label(
                overlay_frame,
                text=f"Error loading overlay settings: {e}",
                bg=THEME_BG_PRIMARY,
                fg=THEME_ACCENT_DANGER,
                font=(FONT_FAMILY, 9),
                wraplength=600,
                justify=tk.LEFT,
            )
            error_label.pack(padx=15, pady=15)
    except Exception:
        logger.debug("create_settings_tab failed", exc_info=True)


def create_export_tab(gui):
    """Create the export tab on the given gui instance."""
    try:
        export_frame = ttk.Frame(gui.notebook)
        gui.notebook.add(export_frame, text=TAB_EXPORT)

        options_frame = ttk.LabelFrame(
            export_frame, text=LABEL_EXPORT_OPTIONS, style="TLabelframe"
        )
        options_frame.pack(fill=tk.X, padx=15, pady=15)

        gui.export_csv_var = tk.BooleanVar(value=True)
        csv_check = ttk.Checkbutton(
            options_frame, text=CHECK_CSV_TEXT, variable=gui.export_csv_var
        )
        csv_check.pack(anchor="w", padx=15, pady=10)

        gui.export_json_var = tk.BooleanVar(value=False)
        json_check = ttk.Checkbutton(
            options_frame, text=CHECK_JSON_TEXT, variable=gui.export_json_var
        )
        json_check.pack(anchor="w", padx=15, pady=10)

        export_button = ttk.Button(
            export_frame,
            text=BUTTON_EXPORT_TEXT,
            command=gui.export_data,
            style="Success.TButton",
        )
        export_button.pack(pady=25)

        gui.export_status = tk.Label(
            export_frame,
            text="",
            bg=THEME_BG_PRIMARY,
            fg=THEME_TEXT_PRIMARY,
            font=(FONT_FAMILY, 10),
            pady=10,
        )
        gui.export_status.pack(pady=15)
    except Exception:
        logger.debug("create_export_tab failed", exc_info=True)
