"""Windows-specific window and icon helpers.

These helpers are best-effort and safe to import on non-Windows
platforms; they simply no-op when the Win32 API is not available.
"""

import os
import sys
import logging
from constants import ASSETS_DIR, ICON_FILENAME

logger = logging.getLogger(__name__)


def set_app_icon(root_window, tk_root=None, ico_path=None):
    """Set the application icon using Tk methods and Win32 WM_SETICON/class icon.

    root_window: visible toplevel
    tk_root: optional hidden root that may own the taskbar entry
    ico_path: optional explicit path to .ico file; if None will attempt to
      look in the assets/ directory relative to the package.
    """
    try:
        if not ico_path:
            base = os.path.dirname(os.path.abspath(__file__))
            # lib/.. -> project root
            project_root = os.path.dirname(base)
            ico_path = os.path.join(project_root, ASSETS_DIR, ICON_FILENAME)

        if os.path.exists(ico_path):
            try:
                try:
                    root_window.iconbitmap(ico_path)
                except Exception:
                    pass
                if tk_root:
                    try:
                        tk_root.iconbitmap(ico_path)
                    except Exception:
                        pass

                if sys.platform == "win32":
                    try:
                        import ctypes

                        LR_LOADFROMFILE = 0x00000010
                        IMAGE_ICON = 1
                        hIcon = ctypes.windll.user32.LoadImageW(
                            0, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE
                        )
                        if hIcon:
                            WM_SETICON = 0x0080
                            ICON_SMALL = 0
                            ICON_BIG = 1

                            def _set_icon(win):
                                try:
                                    hwnd = int(win.winfo_id())
                                    ctypes.windll.user32.SendMessageW(
                                        hwnd, WM_SETICON, ICON_SMALL, hIcon
                                    )
                                    ctypes.windll.user32.SendMessageW(
                                        hwnd, WM_SETICON, ICON_BIG, hIcon
                                    )
                                    try:
                                        GCLP_HICON = -14
                                        GCLP_HICONSM = -34
                                        try:
                                            ctypes.windll.user32.SetClassLongPtrW(
                                                hwnd, GCLP_HICON, hIcon
                                            )
                                            ctypes.windll.user32.SetClassLongPtrW(
                                                hwnd, GCLP_HICONSM, hIcon
                                            )
                                        except Exception:
                                            try:
                                                ctypes.windll.user32.SetClassLongW(
                                                    hwnd, GCLP_HICON, hIcon
                                                )
                                                ctypes.windll.user32.SetClassLongW(
                                                    hwnd, GCLP_HICONSM, hIcon
                                                )
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                                except Exception:
                                    pass

                            try:
                                _set_icon(root_window)
                            except Exception:
                                pass
                            if tk_root:
                                try:
                                    _set_icon(tk_root)
                                except Exception:
                                    pass
                    except Exception:
                        logger.debug("Failed to set Win32 icon", exc_info=True)
            except Exception:
                logger.debug("Failed to apply icon via Tk", exc_info=True)
    except Exception:
        logger.debug("set_app_icon fallback failure", exc_info=True)


def apply_native_win32_borderless(win):
    """Apply native Win32 borderless style to a Tk window (best-effort).

    Accepts a Tk widget (Toplevel or Tk) and tries to change its window
    style to a frameless WS_POPUP while keeping the WS_EX_APPWINDOW bit so
    it remains on the taskbar.
    """
    try:
        if sys.platform != "win32":
            return
        import ctypes

        hwnd = win.winfo_id()

        GWL_STYLE = -16
        GWL_EXSTYLE = -20
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_SYSMENU = 0x00080000
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000

        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080

        style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
        WS_POPUP = 0x80000000
        remove_mask = (
            WS_CAPTION | WS_THICKFRAME | WS_SYSMENU | WS_MAXIMIZEBOX | WS_MINIMIZEBOX
        )
        new_style = (style & ~remove_mask) | WS_POPUP
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

        ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex = (ex | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)

        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOZORDER = 0x0004
        SWP_FRAMECHANGED = 0x0020
        SWP_SHOWWINDOW = 0x0040
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW,
        )
    except Exception:
        logger.debug("apply_native_win32_borderless failed", exc_info=True)


def set_foreground_hwnd(hwnd):
    """Set foreground to the given HWND (best-effort)."""
    try:
        if sys.platform != "win32":
            return False
        import ctypes

        user32 = ctypes.windll.user32
        try:
            user32.SetForegroundWindow(hwnd)
            return True
        except Exception:
            try:
                # As a fallback, bring window to top and show
                user32.BringWindowToTop(hwnd)
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                return True
            except Exception:
                return False
    except Exception:
        logger.debug("set_foreground_hwnd failed", exc_info=True)
        return False


def setup_taskbar_click_handler(tk_root, callback):
    """Setup a handler for taskbar icon clicks on Windows.

    This function sets up a Windows message handler to catch WM_COMMAND
    messages that are sent when the taskbar icon is clicked, providing
    more reliable taskbar interaction.
    """
    try:
        if sys.platform != "win32":
            return False
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Get the window handle
        hwnd = tk_root.winfo_id()

        # Define the window procedure
        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

        def window_proc(hwnd, msg, wparam, lparam):
            # Handle WM_COMMAND messages (taskbar clicks)
            if msg == 0x0111:  # WM_COMMAND
                try:
                    callback()
                except Exception:
                    pass

            # Call the default window procedure
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        # Set the new window procedure
        old_proc = user32.SetWindowLongW(
            hwnd, -4, WNDPROC(window_proc)
        )  # GWL_WNDPROC = -4

        return True
    except Exception:
        logger.debug("setup_taskbar_click_handler failed", exc_info=True)
        return False
