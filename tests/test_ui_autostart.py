import sc_kill_feed_gui as gui


def test_start_stop_monitoring():
    g = object.__new__(gui.StarCitizenKillFeedGUI)
    # Minimal attrs required
    g.is_monitoring = False

    # status_var should have set method; use a simple stub
    class StubVar:
        def __init__(self):
            self.val = None

        def set(self, v):
            self.val = v

    g.status_var = StubVar()

    # Prevent actual background thread from starting by stubbing Thread
    class DummyThread:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

    orig_thread = gui.threading.Thread
    gui.threading.Thread = DummyThread
    try:
        g.start_monitoring()
        assert g.is_monitoring is True

        g.stop_monitoring()
        assert g.is_monitoring is False
    finally:
        gui.threading.Thread = orig_thread


def test_save_settings_triggers_autostart(monkeypatch, tmp_path):
    g = object.__new__(gui.StarCitizenKillFeedGUI)

    # Provide player_name_var and log_path_var with get()
    class Var:
        def __init__(self, v):
            self._v = v

        def get(self):
            return self._v

    g.player_name_var = Var("PlayerOne")
    g.log_path_var = Var(str(tmp_path / "game.log"))

    # Stub validation and save_config
    g.validate_player_name = lambda n: True
    g.validate_file_path = lambda p: True
    g.save_config = lambda: None
    # Provide minimal config structure used by save_settings
    import configparser

    g.config = configparser.ConfigParser()
    g.config["user"] = {}

    # Replace messagebox functions to avoid GUI dialogs
    monkeypatch.setattr(
        gui,
        "messagebox",
        type(
            "M",
            (),
            {
                "showinfo": lambda *a, **k: None,
                "showerror": lambda *a, **k: None,
                "showwarning": lambda *a, **k: None,
            },
        ),
    )

    started = {"called": False}

    def fake_start():
        started["called"] = True

    g.start_monitoring = fake_start
    g.is_monitoring = False

    # Run save_settings and expect start_monitoring to be called
    g.save_settings()
    assert started["called"] is True
