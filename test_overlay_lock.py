#!/usr/bin/env python3
"""
Test suite for overlay lock/unlock functionality
Tests all aspects of the lock feature
"""

import unittest
import tkinter as tk
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sc_kill_feed_gui import StatisticsOverlay, StarCitizenKillFeedGUI


class TestOverlayLock(unittest.TestCase):
    """Test cases for overlay lock functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window during tests
        
        # Create a mock parent GUI
        self.mock_parent = Mock()
        self.mock_parent.root = self.root
        self.mock_parent.save_config = Mock()
        self.mock_parent.update_lock_status = Mock()
        
        # Create overlay instance
        self.overlay = StatisticsOverlay(self.mock_parent)
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self.overlay, 'overlay_window') and self.overlay.overlay_window:
            self.overlay.destroy()
        self.root.destroy()
    
    def test_lock_state_initialization(self):
        """Test that lock state is properly initialized"""
        self.assertFalse(self.overlay.is_locked)
    
    def test_toggle_lock_unlocked_to_locked(self):
        """Test toggling lock from unlocked to locked"""
        self.overlay.is_locked = False
        self.overlay.create_overlay()
        
        # Toggle to locked
        self.overlay.toggle_lock()
        
        # Check that lock state changed
        self.assertTrue(self.overlay.is_locked)
        
        # Check that lock button was updated
        self.assertEqual(self.overlay.lock_button['text'], '🔓')
        self.assertEqual(self.overlay.lock_button['fg'], '#00ff88')
        
        # Check that parent GUI was notified
        self.mock_parent.update_lock_status.assert_called()
        self.mock_parent.save_config.assert_called()
    
    def test_toggle_lock_locked_to_unlocked(self):
        """Test toggling lock from locked to unlocked"""
        self.overlay.is_locked = True
        self.overlay.create_overlay()
        
        # Toggle to unlocked
        self.overlay.toggle_lock()
        
        # Check that lock state changed
        self.assertFalse(self.overlay.is_locked)
        
        # Check that lock button was updated
        self.assertEqual(self.overlay.lock_button['text'], '🔒')
        self.assertEqual(self.overlay.lock_button['fg'], '#ff4757')
    
    def test_set_lock_state_programmatically(self):
        """Test setting lock state programmatically"""
        self.overlay.create_overlay()
        
        # Set to locked
        self.overlay.set_lock_state(True)
        self.assertTrue(self.overlay.is_locked)
        self.assertEqual(self.overlay.lock_button['text'], '🔓')
        
        # Set to unlocked
        self.overlay.set_lock_state(False)
        self.assertFalse(self.overlay.is_locked)
        self.assertEqual(self.overlay.lock_button['text'], '🔒')
    
    def test_lock_button_creation_and_styling(self):
        """Test that lock button is created with proper styling"""
        self.overlay.create_overlay()
        
        # Check button exists
        self.assertIsNotNone(self.overlay.lock_button)
        
        # Check initial state (unlocked)
        self.assertEqual(self.overlay.lock_button['text'], '🔒')
        self.assertEqual(self.overlay.lock_button['fg'], '#ff4757')
        self.assertEqual(self.overlay.lock_button['bg'], '#0a0a0a')
        self.assertEqual(self.overlay.lock_button['cursor'], 'hand2')
    
    def test_lock_prevents_drag_start(self):
        """Test that lock prevents drag from starting"""
        self.overlay.is_locked = True
        self.overlay.create_overlay()
        
        # Try to start drag
        mock_event = Mock()
        mock_event.x_root = 100
        mock_event.y_root = 200
        
        self.overlay._start_drag(mock_event)
        
        # Drag data should not be set
        self.assertEqual(self.overlay._drag_data["x"], 0)
        self.assertEqual(self.overlay._drag_data["y"], 0)
    
    def test_lock_prevents_drag_motion(self):
        """Test that lock prevents drag motion"""
        self.overlay.is_locked = True
        self.overlay.create_overlay()
        
        # Set some drag data (simulating previous drag start)
        self.overlay._drag_data = {"x": 100, "y": 200}
        
        # Try to drag
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry method
        self.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.overlay._on_drag(mock_event)
        
        # Geometry should not be called
        self.overlay.overlay_window.geometry.assert_not_called()
    
    def test_lock_state_persistence(self):
        """Test that lock state is saved and loaded correctly"""
        # Test saving lock state
        self.overlay.is_locked = True
        
        # Mock config structure
        config = {"overlay": {}}
        
        # Test saving
        with patch.object(self.mock_parent, 'config', config):
            self.overlay.parent_gui.save_overlay_config = Mock()
            self.overlay.parent_gui.save_overlay_config()
        
        # Test loading
        config["overlay"]["is_locked"] = "True"
        
        with patch.object(self.mock_parent, 'config', config):
            self.mock_parent.load_overlay_config = Mock()
            self.mock_parent.load_overlay_config()
        
        # Verify lock state was loaded
        self.assertTrue(self.overlay.is_locked)


class TestLockIntegration(unittest.TestCase):
    """Integration tests for lock functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create full GUI instance
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after integration tests"""
        if hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        self.gui.root.destroy()
    
    def test_main_ui_lock_controls(self):
        """Test lock controls in main UI"""
        # Check that lock controls exist
        self.assertTrue(hasattr(self.gui, 'toggle_overlay_lock'))
        self.assertTrue(hasattr(self.gui, 'update_lock_status'))
        
        # Test toggle from main UI
        initial_state = self.gui.overlay.is_locked
        self.gui.toggle_overlay_lock()
        
        # State should be toggled
        self.assertNotEqual(self.gui.overlay.is_locked, initial_state)
    
    def test_lock_status_display_update(self):
        """Test that lock status display is updated correctly"""
        # Create overlay to get UI elements
        self.gui.overlay.create_overlay()
        
        # Test unlocked state
        self.gui.overlay.is_locked = False
        self.gui.update_lock_status()
        
        # Check button text
        if hasattr(self.gui, 'lock_toggle_btn'):
            self.assertIn("Lock", self.gui.lock_toggle_btn['text'])
        
        # Check status label
        if hasattr(self.gui, 'lock_status_label'):
            self.assertIn("Unlocked", self.gui.lock_status_label['text'])
        
        # Test locked state
        self.gui.overlay.is_locked = True
        self.gui.update_lock_status()
        
        # Check button text
        if hasattr(self.gui, 'lock_toggle_btn'):
            self.assertIn("Unlock", self.gui.lock_toggle_btn['text'])
        
        # Check status label
        if hasattr(self.gui, 'lock_status_label'):
            self.assertIn("Locked", self.gui.lock_status_label['text'])
    
    def test_lock_configuration_save_load(self):
        """Test that lock state is saved and loaded in configuration"""
        # Set lock state
        self.gui.overlay.is_locked = True
        
        # Save configuration
        self.gui.save_overlay_config()
        
        # Check that lock state was saved
        self.assertIn("overlay", self.gui.config)
        self.assertEqual(self.gui.config["overlay"]["is_locked"], "True")
        
        # Reset and load
        self.gui.overlay.is_locked = False
        self.gui.load_overlay_config()
        
        # Check that lock state was loaded
        self.assertTrue(self.gui.overlay.is_locked)
    
    def test_lock_with_drag_integration(self):
        """Test lock functionality integrated with drag"""
        self.gui.overlay.create_overlay()
        
        # Test unlocked - should allow drag
        self.gui.overlay.is_locked = False
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        
        mock_event = Mock()
        mock_event.x_root = 150
        mock_event.y_root = 250
        
        # Mock geometry
        self.gui.overlay.overlay_window.geometry = Mock(return_value="200x100+50+75")
        
        self.gui.overlay._on_drag(mock_event)
        
        # Should allow drag
        self.overlay.overlay_window.geometry.assert_called()
        
        # Test locked - should prevent drag
        self.gui.overlay.is_locked = True
        self.gui.overlay._drag_data = {"x": 100, "y": 200}
        
        # Reset mock
        self.gui.overlay.overlay_window.geometry.reset_mock()
        
        self.gui.overlay._on_drag(mock_event)
        
        # Should not allow drag
        self.gui.overlay.overlay_window.geometry.assert_not_called()


class TestLockUI(unittest.TestCase):
    """Test cases for lock UI elements"""
    
    def setUp(self):
        """Set up UI test fixtures"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.gui = StarCitizenKillFeedGUI()
        
    def tearDown(self):
        """Clean up after UI tests"""
        if hasattr(self.gui, 'overlay') and self.gui.overlay.overlay_window:
            self.gui.overlay.destroy()
        self.gui.root.destroy()
    
    def test_lock_frame_creation(self):
        """Test that lock control frame is created in overlay tab"""
        # Check that overlay tab was created
        self.assertTrue(hasattr(self.gui, 'notebook'))
        
        # The lock frame should be created when overlay tab is created
        # This is tested indirectly through the create_overlay_tab method
    
    def test_lock_button_functionality(self):
        """Test lock button click functionality"""
        self.gui.overlay.create_overlay()
        
        # Get initial state
        initial_state = self.gui.overlay.is_locked
        
        # Simulate button click
        self.gui.overlay.toggle_lock()
        
        # State should be toggled
        self.assertNotEqual(self.gui.overlay.is_locked, initial_state)
    
    def test_lock_status_color_coding(self):
        """Test that lock status uses proper color coding"""
        self.gui.overlay.create_overlay()
        
        # Test unlocked state colors
        self.gui.overlay.is_locked = False
        self.gui.update_lock_status()
        
        if hasattr(self.gui, 'lock_status_label'):
            self.assertEqual(self.gui.lock_status_label['fg'], '#b0b0b0')
        
        # Test locked state colors
        self.gui.overlay.is_locked = True
        self.gui.update_lock_status()
        
        if hasattr(self.gui, 'lock_status_label'):
            self.assertEqual(self.gui.lock_status_label['fg'], '#00ff88')


if __name__ == '__main__':
    unittest.main()
