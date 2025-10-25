import os
import sys
from types import SimpleNamespace

from lib import win32_helpers


def test_set_app_icon_with_missing_file_does_nothing(tmp_path):
    # pass an ico_path that does not exist -> function should not raise
    fake_root = SimpleNamespace()

    # provide an iconbitmap method to observe if it would be called
    called = {"icon": False}

    def iconbitmap(path):
        called["icon"] = True

    fake_root.iconbitmap = iconbitmap

    # call with a non-existent path
    nonexist = str(tmp_path / "nope.ico")
    win32_helpers.set_app_icon(fake_root, tk_root=None, ico_path=nonexist)
    # since file doesn't exist, iconbitmap should not have been called
    assert not called["icon"]


def test_set_app_icon_calls_iconbitmap_when_file_exists(tmp_path, monkeypatch):
    fake_root = SimpleNamespace()
    called = {"icon": False}

    def iconbitmap(path):
        called["icon"] = True

    fake_root.iconbitmap = iconbitmap

    # create an empty file to simulate an ico
    ico = tmp_path / "fake.ico"
    ico.write_bytes(b"\x00")

    win32_helpers.set_app_icon(fake_root, tk_root=None, ico_path=str(ico))
    assert called["icon"]


def test_apply_native_win32_borderless_noop_on_non_win(monkeypatch):
    # ensure non-win32 platform doesn't raise
    monkeypatch.setattr(sys, "platform", "linux")
    fake = SimpleNamespace()
    # should not raise
    win32_helpers.apply_native_win32_borderless(fake)


def test_set_foreground_hwnd_returns_false_on_non_win(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    assert win32_helpers.set_foreground_hwnd(12345) is False
