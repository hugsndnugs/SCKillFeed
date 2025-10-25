import sys
import importlib


def test_no_messagebox_on_import(monkeypatch):
    """Ensure importing the GUI module does not show any messagebox dialogs.

    This guards against regressions where a messagebox call is executed at
    module import time.
    """
    calls = []

    def make_stub(name):
        def _stub(*a, **k):
            calls.append(name)

        return _stub

    # Patch the tkinter.messagebox functions BEFORE importing the module so
    # the module-level import will pick up our stubs if it tries to call them.
    monkeypatch.setattr("tkinter.messagebox.showinfo", make_stub("showinfo"))
    monkeypatch.setattr("tkinter.messagebox.showwarning", make_stub("showwarning"))
    monkeypatch.setattr("tkinter.messagebox.showerror", make_stub("showerror"))

    # Ensure we re-import the module fresh to trigger any accidental top-level calls
    if "sc_kill_feed_gui" in sys.modules:
        del sys.modules["sc_kill_feed_gui"]

    import sc_kill_feed_gui as gui_mod

    importlib.reload(gui_mod)

    # No messagebox functions should have been called during import
    assert calls == []
