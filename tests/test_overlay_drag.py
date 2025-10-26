#!/usr/bin/env python3
"""
Test suite for overlay drag functionality
Tests all aspects of the draggable overlay feature
"""

import unittest
import tkinter as tk
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sc_kill_feed_gui import StatisticsOverlay, StarCitizenKillFeedGUI

# Check if running in headless environment
SKIP_TESTS = os.environ.get('DISPLAY') is None and sys.platform != 'win32'


class TestOverlayDrag(unittest.TestCase):
    """Test cases for overlay drag functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        if SKIP_TESTS:
            self.skipTest("Skipping GUI tests in headless environment")
        
        try:
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the main window during tests
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
    
    def test_drag_data_initialization(self):
        """Test that drag data is properly initialized"""
        self.assertEqual(self.overlay._drag_data, {"x": 0, "y": 0})
        self.assertFalse(self.overlay.is_locked)
        self.assertIsNone(self.overlay.custom_x)
        self.assertIsNone(self.overlay.custom_y)
    
    def test_custom_position_properties(self):
        """Test custom position properties are initialized"""
        self.assertIsNone(self.overlay.custom_x)
        self.assertIsNone(self.overlay.custom_y)
        self.assertEqual(self.overlay.position, "top_right")
    
    def test_overlay_creation_with_drag_handlers(self):
        """Test that overlay window is created with drag event handlers"""
        self.overlay.create_overlay()
        
        # Check that overlay window exists
        self.assertIsNotNone(self.overlay.overlay_window)
        
        # Check that drag event handlers are bound
        bindings = self.overlay.overlay_window.bind()
        self.assertIn('<Button-1>', bindings)
        self.assertIn('<B1-Motion>', bindings)
        self.assertIn('<ButtonRelease-1>', bindings)
    
    def test_lock_button_creation(self):
        """Test that lock button is created in overlay"""
        self.overlay.create_overlay()
        
        # Check that lock button exists
        self.assertIsNotNone(self.overlay.lock_button)
        self.assertEqual(self.overlay.lock_button['text'], '🔒')
    
    def test_start_drag_when_unlocked(self):
        """Test starting drag when overlay is unlocked"""
        self.overlay.is_locked = False
        
        # Mock event with coordinates
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        
        self.overlay._start_drag(mock_event)
        
        # Check that drag data is set
        self.assertEqual(self.overlay._drag_data["x"], 100)
        self.assertEqual(self.overlay._drag_data["y"], 200)
    
    def test_start_drag_when_locked(self):
        """Test that drag doesn't start when overlay is locked"""
        self.overlay.is_locked = True
        
        # Mock event with coordinates
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        
        self.overlay._start_drag(mock_event)
        
        # Check that drag data is NOT set
        self.assertEqual(self.overlay._drag_data["x"], 0)
        self.assertEqual(self.overlay._drag_data["y"], 0)
    
    def test_on_drag_when_unlocked(self):
        """Test dragging when overlay is unlocked"""
        self.overlay.is_locked = False
        self.overlay.create_overlay()
        
        # Set initial drag data
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock event with new coordinates
        mock_event = Mock()
        mock_event.x_root = 150  # 50 pixels right
        mock_event.y_root = 250  # 50 pixels down
        
        # Mock geometry method to return current position
        self.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.overlay._on_drag(mock_event)
        
        # Check that position was updated
        self.overlay.overlay_window.geometry.assert_called()
        
        # Check that position was set to custom
        self.assertEqual(self.overlay.position, "custom")
        self.assertIsNotNone(self.overlay.custom_x)
        self.assertIsNotNone(self.overlay.custom_y)
    
    def test_on_drag_when_locked(self):
        """Test that dragging doesn't work when locked"""
        self.overlay.is_locked = True
        self.overlay.create_overlay()
        
        # Set initial drag data
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock event
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry method
        self.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.overlay._on_drag(mock_event)
        
        # Check that geometry was NOT called (no movement)
        self.overlay.overlay_window.geometry.assert_not_called()
    
    def test_stop_drag(self):
        """Test stopping drag operation"""
        # Set some drag data
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        mock_event = Mock()
        self.overlay._stop_drag(mock_event)
        
        # Check that drag data is reset
        self.assertEqual(self.overlay._drag_data["x"], 0)
        self.assertEqual(self.overlay._drag_data["y"], 0)
    
    def test_position_calculation_with_custom_coordinates(self):
        """Test position calculation when custom coordinates are set"""
        self.overlay.position = "custom"
        self.overlay.custom_x = 300
        self.overlay.custom_y = 400
        self.overlay.create_overlay()
        
        # Mock screen dimensions
        self.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        self.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        self.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        self.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        self.overlay.overlay_window.update_idletasks = Mock()
        
        # Mock geometry method
        self.overlay.overlay_window.geometry = Mock()
        
        self.overlay._position_overlay()
        
        # Check that custom coordinates were used
        self.overlay.overlay_window.geometry.assert_called_with("200x100+300+400")
    
    def test_drag_with_no_drag_data(self):
        """Test dragging when no initial drag data is set"""
        self.overlay.is_locked = False
        self.overlay._drag_data = {"x": 0, "y": 0}
        
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Should not cause any issues
        self.overlay._on_drag(mock_event)
        
        # Position should remain unchanged
        self.assertEqual(self.overlay.position, "top_right")
    
    def test_save_throttling(self):
        """Test that configuration saves are throttled during drag"""
        self.overlay.is_locked = False
        self.overlay.create_overlay()
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock geometry
        self.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        # Create multiple drag events quickly
        for i in range(5):
            mock_event = Mock()
            mock_event.x_root = 100 + i
            mock_event.y_root = 200 + i
            self.overlay._on_drag(mock_event)
            time.sleep(0.1)  # Small delay
        
        # Should not save more than once per 500ms
        # The exact count depends on timing, but should be throttled
        self.assertLessEqual(self.mock_parent.save_config.call_count, 3)


class TestDragIntegration(unittest.TestCase):
    """Integration tests for drag functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if SKIP_TESTS:
            self.skipTest("Skipping GUI tests in headless environment")
        
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError:
            self.skipTest("No display available for GUI tests")
        
        # Create full GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after integration tests"""
        if hasattr(self, 'gui') and hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_drag_with_position_info_update(self):
        """Test that position info is updated during drag"""
        self.gui.overlay.create_overlay()
        self.gui.overlay.is_locked = False
        
        # Set initial drag data
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        # Mock event
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock the update_position_info method
        self.gui.update_position_info = Mock()
        
        self.gui.overlay._on_drag(mock_event)
        
        # Check that position info was updated
        self.gui.update_position_info.assert_called()
    
    def test_preset_position_clears_custom_coordinates(self):
        """Test that using preset position clears custom coordinates"""
        # Set custom coordinates
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        self.gui.overlay.position = "custom"
        
        # Use preset position
        self.gui.update_overlay_position("top_left")
        
        # Check that custom coordinates are cleared
        self.assertIsNone(self.gui.overlay.custom_x)
        self.assertIsNone(self.gui.overlay.custom_y)
        self.assertEqual(self.gui.overlay.position, "top_left")


if __name__ == '__main__':
    unittest.main()
