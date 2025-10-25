import tkinter as tk

from lib import ui_helpers


def test_setup_styles_runs_without_error():
    # create a hidden root to allow ttk.Style() to initialize
    root = tk.Tk()
    try:
        root.withdraw()
        # should not raise
        ui_helpers.setup_styles()
    finally:
        root.destroy()
