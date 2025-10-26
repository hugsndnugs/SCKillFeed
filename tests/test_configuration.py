#!/usr/bin/env python3
"""
Test suite for configuration saving and loading
Tests all aspects of configuration persistence
"""

import unittest
import tkinter as tk
import sys
import os
import tempfile
import configparser
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sc_kill_feed_gui import StarCitizenKillFeedGUI


class TestConfigurationSaving(unittest.TestCase):
    """Test cases for configuration saving functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        self.gui.root.destroy()
    
    def test_save_overlay_config_structure(self):
        """Test that overlay configuration is saved with proper structure"""
        # Set various overlay settings
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        self.gui.overlay.transparency = 0.7
        self.gui.overlay.is_always_on_top = False
        self.gui.overlay.update_interval = 2000
        self.gui.overlay.is_locked = True
        
        # Set statistics visibility
        self.gui.overlay.show_stats = {
            "kills": True,
            "deaths": False,
            "kd_ratio": True,
            "current_streak": False,
            "max_kill_streak": True,
            "time_since_last": False,
            "top_weapon": True
        }
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that overlay section exists
        self.assertIn("overlay", self.gui.config)
        overlay_config = self.gui.config["overlay"]
        
        # Check all settings were saved
        self.assertEqual(overlay_config["position"], "custom")
        self.assertEqual(overlay_config["custom_x"], "300")
        self.assertEqual(overlay_config["custom_y"], "400")
        self.assertEqual(overlay_config["transparency"], "0.7")
        self.assertEqual(overlay_config["always_on_top"], "False")
        self.assertEqual(overlay_config["update_interval"], "2000")
        self.assertEqual(overlay_config["is_locked"], "True")
        
        # Check statistics visibility
        self.assertEqual(overlay_config["show_kills"], "True")
        self.assertEqual(overlay_config["show_deaths"], "False")
        self.assertEqual(overlay_config["show_kd_ratio"], "True")
        self.assertEqual(overlay_config["show_current_streak"], "False")
        self.assertEqual(overlay_config["show_max_kill_streak"], "True")
        self.assertEqual(overlay_config["show_time_since_last"], "False")
        self.assertEqual(overlay_config["show_top_weapon"], "True")
    
    def test_save_overlay_config_without_custom_coordinates(self):
        """Test saving overlay config when custom coordinates are not set"""
        # Set preset position without custom coordinates
        self.gui.overlay.position = "top_left"
        self.gui.overlay.custom_x = None
        self.gui.overlay.custom_y = None
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that preset position was saved
        overlay_config = self.gui.config["overlay"]
        self.assertEqual(overlay_config["position"], "top_left")
        
        # Custom coordinates should not be saved
        self.assertNotIn("custom_x", overlay_config)
        self.assertNotIn("custom_y", overlay_config)
    
    def test_save_config_creates_overlay_section(self):
        """Test that save_config creates overlay section if it doesn't exist"""
        # Ensure overlay section doesn't exist
        if "overlay" in self.gui.config:
            del self.gui.config["overlay"]
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that overlay section was created
        self.assertIn("overlay", self.gui.config)
    
    def test_save_config_preserves_existing_settings(self):
        """Test that save_config preserves existing overlay settings"""
        # Set up existing configuration
        self.gui.config["overlay"] = {
            "position": "bottom_right",
            "transparency": "0.9",
            "existing_setting": "preserved"
        }
        
        # Change only some settings
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 100
        self.gui.overlay.custom_y = 200
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that existing settings are preserved
        overlay_config = self.gui.config["overlay"]
        self.assertEqual(overlay_config["existing_setting"], "preserved")
        self.assertEqual(overlay_config["transparency"], "0.9")
        
        # Check that new settings were added
        self.assertEqual(overlay_config["position"], "custom")
        self.assertEqual(overlay_config["custom_x"], "100")
        self.assertEqual(overlay_config["custom_y"], "200")


class TestConfigurationLoading(unittest.TestCase):
    """Test cases for configuration loading functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        self.gui.root.destroy()
    
    def test_load_overlay_config_complete(self):
        """Test loading complete overlay configuration"""
        # Set up complete configuration
        self.gui.config["overlay"] = {
            "position": "custom",
            "custom_x": "300",
            "custom_y": "400",
            "transparency": "0.7",
            "always_on_top": "False",
            "update_interval": "2000",
            "is_locked": "True",
            "show_kills": "True",
            "show_deaths": "False",
            "show_kd_ratio": "True",
            "show_current_streak": "False",
            "show_max_kill_streak": "True",
            "show_time_since_last": "False",
            "show_top_weapon": "True"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that all settings were loaded
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertEqual(self.gui.overlay.custom_x, 300)
        self.assertEqual(self.gui.overlay.custom_y, 400)
        self.assertEqual(self.gui.overlay.transparency, 0.7)
        self.assertFalse(self.gui.overlay.is_always_on_top)
        self.assertEqual(self.gui.overlay.update_interval, 2000)
        self.assertTrue(self.gui.overlay.is_locked)
        
        # Check statistics visibility
        self.assertTrue(self.gui.overlay.show_stats["kills"])
        self.assertFalse(self.gui.overlay.show_stats["deaths"])
        self.assertTrue(self.gui.overlay.show_stats["kd_ratio"])
        self.assertFalse(self.gui.overlay.show_stats["current_streak"])
        self.assertTrue(self.gui.overlay.show_stats["max_kill_streak"])
        self.assertFalse(self.gui.overlay.show_stats["time_since_last"])
        self.assertTrue(self.gui.overlay.show_stats["top_weapon"])
    
    def test_load_overlay_config_with_defaults(self):
        """Test loading overlay config with missing values using defaults"""
        # Set up minimal configuration
        self.gui.config["overlay"] = {
            "position": "top_right"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that defaults were used for missing values
        self.assertEqual(self.gui.overlay.position, "top_right")
        self.assertEqual(self.gui.overlay.transparency, 0.8)  # Default
        self.assertTrue(self.gui.overlay.is_always_on_top)  # Default
        self.assertEqual(self.gui.overlay.update_interval, 1000)  # Default
        self.assertFalse(self.gui.overlay.is_locked)  # Default
        
        # Check that all statistics are shown by default
        for stat_name, is_shown in self.gui.overlay.show_stats.items():
            self.assertTrue(is_shown, f"Default for {stat_name} should be True")
    
    def test_load_overlay_config_invalid_values(self):
        """Test loading overlay config with invalid values"""
        # Set up configuration with invalid values
        self.gui.config["overlay"] = {
            "position": "invalid_position",
            "transparency": "invalid_float",
            "always_on_top": "invalid_bool",
            "update_interval": "invalid_int",
            "is_locked": "invalid_bool",
            "custom_x": "invalid_int",
            "custom_y": "invalid_int"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that defaults were used for invalid values
        self.assertEqual(self.gui.overlay.position, "invalid_position")  # Invalid positions are kept as-is
        self.assertEqual(self.gui.overlay.transparency, 0.8)  # Default for invalid float
        self.assertTrue(self.gui.overlay.is_always_on_top)  # Default for invalid bool
        self.assertEqual(self.gui.overlay.update_interval, 1000)  # Default for invalid int
        self.assertFalse(self.gui.overlay.is_locked)  # Default for invalid bool
        self.assertIsNone(self.gui.overlay.custom_x)  # None for invalid int
        self.assertIsNone(self.gui.overlay.custom_y)  # None for invalid int
    
    def test_load_overlay_config_missing_section(self):
        """Test loading when overlay section is missing"""
        # Ensure overlay section doesn't exist
        if "overlay" in self.gui.config:
            del self.gui.config["overlay"]
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that defaults were used
        self.assertEqual(self.gui.overlay.position, "top_right")
        self.assertEqual(self.gui.overlay.transparency, 0.8)
        self.assertTrue(self.gui.overlay.is_always_on_top)
        self.assertEqual(self.gui.overlay.update_interval, 1000)
        self.assertFalse(self.gui.overlay.is_locked)
    
    def test_load_overlay_config_boolean_parsing(self):
        """Test loading boolean values with various formats"""
        # Test different boolean representations
        boolean_tests = [
            ("True", True),
            ("true", True),
            ("TRUE", True),
            ("False", False),
            ("false", False),
            ("FALSE", False),
            ("1", False),  # Should be False for invalid format
            ("0", False),  # Should be False for invalid format
            ("yes", False),  # Should be False for invalid format
            ("no", False),  # Should be False for invalid format
        ]
        
        for bool_str, expected in boolean_tests:
            self.gui.config["overlay"] = {
                "always_on_top": bool_str,
                "is_locked": bool_str
            }
            
            # Load configuration
            self.gui.load_overlay_config()
            
            # Check that boolean was parsed correctly
            self.assertEqual(self.gui.overlay.is_always_on_top, expected)
            self.assertEqual(self.gui.overlay.is_locked, expected)


class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after integration tests"""
        if hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        self.gui.root.destroy()
    
    def test_save_load_roundtrip(self):
        """Test saving and loading configuration maintains all settings"""
        # Set up complex configuration
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        self.gui.overlay.transparency = 0.7
        self.gui.overlay.is_always_on_top = False
        self.gui.overlay.update_interval = 2000
        self.gui.overlay.is_locked = True
        
        # Set statistics visibility
        self.gui.overlay.show_stats = {
            "kills": True,
            "deaths": False,
            "kd_ratio": True,
            "current_streak": False,
            "max_kill_streak": True,
            "time_since_last": False,
            "top_weapon": True
        }
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Create new GUI instance
        new_gui = StarCitizenKillFeedGUI()
        
        # Load configuration
        new_gui.config = self.gui.config
        new_gui.load_overlay_config()
        
        # Check that all settings were preserved
        self.assertEqual(new_gui.overlay.position, "custom")
        self.assertEqual(new_gui.overlay.custom_x, 300)
        self.assertEqual(new_gui.overlay.custom_y, 400)
        self.assertEqual(new_gui.overlay.transparency, 0.7)
        self.assertFalse(new_gui.overlay.is_always_on_top)
        self.assertEqual(new_gui.overlay.update_interval, 2000)
        self.assertTrue(new_gui.overlay.is_locked)
        
        # Check statistics visibility
        self.assertTrue(new_gui.overlay.show_stats["kills"])
        self.assertFalse(new_gui.overlay.show_stats["deaths"])
        self.assertTrue(new_gui.overlay.show_stats["kd_ratio"])
        self.assertFalse(new_gui.overlay.show_stats["current_streak"])
        self.assertTrue(new_gui.overlay.show_stats["max_kill_streak"])
        self.assertFalse(new_gui.overlay.show_stats["time_since_last"])
        self.assertTrue(new_gui.overlay.show_stats["top_weapon"])
        
        # Clean up
        if hasattr(new_gui, 'overlay') and new_gui.overlay.overlay_window:
            new_gui.overlay.destroy()
        new_gui.root.destroy()
    
    def test_configuration_error_handling(self):
        """Test that configuration errors are handled gracefully"""
        # Test with corrupted configuration
        self.gui.config = {"overlay": None}
        
        # Should not raise exception
        try:
            self.gui.load_overlay_config()
        except Exception as e:
            self.fail(f"load_overlay_config raised {type(e).__name__}: {e}")
        
        # Should fall back to defaults
        self.assertEqual(self.gui.overlay.position, "top_right")
        self.assertEqual(self.gui.overlay.transparency, 0.8)
    
    def test_configuration_file_operations(self):
        """Test configuration file read/write operations"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            config_content = """[overlay]
position = custom
custom_x = 300
custom_y = 400
transparency = 0.7
always_on_top = False
update_interval = 2000
is_locked = True
show_kills = True
show_deaths = False
"""
            f.write(config_content)
            temp_config_path = f.name
        
        try:
            # Test reading configuration file
            config = configparser.ConfigParser()
            config.read(temp_config_path)
            
            # Verify content was read correctly
            self.assertIn("overlay", config)
            overlay_section = config["overlay"]
            self.assertEqual(overlay_section["position"], "custom")
            self.assertEqual(overlay_section["custom_x"], "300")
            self.assertEqual(overlay_section["custom_y"], "400")
            self.assertEqual(overlay_section["transparency"], "0.7")
            self.assertEqual(overlay_section["always_on_top"], "False")
            self.assertEqual(overlay_section["update_interval"], "2000")
            self.assertEqual(overlay_section["is_locked"], "True")
            self.assertEqual(overlay_section["show_kills"], "True")
            self.assertEqual(overlay_section["show_deaths"], "False")
            
        finally:
            # Clean up temporary file
            os.unlink(temp_config_path)


if __name__ == '__main__':
    unittest.main()
