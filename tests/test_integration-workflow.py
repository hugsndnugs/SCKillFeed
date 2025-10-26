#!/usr/bin/env python3
"""
Integration test suite for complete drag and lock workflow
Tests the entire user experience from start to finish
"""

import unittest
import tkinter as tk
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sc_kill_feed_gui import StarCitizenKillFeedGUI

# Check if running in headless environment
SKIP_TESTS = os.environ.get('DISPLAY') is None and sys.platform != 'win32'


class TestCompleteWorkflow(unittest.TestCase):
    """Integration tests for complete drag and lock workflow"""
    
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
    
    def test_complete_drag_and_lock_workflow(self):
        """Test complete workflow: create overlay, drag to position, lock, unlock, drag again"""
        # Step 1: Create overlay
        self.gui.overlay.create_overlay()
        self.assertIsNotNone(self.gui.overlay.overlay_window)
        
        # Step 2: Verify initial state
        self.assertFalse(self.gui.overlay.is_locked)
        self.assertEqual(self.gui.overlay.position, "top_right")
        self.assertIsNone(self.gui.overlay.custom_x)
        self.assertIsNone(self.gui.overlay.custom_y)
        
        # Step 3: Start dragging
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        # Verify drag started
        self.assertEqual(self.gui.overlay._drag_data["x"], 100)
        self.assertEqual(self.gui.overlay._drag_data["y"], 200)
        
        # Step 4: Continue dragging
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        
        # Verify position changed to custom
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertIsNotNone(self.gui.overlay.custom_x)
        self.assertIsNotNone(self.gui.overlay.custom_y)
        
        # Step 5: Stop dragging
        self.gui.overlay._stop_drag(mock_event)
        
        # Verify drag stopped
        self.assertEqual(self.gui.overlay._drag_data["x"], 0)
        self.assertEqual(self.gui.overlay._drag_data["y"], 0)
        
        # Step 6: Lock the overlay
        self.gui.overlay.toggle_lock()
        
        # Verify locked state
        self.assertTrue(self.gui.overlay.is_locked)
        self.assertEqual(self.gui.overlay.lock_button['text'], '🔓')
        
        # Step 7: Try to drag while locked (should fail)
        mock_event.x_root = 200
        mock_event.y_root = 300
        self.gui.overlay._start_drag(mock_event)
        
        # Verify drag didn't start
        self.assertEqual(self.gui.overlay._drag_data["x"], 0)
        self.assertEqual(self.gui.overlay._drag_data["y"], 0)
        
        # Step 8: Unlock the overlay
        self.gui.overlay.toggle_lock()
        
        # Verify unlocked state
        self.assertFalse(self.gui.overlay.is_locked)
        self.assertEqual(self.gui.overlay.lock_button['text'], '🔒')
        
        # Step 9: Drag again (should work)
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        # Verify drag started
        self.assertEqual(self.gui.overlay._drag_data["x"], 100)
        self.assertEqual(self.gui.overlay._drag_data["y"], 200)
    
    def test_preset_position_workflow(self):
        """Test workflow using preset position buttons"""
        # Create overlay
        self.gui.overlay.create_overlay()
        
        # Test each preset position
        positions = [
            ("top_left", "Top Left"),
            ("top_right", "Top Right"),
            ("bottom_left", "Bottom Left"),
            ("bottom_right", "Bottom Right"),
            ("center", "Center")
        ]
        
        for position, display_name in positions:
            # Set some custom coordinates first
            self.gui.overlay.custom_x = 300
            self.gui.overlay.custom_y = 400
            self.gui.overlay.position = "custom"
            
            # Use preset position
            self.gui.update_overlay_position(position)
            
            # Verify position changed and custom coordinates cleared
            self.assertEqual(self.gui.overlay.position, position)
            self.assertIsNone(self.gui.overlay.custom_x)
            self.assertIsNone(self.gui.overlay.custom_y)
            
            # Verify position info display updated
            if hasattr(self.gui, 'position_info_label'):
                self.assertIn(display_name, self.gui.position_info_label['text'])
    
    def test_configuration_persistence_workflow(self):
        """Test complete configuration persistence workflow"""
        # Step 1: Set up complex configuration
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
        
        # Step 2: Save configuration
        self.gui.save_overlay_config()
        
        # Verify configuration was saved
        self.assertIn("overlay", self.gui.config)
        overlay_config = self.gui.config["overlay"]
        self.assertEqual(overlay_config["position"], "custom")
        self.assertEqual(overlay_config["custom_x"], "300")
        self.assertEqual(overlay_config["custom_y"], "400")
        self.assertEqual(overlay_config["transparency"], "0.7")
        self.assertEqual(overlay_config["always_on_top"], "False")
        self.assertEqual(overlay_config["update_interval"], "2000")
        self.assertEqual(overlay_config["is_locked"], "True")
        
        # Step 3: Create new GUI instance (simulate app restart)
        new_gui = StarCitizenKillFeedGUI()
        
        # Step 4: Load configuration
        new_gui.config = self.gui.config
        new_gui.load_overlay_config()
        
        # Step 5: Verify all settings were restored
        self.assertEqual(new_gui.overlay.position, "custom")
        self.assertEqual(new_gui.overlay.custom_x, 300)
        self.assertEqual(new_gui.overlay.custom_y, 400)
        self.assertEqual(new_gui.overlay.transparency, 0.7)
        self.assertFalse(new_gui.overlay.is_always_on_top)
        self.assertEqual(new_gui.overlay.update_interval, 2000)
        self.assertTrue(new_gui.overlay.is_locked)
        
        # Verify statistics visibility
        self.assertTrue(new_gui.overlay.show_stats["kills"])
        self.assertFalse(new_gui.overlay.show_stats["deaths"])
        self.assertTrue(new_gui.overlay.show_stats["kd_ratio"])
        self.assertFalse(new_gui.overlay.show_stats["current_streak"])
        self.assertTrue(new_gui.overlay.show_stats["max_kill_streak"])
        self.assertFalse(new_gui.overlay.show_stats["time_since_last"])
        self.assertTrue(new_gui.overlay.show_stats["top_weapon"])
        
        # Step 6: Create overlay and verify position
        new_gui.overlay.create_overlay()
        
        # Mock screen dimensions and geometry
        new_gui.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        new_gui.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        new_gui.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        new_gui.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        new_gui.overlay.overlay_window.update_idletasks = Mock()
        new_gui.overlay.overlay_window.geometry = Mock()
        
        new_gui.overlay._position_overlay()
        
        # Verify custom position was used
        new_gui.overlay.overlay_window.geometry.assert_called_with("200x100+300+400")
        
        # Clean up
        if hasattr(new_gui, 'overlay') and new_gui.overlay.overlay_window:
            new_gui.overlay.destroy()
        new_gui.root.destroy()
    
    def test_ui_synchronization_workflow(self):
        """Test that UI elements stay synchronized during operations"""
        # Create overlay
        self.gui.overlay.create_overlay()
        
        # Test position info synchronization
        self.gui.overlay.position = "custom"
        self.gui.overlay.custom_x = 300
        self.gui.overlay.custom_y = 400
        
        self.gui.update_position_info()
        
        if hasattr(self.gui, 'position_info_label'):
            self.assertIn("Custom position (300, 400)", self.gui.position_info_label['text'])
            self.assertEqual(self.gui.position_info_label['fg'], '#00ff88')
        
        # Test lock status synchronization
        self.gui.overlay.is_locked = True
        self.gui.update_lock_status()
        
        if hasattr(self.gui, 'lock_status_label'):
            self.assertIn("Locked", self.gui.lock_status_label['text'])
            self.assertEqual(self.gui.lock_status_label['fg'], '#00ff88')
        
        if hasattr(self.gui, 'lock_toggle_btn'):
            self.assertIn("Unlock", self.gui.lock_toggle_btn['text'])
        
        # Test unlock status synchronization
        self.gui.overlay.is_locked = False
        self.gui.update_lock_status()
        
        if hasattr(self.gui, 'lock_status_label'):
            self.assertIn("Unlocked", self.gui.lock_status_label['text'])
            self.assertEqual(self.gui.lock_status_label['fg'], '#b0b0b0')
        
        if hasattr(self.gui, 'lock_toggle_btn'):
            self.assertIn("Lock", self.gui.lock_toggle_btn['text'])
    
    def test_error_recovery_workflow(self):
        """Test that the system recovers gracefully from errors"""
        # Test with invalid drag data
        self.gui.overlay.create_overlay()
        self.gui.overlay.is_locked = False
        self.gui.overlay._drag_data = {"x": 0, "y": 0}  # Invalid drag data
        
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Should not cause errors
        try:
            self.gui.overlay._on_drag(mock_event)
        except Exception as e:
            self.fail(f"_on_drag raised {type(e).__name__}: {e}")
        
        # Test with invalid geometry string
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        self.gui.overlay.overlay_window.geometry = Mock(return_value="invalid_geometry")
        
        # Should not cause errors
        try:
            self.gui.overlay._on_drag(mock_event)
        except Exception as e:
            self.fail(f"_on_drag with invalid geometry raised {type(e).__name__}: {e}")
        
        # Test with missing UI elements
        if hasattr(self.gui.overlay, 'lock_button'):
            del self.gui.overlay.lock_button
        
        # Should not cause errors
        try:
            self.gui.overlay.toggle_lock()
        except Exception as e:
            self.fail(f"toggle_lock with missing button raised {type(e).__name__}: {e}")
    
    def test_performance_workflow(self):
        """Test performance characteristics of drag operations"""
        self.gui.overlay.create_overlay()
        self.gui.overlay.is_locked = False
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        # Test rapid drag events
        start_time = time.time()
        
        for i in range(100):
            mock_event = Mock()
            mock_event.x_root = 100 + i
            mock_event.y_root = 200 + i
            self.gui.overlay._drag_data = {"x": 100 + i - 1, "y": 200 + i - 1}
            self.gui.overlay._on_drag(mock_event)
        
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 100 operations)
        self.assertLess(end_time - start_time, 1.0)
        
        # Verify throttling worked (should not save config 100 times)
        self.assertLess(self.gui.save_config.call_count, 50)  # Should be throttled
    
    def test_concurrent_operations_workflow(self):
        """Test handling of concurrent operations"""
        self.gui.overlay.create_overlay()
        
        # Test rapid lock/unlock operations
        for i in range(10):
            self.gui.overlay.toggle_lock()
            self.assertEqual(self.gui.overlay.is_locked, i % 2 == 1)
        
        # Test rapid position changes
        positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        for i in range(20):
            position = positions[i % len(positions)]
            self.gui.update_overlay_position(position)
            self.assertEqual(self.gui.overlay.position, position)
        
        # Test rapid drag operations
        self.gui.overlay.is_locked = False
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        for i in range(50):
            mock_event = Mock()
            mock_event.x_root = 100 + i
            mock_event.y_root = 200 + i
            self.gui.overlay._on_drag(mock_event)
        
        # Should handle all operations without errors
        self.assertEqual(self.gui.overlay.position, "custom")


class TestUserExperienceWorkflow(unittest.TestCase):
    """Test cases focused on user experience scenarios"""
    
    def setUp(self):
        """Set up user experience test fixtures"""
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
        """Clean up after user experience tests"""
        if hasattr(self, 'gui') and hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        if hasattr(self, 'root'):
            self.root.destroy()
    
    def test_first_time_user_workflow(self):
        """Test workflow for a first-time user"""
        # User opens app for first time
        self.assertEqual(self.gui.overlay.position, "top_right")  # Default position
        self.assertFalse(self.gui.overlay.is_locked)  # Default unlocked
        
        # User shows overlay
        self.gui.overlay.create_overlay()
        self.assertIsNotNone(self.gui.overlay.overlay_window)
        
        # User drags overlay to desired position
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        self.gui.overlay._stop_drag(mock_event)
        
        # User locks overlay
        self.gui.overlay.toggle_lock()
        
        # Verify final state
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertTrue(self.gui.overlay.is_locked)
        self.assertIsNotNone(self.gui.overlay.custom_x)
        self.assertIsNotNone(self.gui.overlay.custom_y)
    
    def test_returning_user_workflow(self):
        """Test workflow for a returning user with saved preferences"""
        # Simulate returning user with saved configuration
        self.gui.config["overlay"] = {
            "position": "custom",
            "custom_x": "300",
            "custom_y": "400",
            "is_locked": "True"
        }
        
        # Load saved configuration
        self.gui.load_overlay_config()
        
        # Verify settings were restored
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertEqual(self.gui.overlay.custom_x, 300)
        self.assertEqual(self.gui.overlay.custom_y, 400)
        self.assertTrue(self.gui.overlay.is_locked)
        
        # User shows overlay
        self.gui.overlay.create_overlay()
        
        # Overlay should appear at saved position
        # Mock screen dimensions and geometry
        self.gui.overlay.overlay_window.winfo_screenwidth = Mock(return_value=1920)
        self.gui.overlay.overlay_window.winfo_screenheight = Mock(return_value=1080)
        self.gui.overlay.overlay_window.winfo_reqwidth = Mock(return_value=200)
        self.gui.overlay.overlay_window.winfo_reqheight = Mock(return_value=100)
        self.gui.overlay.overlay_window.update_idletasks = Mock()
        self.gui.overlay.overlay_window.geometry = Mock()
        
        self.gui.overlay._position_overlay()
        
        # Verify custom position was used
        self.gui.overlay.overlay_window.geometry.assert_called_with("200x100+300+400")
        
        # User unlocks to reposition
        self.gui.overlay.toggle_lock()
        self.assertFalse(self.gui.overlay.is_locked)
        
        # User drags to new position
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        self.gui.overlay._stop_drag(mock_event)
        
        # User locks again
        self.gui.overlay.toggle_lock()
        
        # Verify new position was saved
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertTrue(self.gui.overlay.is_locked)
    
    def test_power_user_workflow(self):
        """Test workflow for a power user who frequently changes settings"""
        self.gui.overlay.create_overlay()
        
        # Power user rapidly changes positions
        positions = ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        for position in positions:
            self.gui.update_overlay_position(position)
            self.assertEqual(self.gui.overlay.position, position)
        
        # Power user drags to custom position
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        self.gui.overlay._start_drag(mock_event)
        
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        self.gui.overlay._stop_drag(mock_event)
        
        # Power user rapidly toggles lock
        for i in range(5):
            self.gui.overlay.toggle_lock()
            expected_locked = i % 2 == 1
            self.assertEqual(self.gui.overlay.is_locked, expected_locked)
        
        # Power user changes transparency while dragging
        self.gui.overlay.is_locked = False
        self.gui.overlay.transparency = 0.5
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        mock_event.x_root = 200
        mock_event.y_root = 300
        self.gui.overlay._drag_data = {"x": 150, "y": 250}
        
        self.gui.overlay._on_drag(mock_event)
        
        # Should handle all operations smoothly
        self.assertEqual(self.gui.overlay.position, "custom")
        self.assertEqual(self.gui.overlay.transparency, 0.5)


if __name__ == '__main__':
    unittest.main()
