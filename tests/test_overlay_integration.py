"""Integration tests for overlay functionality in the main GUI."""

import unittest
import threading
import configparser
from collections import Counter
from unittest.mock import Mock, patch, MagicMock

from sc_kill_feed_gui import StarCitizenKillFeedGUI


def make_stub_gui_for_overlay():
    """Create a minimal GUI stub for overlay testing."""
    g = object.__new__(StarCitizenKillFeedGUI)
    
    # Essential attributes
    g.player_name = "TestPlayer"
    g.log_file_path = ""
    g.is_monitoring = False
    g.kills_data = []
    g.data_lock = threading.RLock()
    g.stats = {
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
    
    # Config
    g.config = configparser.ConfigParser()
    g.config["user"] = {}
    g.config["overlay"] = {
        "enabled": "false",
        "theme": "dark",
        "opacity": "0.92",
        "locked": "false",
        "position_x": "0",
        "position_y": "0",
    }
    g.config_path = "test.cfg"
    
    # Root mock
    g.root = Mock()
    g.root.winfo_screenwidth = Mock(return_value=1920)
    g.root.after = Mock(return_value=None)
    g.root.after_cancel = Mock()
    g._tk_root = None
    
    # Overlay tracking
    g.overlay = None
    g._overlay_update_job = None
    
    return g


class TestOverlayIntegration(unittest.TestCase):
    """Integration tests for overlay functionality."""
    
    def setUp(self):
        self.gui = make_stub_gui_for_overlay()
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_init_overlay_default_config(self, mock_create_overlay):
        """Test overlay initialization with default config."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_create_overlay.return_value = mock_overlay
        
        self.gui._init_overlay()
        
        # Check that overlay was created
        self.assertIsNotNone(self.gui.overlay)
        mock_create_overlay.assert_called_once()
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_init_overlay_with_opacity(self, mock_create_overlay):
        """Test overlay initialization with custom opacity."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_overlay.set_opacity = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.config["overlay"]["opacity"] = "0.85"
        self.gui._init_overlay()
        
        # Check that opacity was set
        mock_overlay.set_opacity.assert_called_once_with(0.85)
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_init_overlay_with_lock(self, mock_create_overlay):
        """Test overlay initialization with lock state."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_overlay.set_locked = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.config["overlay"]["locked"] = "true"
        self.gui._init_overlay()
        
        # Check that lock was set
        mock_overlay.set_locked.assert_called_once_with(True)
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_init_overlay_enabled(self, mock_create_overlay):
        """Test overlay initialization when enabled."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_overlay.show = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.config["overlay"]["enabled"] = "true"
        self.gui._init_overlay()
        
        # Check that overlay was shown
        mock_overlay.show.assert_called_once()
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_toggle_overlay(self, mock_create_overlay):
        """Test toggling overlay visibility."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_overlay.toggle = Mock()
        mock_overlay.show = Mock()
        mock_overlay.hide = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.overlay = mock_overlay
        
        # First toggle should show
        mock_overlay.is_visible = False
        self.gui.toggle_overlay()
        mock_overlay.toggle.assert_called_once()
    
    @patch('sc_kill_feed_gui.create_overlay')
    @patch('sc_kill_feed_gui.save_config')
    def test_change_overlay_theme(self, mock_save_config, mock_create_overlay):
        """Test changing overlay theme."""
        mock_overlay = Mock()
        mock_overlay.change_theme = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.overlay = mock_overlay
        self.gui.change_overlay_theme("neon")
        
        # Check that theme was changed
        mock_overlay.change_theme.assert_called_once_with("neon")
        # Check that config was saved
        mock_save_config.assert_called_once()
        self.assertEqual(self.gui.config["overlay"]["theme"], "neon")
    
    @patch('sc_kill_feed_gui.create_overlay')
    @patch('sc_kill_feed_gui.save_config')
    def test_change_overlay_opacity(self, mock_save_config, mock_create_overlay):
        """Test changing overlay opacity."""
        mock_overlay = Mock()
        mock_overlay.set_opacity = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.overlay = mock_overlay
        self.gui.change_overlay_opacity(0.75)
        
        # Check that opacity was set
        mock_overlay.set_opacity.assert_called_once_with(0.75)
        # Check that config was saved
        mock_save_config.assert_called_once()
        self.assertEqual(self.gui.config["overlay"]["opacity"], "0.75")
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_change_overlay_opacity_clamping(self, mock_create_overlay):
        """Test that opacity values are clamped."""
        mock_overlay = Mock()
        mock_overlay.set_opacity = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.overlay = mock_overlay
        
        # Test too low
        self.gui.change_overlay_opacity(0.1)
        mock_overlay.set_opacity.assert_called_with(0.3)  # Should clamp
        
        # Test too high
        self.gui.change_overlay_opacity(1.5)
        mock_overlay.set_opacity.assert_called_with(1.0)  # Should clamp
    
    def test_update_statistics_display_with_overlay(self):
        """Test that statistics display updates overlay."""
        # Create overlay mock
        mock_overlay = Mock()
        mock_overlay.is_visible = True
        mock_overlay.update_stats = Mock()
        
        self.gui.overlay = mock_overlay
        
        # Mock UI elements
        self.gui.kills_label = Mock()
        self.gui.deaths_label = Mock()
        self.gui.kd_ratio_label = Mock()
        self.gui.streak_label = Mock()
        self.gui.weapons_tree = Mock()
        self.gui.recent_tree = Mock()
        self.gui.weapons_tree.get_children = Mock(return_value=[])
        self.gui.recent_tree.get_children = Mock(return_value=[])
        
        # Update stats
        self.gui.stats["total_kills"] = 5
        self.gui.stats["total_deaths"] = 2
        self.gui.update_statistics_display()
        
        # Check that overlay was updated
        mock_overlay.update_stats.assert_called_once()
    
    def test_update_statistics_display_overlay_hidden(self):
        """Test that hidden overlay is not updated."""
        mock_overlay = Mock()
        mock_overlay.is_visible = False
        mock_overlay.update_stats = Mock()
        
        self.gui.overlay = mock_overlay
        
        # Mock UI elements
        self.gui.kills_label = Mock()
        self.gui.deaths_label = Mock()
        self.gui.kd_ratio_label = Mock()
        self.gui.streak_label = Mock()
        self.gui.weapons_tree = Mock()
        self.gui.recent_tree = Mock()
        self.gui.weapons_tree.get_children = Mock(return_value=[])
        self.gui.recent_tree.get_children = Mock(return_value=[])
        
        # Update stats
        self.gui.update_statistics_display()
        
        # Overlay should not be updated when hidden
        mock_overlay.update_stats.assert_not_called()
    
    @patch('sc_kill_feed_gui.create_overlay')
    def test_start_overlay_updates(self, mock_create_overlay):
        """Test starting overlay update loop."""
        mock_overlay = Mock()
        mock_overlay.is_visible = True
        mock_overlay.update_stats = Mock()
        mock_create_overlay.return_value = mock_overlay
        
        self.gui.overlay = mock_overlay
        self.gui._start_overlay_updates()
        
        # Check that update_stats was called
        mock_overlay.update_stats.assert_called()


if __name__ == "__main__":
    unittest.main()

