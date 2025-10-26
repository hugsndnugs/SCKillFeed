#!/usr/bin/env python3
"""
Test suite for overlay position persistence
Tests saving and loading of custom positions
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

from sc_kill_feed_gui import StatisticsOverlay, StarCitizenKillFeedGUI

# Check if running in headless environment
SKIP_TESTS = os.environ.get('DISPLAY') is None and sys.platform != 'win32'


class TestPositionPersistence(unittest.TestCase):
    """Test cases for position persistence functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if SKIP_TESTS:
            self.skipTest("Skipping GUI tests in headless environment")
        
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("No display available for GUI tests")
        
        # Create a mock parent GUI
        self.mock_parent = Mock()
        self.mock_parent.root = self.root
        self.mock_parent.save_config = Mock()
        self.mock_parent.update_position_info = Mock()
        
        # Create overlay instance
        self.overlay = StatisticsOverlay(self.mock_parent)
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'overlay') and hasattr(self.overlay, 'overlay_window') and self.overlay.overlay_window:
            self.overlay.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_custom_position_initialization(self):
        """Test that custom position properties are initialized correctly"""
        self.assertIsNone(self.overlay.custom_x)
        self.assertIsNone(self.overlay.custom_y)
        self.assertEqual(self.overlay.position, "top_right")
    
    def test_custom_position_setting_during_drag(self):
        """Test that custom position is set during drag"""
        self.overlay.is_locked = False
        self.overlay.create_overlay()
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock geometry
        self.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        # Mock event
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        self.overlay._on_drag(mock_event)
        
        # Check that position was set to custom
        self.assertEqual(self.overlay.position, "custom")
        self.assertIsNotNone(self.overlay.custom_x)
        self.assertIsNotNone(self.overlay.custom_y)
    
    def test_preset_position_clears_custom_coordinates(self):
        """Test that using preset position clears custom coordinates"""
        # Set custom coordinates
        self.overlay.custom_x = 300
        self.overlay.custom_y = 400
        self.overlay.position = "custom"
        
        # Use preset position
        self.overlay.position = "top_left"
        
        # Check that custom coordinates are cleared
        self.assertIsNone(self.overlay.custom_x)
        self.assertIsNone(self.overlay.custom_y)
        self.assertEqual(self.overlay.position, "top_left")
    
    def test_position_calculation_with_custom_coordinates(self):
        """Test position calculation when custom coordinates are set"""
        self.overlay.position = "custom"
        self.overlay.custom_x = 300
        self.overlay.custom_y = 400
        self.overlay.create_overlay()
        
        # Mock screen dimensions and geometry
        self.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        self.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        self.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        self.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        self.overlay.overlay_window.update_idletasks = Mock()
        self.overlay.overlay_window.geometry = Mock()
        
        self.overlay._position_overlay()
        
        # Check that custom coordinates were used
        self.overlay.overlay_window.geometry.assert_called_with("200x100+300+400")
    
    def test_position_calculation_without_custom_coordinates(self):
        """Test position calculation when custom coordinates are not set"""
        self.overlay.position = "custom"
        self.overlay.custom_x = None
        self.overlay.custom_y = None
        self.overlay.create_overlay()
        
        # Mock screen dimensions and geometry
        self.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        self.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        self.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        self.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        self.overlay.overlay_window.update_idletasks = Mock()
        self.overlay.overlay_window.geometry = Mock()
        
        self.overlay._position_overlay()
        
        # Should fall back to default position (top_right)
        self.overlay.overlay_window.geometry.assert_called_with("200x100+1710+10")
    
    def test_all_preset_positions(self):
        """Test all preset position calculations"""
        self.overlay.create_overlay()
        
        # Mock screen dimensions
        self.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        self.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        self.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        self.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        self.overlay.overlay_window.update_idletasks = Mock()
        self.overlay.overlay_window.geometry = Mock()
        
        # Test each preset position
        positions = {
            "top_left": "200x100+10+10",
            "top_right": "200x100+1710+10",
            "bottom_left": "200x100+10+970",
            "bottom_right": "200x100+1710+970",
            "center": "200x100+860+490"
        }
        
        for position, expected_geometry in positions.items():
            self.overlay.position = position
            self.overlay._position_overlay()
            self.overlay.overlay_window.geometry.assert_called_with(expected_geometry)


class TestPositionConfiguration(unittest.TestCase):
    """Test cases for position configuration saving/loading"""
    
    def setUp(self):
        """Set up test fixtures"""
        if SKIP_TESTS:
            self.skipTest("Skipping GUI tests in headless environment")
        
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("No display available for GUI tests")
        
        # Create GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'gui') and hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_save_custom_position_config(self):
        """Test saving custom position to configuration"""
        # Set custom position
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that custom coordinates were saved
        self.assertIn("overlay", self.gui.config)
        self.assertEqual(self.gui.config["overlay"]["position"], "custom")
        self.assertEqual(self.gui.config["overlay"]["custom_x"], "300")
        self.assertEqual(self.gui.config["overlay"]["custom_y"], "400")
    
    def test_save_preset_position_config(self):
        """Test saving preset position to configuration"""
        # Set preset position
        self.gui.overlay.position = "top_left"
        self.gui.overlay.custom_x = None
        self.gui.overlay.custom_y = None
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that preset position was saved
        self.assertIn("overlay", self.gui.config)
        self.assertEqual(self.gui.config["overlay"]["position"], "top_left")
        # Custom coordinates should not be saved for preset positions
        self.assertNotIn("custom_x", self.gui.config["overlay"])
        self.assertNotIn("custom_y", self.gui.config["overlay"])
    
    def test_load_custom_position_config(self):
        """Test loading custom position from configuration"""
        # Set up configuration with custom position
        self.gui.config["overlay"] = {
            "position": "custom",
            "custom_x": "300",
            "custom_y": "400"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that custom position was loaded
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertEqual(self.gui.overlay.custom_x, 300)
        self.assertEqual(self.gui.overlay.custom_y, 400)
    
    def test_load_preset_position_config(self):
        """Test loading preset position from configuration"""
        # Set up configuration with preset position
        self.gui.config["overlay"] = {
            "position": "bottom_right"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Check that preset position was loaded
        self.assertEqual(self.gui.overlay.position, "bottom_right")
        self.assertIsNone(self.gui.overlay.custom_x)
        self.assertIsNone(self.gui.overlay.custom_y)
    
    def test_load_invalid_custom_coordinates(self):
        """Test loading invalid custom coordinates"""
        # Set up configuration with invalid coordinates
        self.gui.config["overlay"] = {
            "position": "custom",
            "custom_x": "invalid",
            "custom_y": "also_invalid"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Should handle invalid coordinates gracefully
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertIsNone(self.gui.overlay.custom_x)
        self.assertIsNone(self.gui.overlay.custom_y)
    
    def test_load_missing_custom_coordinates(self):
        """Test loading when custom coordinates are missing"""
        # Set up configuration with custom position but missing coordinates
        self.gui.config["overlay"] = {
            "position": "custom"
        }
        
        # Load configuration
        self.gui.load_overlay_config()
        
        # Should handle missing coordinates gracefully
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertIsNone(self.gui.overlay.custom_x)
        self.assertIsNone(self.gui.overlay.custom_y)
    
    def test_position_info_display_update(self):
        """Test that position info display is updated correctly"""
        # Test preset position display
        self.gui.overlay.position = "top_left"
        self.gui.update_position_info()
        
        if hasattr(self.gui, 'position_info_label'):
            self.assertIn("Top Left", self.gui.position_info_label['text'])
        
        # Test custom position display
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        self.gui.update_position_info()
        
        if hasattr(self.gui, 'position_info_label'):
            self.assertIn("Custom position (300, 400)", self.gui.position_info_label['text'])
            self.assertEqual(self.gui.position_info_label['fg'], '#00ff88')


class TestPositionIntegration(unittest.TestCase):
    """Integration tests for position functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if SKIP_TESTS:
            self.skipTest("Skipping GUI tests in headless environment")
        
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("No display available for GUI tests")
        
        # Create GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after integration tests"""
        if hasattr(self, 'gui') and hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_complete_drag_to_custom_position_workflow(self):
        """Test complete workflow from drag to custom position"""
        self.gui.overlay.create_overlay()
        self.gui.overlay.is_locked = False
        
        # Start drag
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        # Continue drag
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        
        # Stop drag
        self.gui.overlay._stop_drag(mock_event)
        
        # Check final state
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertIsNotNone(self.gui.overlay.custom_x)
        self.assertIsNotNone(self.gui.overlay.custom_y)
        
        # Check that configuration was saved
        self.gui.save_overlay_config()
        self.assertIn("overlay", self.gui.config)
        self.assertEqual(self.gui.config["overlay"]["position"], "custom")
    
    def test_preset_position_button_workflow(self):
        """Test workflow using preset position buttons"""
        # Test each preset position button
        positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        
        for position in positions:
            # Set some custom coordinates first
            self.gui.overlay.custom_x = 300
            self.gui.overlay.custom_y = 400
            self.gui.overlay.position = "custom"
            
            # Use preset position
            self.gui.update_overlay_position(position)
            
            # Check that position changed and custom coordinates cleared
            self.assertEqual(self.gui.overlay.position, position)
            self.assertIsNone(self.gui.overlay.custom_x)
            self.assertIsNone(self.gui.overlay.custom_y)
    
    def test_position_persistence_across_sessions(self):
        """Test that position persists across application sessions"""
        # Set custom position
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Create new GUI instance (simulating new session)
        new_gui = StarCitizenKillFeedGUI()
        
        # Load configuration
        new_gui.config = self.gui.config
        new_gui.load_overlay_config()
        
        # Check that position was restored
        self.assertEqual(new_gui.overlay.position, "custom")
        self.assertEqual(new_gui.overlay.custom_x, 300)
        self.assertEqual(new_gui.overlay.custom_y, 400)
        
        # Clean up
        if hasattr(new_gui, 'overlay') and new_gui.overlay.overlay_window:
            new_gui.overlay.destroy()
        new_gui.root.destroy()


if __name__ == '__main__':
    unittest.main()
