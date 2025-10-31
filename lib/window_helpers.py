"""Window and resize-related helpers extracted from the GUI.

These helpers operate on a GUI-like object (expects attributes such as
`root`, `_resize_border`, `_resizing`, `_resize_dir`, `_resize_start_x`,
`_resize_start_y`, `_start_geom`, `_resize_left`, and `_resize_top`).
They are structured as standalone functions to improve testability while
keeping event binding in the GUI.
"""

import logging

logger = logging.getLogger(__name__)


def determine_cursor(gui, x_root, y_root):
    """Determine appropriate resize cursor string for the window."""
    try:
        win_x = gui.root.winfo_x()
        win_y = gui.root.winfo_y()
        w = gui.root.winfo_width()
        h = gui.root.winfo_height()
        margin = getattr(gui, "_resize_border", 8)

        left = abs(x_root - win_x) <= margin
        right = abs(x_root - (win_x + w)) <= margin
        top = abs(y_root - win_y) <= margin
        bottom = abs(y_root - (win_y + h)) <= margin

        if left and top:
            return "size_nw_se"
        if right and bottom:
            return "size_nw_se"
        if left and bottom:
            return "size_ne_sw"
        if right and top:
            return "size_ne_sw"
        if left or right:
            return "size_we"
        if top or bottom:
            return "size_ns"
        return ""
    except Exception:
        logger.debug("determine_cursor failed", exc_info=True)
        return ""


def on_root_motion(gui, event):
    """Handler for Motion events to update cursor when near edges."""
    try:
        cursor = determine_cursor(gui, event.x_root, event.y_root)
        try:
            gui.root.configure(cursor=cursor)
        except Exception:
            pass
    except Exception:
        logger.debug("on_root_motion error", exc_info=True)


def on_root_button_press(gui, event):
    """Begin resize operation if cursor indicates resizing."""
    try:
        cur = ""
        try:
            cur = gui.root["cursor"] if gui.root["cursor"] else ""
        except Exception:
            cur = ""

        if cur:
            try:
                gui._resizing = True
                gui._resize_dir = cur
                gui._resize_start_x = event.x_root
                gui._resize_start_y = event.y_root
                gui._start_geom = (
                    gui.root.winfo_x(),
                    gui.root.winfo_y(),
                    gui.root.winfo_width(),
                    gui.root.winfo_height(),
                )
                # Determine which edges are being resized from the start
                # to avoid jumping when cursor position crosses window center
                sx, sy, sw, sh = gui._start_geom
                gui._resize_left = event.x_root < sx + sw / 2
                gui._resize_top = event.y_root < sy + sh / 2
            except Exception:
                gui._resizing = False
    except Exception:
        logger.debug("on_root_button_press error", exc_info=True)


def on_root_button_release(gui, event):
    try:
        gui._resizing = False
        gui._resize_dir = None
    except Exception:
        logger.debug("on_root_button_release error", exc_info=True)


def on_root_drag(gui, event):
    """Handle actual resize drag. Expects gui._resizing and geometry state."""
    if not getattr(gui, "_resizing", False):
        return

    try:
        dir = gui._resize_dir
        sx, sy, sw, sh = gui._start_geom
        dx = event.x_root - gui._resize_start_x
        dy = event.y_root - gui._resize_start_y

        new_x, new_y, new_w, new_h = sx, sy, sw, sh

        # Use the pre-determined resize direction to avoid jumping
        resize_left = getattr(gui, "_resize_left", False)
        resize_top = getattr(gui, "_resize_top", False)

        if dir == "size_we":
            if resize_left:
                new_x = sx + dx
                new_w = sw - dx
            else:
                new_w = sw + dx
        elif dir == "size_ns":
            if resize_top:
                new_y = sy + dy
                new_h = sh - dy
            else:
                new_h = sh + dy
        elif dir == "size_nw_se":
            if resize_left:
                new_x = sx + dx
                new_w = sw - dx
            else:
                new_w = sw + dx
            if resize_top:
                new_y = sy + dy
                new_h = sh - dy
            else:
                new_h = sh + dy
        elif dir == "size_ne_sw":
            if resize_left:
                new_x = sx + dx
                new_w = sw - dx
            else:
                new_w = sw + dx
            if resize_top:
                new_y = sy + dy
                new_h = sh - dy
            else:
                new_h = sh + dy

        try:
            if new_w < 1:
                new_w = 1
            if new_h < 1:
                new_h = 1
            gui.root.geometry(f"{int(new_w)}x{int(new_h)}+{int(new_x)}+{int(new_y)}")
        except Exception:
            pass
    except Exception:
        logger.debug("on_root_drag error", exc_info=True)
