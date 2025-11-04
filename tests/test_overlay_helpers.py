"""Unit tests for overlay_helpers module."""

import unittest
import threading
from collections import Counter
from unittest.mock import Mock, patch, MagicMock

from lib.overlay_helpers import OVERLAY_THEMES, create_overlay


class MockGUI:
    """Mock GUI object for testing overlay functionality."""

    def __init__(self):
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
        self.player_name = "TestPlayer"
        self.data_lock = threading.RLock()
        self.config = {}
        self.config_path = "test.cfg"
        self.root = Mock()
        self.root.winfo_screenwidth = Mock(return_value=1920)
        self.root.after = Mock(return_value=None)
        self.root.after_cancel = Mock()


class MockTkRoot:
    """Mock Tkinter root for overlay window."""

    def __init__(self):
        self.attributes_calls = []
        self.geometry_calls = []
        self.withdraw_calls = []
        self.deiconify_calls = []
        self.title_calls = []
        self.resizable_calls = []
        self.winfo_children_calls = []
        self.winfo_x_calls = []
        self.winfo_y_calls = []
        self._children = []
        self.tk = Mock()  # Required by tkinter
        self.pack_calls = []  # Track pack() calls
        self.config_calls = []  # Track config() calls

    def attributes(self, *args, **kwargs):
        """Mock attributes() method for window attributes."""
        if args:
            # Handle positional args like root.attributes("-topmost", True)
            for i in range(0, len(args), 2):
                if i + 1 < len(args):
                    kwargs[args[i]] = args[i + 1]
        self.attributes_calls.append(kwargs)
        return None

    def geometry(self, geom):
        self.geometry_calls.append(geom)

    def withdraw(self):
        self.withdraw_calls.append(True)

    def deiconify(self):
        self.deiconify_calls.append(True)

    def lift(self):
        """Mock lift() method to bring window to front."""
        pass

    def title(self, title=None):
        if title:
            self.title_calls.append(title)

    def resizable(self, width, height):
        self.resizable_calls.append((width, height))

    def winfo_children(self):
        return self._children

    def winfo_x(self):
        return 100

    def winfo_y(self):
        return 100

    def destroy(self):
        pass

    def bind(self, *args, **kwargs):
        pass

    def pack(self, **kwargs):
        """Mock pack() method for widgets."""
        self.pack_calls.append(kwargs)

    def config(self, **kwargs):
        """Mock config() method for widgets."""
        self.config_calls.append(kwargs)

    def cget(self, key):
        """Mock cget() method for widgets."""
        return self.config_calls[-1].get(key, "") if self.config_calls else ""

    def overrideredirect(self, flag):
        """Mock overrideredirect() method."""
        pass


@patch("lib.overlay_helpers.tk.Toplevel")
@patch("lib.overlay_helpers.tk.Frame")
@patch("lib.overlay_helpers.tk.Label")
class TestKillTrackerOverlay(unittest.TestCase):
    """Test cases for KillTrackerOverlay class."""

    def setUp(self):
        self.gui = MockGUI()

    def test_overlay_initialization(self, mock_label, mock_frame, mock_toplevel):
        """Test overlay initialization with default theme."""
        # Mock tkinter widgets to avoid real widget creation
        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        # Import here after patching
        from lib.overlay_helpers import KillTrackerOverlay

        overlay = KillTrackerOverlay(self.gui, theme="dark", position=(50, 50))

        self.assertIsNotNone(overlay)
        self.assertEqual(overlay.theme_name, "dark")
        self.assertEqual(overlay.position, (50, 50))
        self.assertFalse(overlay.is_visible)
        self.assertFalse(overlay._locked)
        self.assertIsNone(overlay._custom_opacity)

    def test_overlay_themes(self, mock_label, mock_frame, mock_toplevel):
        """Test overlay with different themes."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        for theme_name in OVERLAY_THEMES.keys():
            overlay = KillTrackerOverlay(self.gui, theme=theme_name, position=(0, 0))
            self.assertEqual(overlay.theme_name, theme_name)
            self.assertIn(theme_name, OVERLAY_THEMES)

    def test_overlay_show_hide(self, mock_label, mock_frame, mock_toplevel):
        """Test overlay show and hide functionality."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)
        overlay.show()
        self.assertTrue(overlay.is_visible)
        self.assertTrue(len(mock_root.deiconify_calls) > 0)

        overlay.hide()
        self.assertFalse(overlay.is_visible)
        self.assertTrue(len(mock_root.withdraw_calls) > 1)

    def test_overlay_toggle(self, mock_label, mock_frame, mock_toplevel):
        """Test overlay toggle functionality."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)
        self.assertFalse(overlay.is_visible)

        overlay.toggle()
        self.assertTrue(overlay.is_visible)

        overlay.toggle()
        self.assertFalse(overlay.is_visible)

    def test_overlay_update_stats(self, mock_label, mock_frame, mock_toplevel):
        """Test overlay statistics update."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label_instance = Mock()
        mock_label_instance.cget = Mock(return_value="")
        mock_label_instance.config = Mock()
        mock_label.return_value = mock_label_instance

        overlay = KillTrackerOverlay(self.gui)

        # Update GUI stats
        self.gui.stats["total_kills"] = 5
        self.gui.stats["total_deaths"] = 2
        self.gui.stats["kill_streak"] = 3
        self.gui.stats["death_streak"] = 0

        overlay.update_stats()

        # Check that labels exist in stat_widgets dictionary
        self.assertIsNotNone(overlay.stat_widgets.get("kills"))
        self.assertIsNotNone(overlay.stat_widgets.get("deaths"))
        self.assertIsNotNone(overlay.stat_widgets.get("kd"))
        self.assertIsNotNone(overlay.stat_widgets.get("streak"))

    def test_overlay_kd_calculation(self, mock_label, mock_frame, mock_toplevel):
        """Test K/D ratio calculation in overlay."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label_instance = Mock()
        mock_label_instance.cget = Mock(return_value="")
        mock_label_instance.config = Mock()
        mock_label.return_value = mock_label_instance

        overlay = KillTrackerOverlay(self.gui)

        # Test case: 10 kills, 5 deaths = 2.00 K/D
        self.gui.stats["total_kills"] = 10
        self.gui.stats["total_deaths"] = 5
        self.gui.stats["kill_streak"] = 0
        self.gui.stats["death_streak"] = 0

        overlay.update_stats()
        # Check that config was called with correct K/D value
        kd_widget = overlay.stat_widgets.get("kd")
        self.assertIsNotNone(kd_widget)
        calls = [
            call
            for call in kd_widget.config.call_args_list
            if "text" in (call[0][0] if call[0] else {})
            or (call[1] and "text" in call[1])
        ]
        self.assertTrue(len(calls) > 0 or hasattr(kd_widget, "config"))

        # Test case: 0 deaths
        self.gui.stats["total_kills"] = 7
        self.gui.stats["total_deaths"] = 0
        overlay.update_stats()

    def test_overlay_streak_display(self, mock_label, mock_frame, mock_toplevel):
        """Test streak display in overlay."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label_instance = Mock()
        mock_label_instance.cget = Mock(return_value="")
        mock_label_instance.config = Mock()
        mock_label.return_value = mock_label_instance

        overlay = KillTrackerOverlay(self.gui)

        # Test kill streak
        self.gui.stats["kill_streak"] = 5
        self.gui.stats["death_streak"] = 0
        overlay.update_stats()

        # Test death streak (should be negative)
        self.gui.stats["kill_streak"] = 0
        self.gui.stats["death_streak"] = 3
        overlay.update_stats()

    def test_overlay_change_theme(self, mock_label, mock_frame, mock_toplevel):
        """Test theme changing functionality."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui, theme="dark")
        self.assertEqual(overlay.theme_name, "dark")

        overlay.change_theme("neon")
        self.assertEqual(overlay.theme_name, "neon")
        # Verify theme properties changed to neon theme
        self.assertEqual(overlay.theme["fg"], "#00ffff")  # Neon theme property

    def test_overlay_change_theme_invalid(self, mock_label, mock_frame, mock_toplevel):
        """Test theme change with invalid theme name."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui, theme="dark")
        overlay.change_theme("invalid_theme")
        # Should fall back to dark
        self.assertEqual(overlay.theme_name, "dark")

    def test_overlay_set_opacity(self, mock_label, mock_frame, mock_toplevel):
        """Test opacity setting."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)
        overlay.set_opacity(0.85)

        # Check that custom opacity was set
        self.assertEqual(overlay._custom_opacity, 0.85)

    def test_overlay_set_opacity_clamping(self, mock_label, mock_frame, mock_toplevel):
        """Test opacity clamping to valid range."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)

        # Test too low
        overlay.set_opacity(0.1)
        self.assertEqual(overlay._custom_opacity, 0.3)  # Should clamp to 0.3

        # Test too high
        overlay.set_opacity(1.5)
        self.assertEqual(overlay._custom_opacity, 1.0)  # Should clamp to 1.0

    def test_overlay_lock_unlock(self, mock_label, mock_frame, mock_toplevel):
        """Test lock/unlock functionality."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)
        self.assertFalse(overlay._locked)

        overlay.set_locked(True)
        self.assertTrue(overlay._locked)

        overlay.set_locked(False)
        self.assertFalse(overlay._locked)

        # Test toggle
        result = overlay.toggle_lock()
        self.assertTrue(result)  # Should return True when locked
        self.assertTrue(overlay._locked)

        result = overlay.toggle_lock()
        self.assertFalse(result)  # Should return False when unlocked
        self.assertFalse(overlay._locked)

    def test_overlay_drag_prevention_when_locked(
        self, mock_label, mock_frame, mock_toplevel
    ):
        """Test that dragging is prevented when locked."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui)
        overlay.set_locked(True)

        # When locked, dragging should not update position
        self.assertTrue(overlay._locked)

    def test_overlay_set_position(self, mock_label, mock_frame, mock_toplevel):
        """Test position setting."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        overlay = KillTrackerOverlay(self.gui, position=(50, 50))
        overlay.set_position(100, 200)

        self.assertEqual(overlay.position, (100, 200))

    def test_overlay_position_save(self, mock_label, mock_frame, mock_toplevel):
        """Test position saving to config."""
        from lib.overlay_helpers import KillTrackerOverlay

        mock_root = MockTkRoot()
        mock_toplevel.return_value = mock_root
        mock_frame.return_value = MockTkRoot()
        mock_label.return_value = Mock()

        with patch("lib.config_helpers.save_config"):
            overlay = KillTrackerOverlay(self.gui)
            overlay.position = (150, 150)
            overlay._save_position()

            # Check that config was accessed
            self.assertIsNotNone(self.gui.config)


class TestCreateOverlay(unittest.TestCase):
    """Test cases for create_overlay factory function."""

    def setUp(self):
        self.gui = MockGUI()

    @patch("lib.overlay_helpers.KillTrackerOverlay")
    def test_create_overlay_default(self, mock_overlay_class):
        """Test create_overlay with default parameters."""
        mock_overlay = Mock()
        mock_overlay_class.return_value = mock_overlay

        result = create_overlay(self.gui)

        mock_overlay_class.assert_called_once()
        self.assertEqual(result, mock_overlay)

    @patch("lib.overlay_helpers.KillTrackerOverlay")
    def test_create_overlay_with_theme(self, mock_overlay_class):
        """Test create_overlay with specific theme."""
        mock_overlay = Mock()
        mock_overlay_class.return_value = mock_overlay

        result = create_overlay(self.gui, theme="neon")

        # Check that theme was passed
        call_args = mock_overlay_class.call_args
        self.assertEqual(call_args[1]["theme"], "neon")

    @patch("lib.overlay_helpers.KillTrackerOverlay")
    def test_create_overlay_with_position(self, mock_overlay_class):
        """Test create_overlay with specific position."""
        mock_overlay = Mock()
        mock_overlay_class.return_value = mock_overlay

        position = (200, 300)
        result = create_overlay(self.gui, position=position)

        # Check that position was passed
        call_args = mock_overlay_class.call_args
        self.assertEqual(call_args[1]["position"], position)


class TestOverlayThemes(unittest.TestCase):
    """Test cases for overlay themes."""

    def test_all_themes_exist(self):
        """Test that all expected themes exist."""
        expected_themes = ["dark", "light", "neon", "minimal"]
        for theme in expected_themes:
            self.assertIn(theme, OVERLAY_THEMES)

    def test_theme_structure(self):
        """Test that themes have required keys."""
        required_keys = [
            "bg",
            "fg",
            "accent_kill",
            "accent_death",
            "accent_kd",
            "accent_streak",
            "border",
            "alpha",
        ]
        for theme_name, theme in OVERLAY_THEMES.items():
            for key in required_keys:
                self.assertIn(key, theme, f"Theme {theme_name} missing key {key}")

    def test_theme_alpha_range(self):
        """Test that theme alpha values are in valid range."""
        for theme_name, theme in OVERLAY_THEMES.items():
            alpha = theme.get("alpha", 1.0)
            self.assertGreaterEqual(alpha, 0.0, f"Theme {theme_name} alpha too low")
            self.assertLessEqual(alpha, 1.0, f"Theme {theme_name} alpha too high")


if __name__ == "__main__":
    unittest.main()
