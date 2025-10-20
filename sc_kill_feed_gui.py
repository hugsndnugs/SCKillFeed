#!/usr/bin/env python3
"""
Star Citizen Kill Feed Tracker - GUI Version

A modern GUI application for tracking Star Citizen kill events
with real-time display, statistics, and data export capabilities.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import sys
import time
import threading
import csv
from datetime import datetime
import configparser
from typing import Optional, Tuple, Dict, List
from collections import defaultdict, Counter, deque
import json

# Custom exception classes for better error handling
class KillFeedError(Exception):
    """Base exception for kill feed errors"""
    pass

class LogFileError(KillFeedError):
    """Log file related errors"""
    pass

class ConfigurationError(KillFeedError):
    """Configuration related errors"""
    pass

class StarCitizenKillFeedGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Star Citizen Kill Feed Tracker")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0a')
        
        # Configuration
        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_path()
        self.load_config()
        
        # Data storage - Use deque with maxlen to prevent memory leaks
        self.kills_data = deque(maxlen=10000)  # Keep only last 10,000 events
        self.data_lock = threading.RLock()  # Thread-safe access to shared data
        self.player_name = self.config.get('user', 'ingame_name', fallback='')
        self.log_file_path = self.config.get('user', 'log_path', fallback='')
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Performance settings
        self.FILE_CHECK_INTERVAL = 0.1  # Reduced from 0.2 seconds
        self.MAX_LINES_PER_CHECK = 50   # Process up to 50 lines at once
        
        # UI update debouncing
        self._update_timer = None
        self._pending_updates = 0
        
        # Statistics
        self.stats = {
            'total_kills': 0,
            'total_deaths': 0,
            'kill_streak': 0,
            'death_streak': 0,
            'max_kill_streak': 0,
            'max_death_streak': 0,
            'weapons_used': Counter(),
            'weapons_against': Counter(),
            'victims': Counter(),
            'killers': Counter()
        }
        
        # Regex for parsing kill events
        self.KILL_LINE_RE = re.compile(
            r"<Actor Death>\s+CActor::Kill:\s*'(?P<victim>[^']+)'\s*\[[^\]]+\]\s*in zone '[^']+'\s*killed by\s*'(?P<killer>[^']+)'\s*\[[^\]]+\]\s*using\s*'(?P<weapon>[^']+)'",
            re.IGNORECASE,
        )
        
        self.setup_ui()
        self.setup_styles()
        
    def get_config_path(self):
        """Get the configuration file path"""
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(exe_dir, 'sc-kill-feed.cfg')
    
    def validate_file_path(self, file_path: str) -> bool:
        """Validate file path to prevent directory traversal attacks"""
        if not file_path or not isinstance(file_path, str):
            return False
        
        try:
            # Normalize the path to prevent directory traversal
            normalized_path = os.path.normpath(file_path)
            resolved_path = os.path.abspath(normalized_path)
            
            # Check if file exists and is a .log file
            if not os.path.exists(resolved_path):
                return False
            
            if not resolved_path.lower().endswith('.log'):
                return False
            
            # Check if path contains suspicious patterns
            suspicious_patterns = ['..', '~', '$', '`']
            for pattern in suspicious_patterns:
                if pattern in file_path:
                    return False
            
            return True
        except (OSError, ValueError):
            return False
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        if 'user' not in self.config:
            self.config['user'] = {}
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            self.config.write(f)
    
    def setup_styles(self):
        """Setup modern dark theme styling with contemporary design"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern color palette
        colors = {
            'bg_primary': '#0a0a0a',      # Deep black
            'bg_secondary': '#0a0a0a',   # Dark gray
            'bg_tertiary': '#0a0a0a',    # Medium gray
            'accent_primary': '#00d4ff',  # Cyan blue
            'accent_secondary': '#ff6b35', # Orange
            'accent_success': '#00ff88',  # Green
            'accent_danger': '#ff4757',   # Red
            'accent_warning': '#ffa502',  # Yellow
            'text_primary': '#ffffff',    # White
            'text_secondary': '#b0b0b0',  # Light gray
            'text_muted': '#808080'       # Medium gray
        }
        
        # Configure notebook styling
        style.configure('TNotebook', background=colors['bg_secondary'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=colors['bg_tertiary'], 
                       foreground=colors['text_primary'], 
                       padding=[25, 15],
                       font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', 
                 background=[('selected', colors['accent_primary']),
                           ('active', colors['bg_tertiary'])])
        
        # Configure frames
        style.configure('TFrame', background=colors['bg_secondary'])
        style.configure('Card.TFrame', background=colors['bg_tertiary'], relief='flat')
        
        # Configure labels
        style.configure('TLabel', background=colors['bg_secondary'], foreground=colors['text_primary'])
        style.configure('Title.TLabel', 
                       background=colors['bg_secondary'], 
                       foreground=colors['accent_primary'],
                       font=('Segoe UI', 24, 'bold'))
        style.configure('Subtitle.TLabel', 
                       background=colors['bg_secondary'], 
                       foreground=colors['text_secondary'],
                       font=('Segoe UI', 12))
        
        # Configure buttons with modern styling
        style.configure('TButton', 
                       background=colors['accent_primary'], 
                       foreground=colors['bg_primary'],
                       font=('Segoe UI', 10, 'bold'),
                       padding=[20, 10],
                       relief='flat')
        style.map('TButton', 
                 background=[('active', colors['accent_secondary']),
                           ('pressed', colors['accent_secondary'])])
        
        # Configure success/danger buttons
        style.configure('Success.TButton', 
                       background=colors['accent_success'], 
                       foreground=colors['bg_primary'])
        style.map('Success.TButton', 
                 background=[('active', '#00cc6a')])
        
        style.configure('Danger.TButton', 
                       background=colors['accent_danger'], 
                       foreground=colors['text_primary'])
        style.map('Danger.TButton', 
                 background=[('active', '#ff3742')])
        
        # Configure treeview with modern styling
        style.configure('Treeview', 
                       background=colors['bg_tertiary'], 
                       foreground=colors['text_primary'], 
                       fieldbackground=colors['bg_tertiary'],
                       font=('Segoe UI', 9))
        style.map('Treeview', background=[('selected', colors['accent_primary'])])
        
        # Configure entry fields
        style.configure('TEntry', 
                       background=colors['bg_tertiary'], 
                       foreground=colors['text_primary'], 
                       fieldbackground=colors['bg_tertiary'],
                       font=('Segoe UI', 10),
                       padding=[10, 8])
        style.configure('TCombobox', 
                       background=colors['bg_tertiary'], 
                       foreground=colors['text_primary'], 
                       fieldbackground=colors['bg_tertiary'])
        
        # Configure label frames
        style.configure('TLabelframe', 
                       background=colors['bg_secondary'], 
                       foreground=colors['text_primary'],
                       font=('Segoe UI', 11, 'bold'))
        style.configure('TLabelframe.Label', 
                       background=colors['bg_secondary'], 
                       foreground=colors['accent_primary'],
                       font=('Segoe UI', 11, 'bold'))
    
    def setup_ui(self):
        """Setup the main user interface with modern design"""
        # Main container with padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section with modern styling
        header_frame = ttk.Frame(main_frame, style='Card.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Title with modern typography
        title_label = ttk.Label(header_frame, text="Star Citizen Kill Feed Tracker", 
                              style='Title.TLabel')
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Wondering how many kills you get? Let us Ponder it for you!", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_kill_feed_tab()
        self.create_statistics_tab()
        self.create_settings_tab()
        self.create_export_tab()
        
        # Modern status bar
        status_frame = ttk.Frame(main_frame, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Configure settings to start monitoring")
        status_bar = tk.Label(status_frame, textvariable=self.status_var, 
                             bg='#0a0a0a', fg='#b0b0b0', anchor='w',
                             font=('Segoe UI', 9), padx=15, pady=8)
        status_bar.pack(fill=tk.X)
    
    def create_kill_feed_tab(self):
        """Create the real-time kill feed tab with modern design"""
        kill_feed_frame = ttk.Frame(self.notebook)
        self.notebook.add(kill_feed_frame, text="🎯 Kill Feed")
        
        # Control panel with modern card design
        control_frame = ttk.Frame(kill_feed_frame, style='Card.TFrame')
        control_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # Button container with better spacing
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, padx=15, pady=15)
        
        self.start_button = ttk.Button(button_frame, text="▶ Start Monitoring", 
                                      command=self.toggle_monitoring, style='Success.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.clear_button = ttk.Button(button_frame, text="🗑 Clear Feed", 
                                      command=self.clear_kill_feed, style='Danger.TButton')
        self.clear_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Player info with modern styling
        player_frame = ttk.Frame(control_frame)
        player_frame.pack(side=tk.RIGHT, padx=15, pady=15)
        
        self.player_label = tk.Label(player_frame, text=f"👤 Player: {self.player_name}", 
                                   bg='#0a0a0a', fg='#00d4ff', 
                                   font=('Segoe UI', 11, 'bold'), padx=10, pady=5)
        self.player_label.pack()
        
        # Kill feed display with modern styling
        feed_frame = ttk.Frame(kill_feed_frame, style='Card.TFrame')
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Feed header
        feed_header = tk.Label(feed_frame, text="📊 Live Combat Feed", 
                             bg='#2a2a2a', fg='#00d4ff', 
                             font=('Segoe UI', 12, 'bold'), pady=10)
        feed_header.pack(fill=tk.X)
        
        self.kill_feed_text = scrolledtext.ScrolledText(feed_frame, 
                                                       bg='#1a1a1a', fg='#ffffff',
                                                       font=('Consolas', 11),
                                                       wrap=tk.WORD,
                                                       padx=15, pady=10,
                                                       insertbackground='#00d4ff',
                                                       selectbackground='#00d4ff',
                                                       selectforeground='#1a1a1a')
        self.kill_feed_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Configure text tags for modern coloring
        self.kill_feed_text.tag_configure("player_kill", foreground="#00ff88", font=('Consolas', 11, 'bold'))
        self.kill_feed_text.tag_configure("player_death", foreground="#ff4757", font=('Consolas', 11, 'bold'))
        self.kill_feed_text.tag_configure("other_kill", foreground="#b0b0b0")
        self.kill_feed_text.tag_configure("weapon", foreground="#00d4ff", font=('Consolas', 11, 'italic'))
        self.kill_feed_text.tag_configure("timestamp", foreground="#808080", font=('Consolas', 10))
    
    def create_statistics_tab(self):
        """Create the statistics dashboard tab with modern design"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📈 Statistics")
        
        # Main stats grid with modern layout
        main_stats_frame = ttk.Frame(stats_frame)
        main_stats_frame.pack(fill=tk.X, padx=15, pady=15)
        
        # K/D Ratio and Streaks with modern card design
        kd_frame = ttk.LabelFrame(main_stats_frame, text="⚔️ Combat Statistics", style='TLabelframe')
        kd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Stats container with better spacing
        stats_container = ttk.Frame(kd_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        self.kills_label = tk.Label(stats_container, text="💀 Kills: 0", bg='#0a0a0a', fg='#00ff88', 
                                   font=('Segoe UI', 16, 'bold'), pady=8)
        self.kills_label.pack(fill=tk.X, pady=5)
        
        self.deaths_label = tk.Label(stats_container, text="💀 Deaths: 0", bg='#0a0a0a', fg='#ff4757', 
                                    font=('Segoe UI', 16, 'bold'), pady=8)
        self.deaths_label.pack(fill=tk.X, pady=5)
        
        self.kd_ratio_label = tk.Label(stats_container, text="📊 K/D Ratio: 0.00", bg='#0a0a0a', fg='#00d4ff', 
                                      font=('Segoe UI', 14, 'bold'), pady=8)
        self.kd_ratio_label.pack(fill=tk.X, pady=5)
        
        self.streak_label = tk.Label(stats_container, text="🔥 Current Streak: 0", bg='#0a0a0a', fg='#ffa502', 
                                    font=('Segoe UI', 14, 'bold'), pady=8)
        self.streak_label.pack(fill=tk.X, pady=5)
        
        # Weapons stats with modern design
        weapons_frame = ttk.LabelFrame(main_stats_frame, text="🔫 Weapon Statistics", style='TLabelframe')
        weapons_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.weapons_tree = ttk.Treeview(weapons_frame, columns=('count',), show='tree headings', height=8)
        self.weapons_tree.heading('#0', text='Weapon')
        self.weapons_tree.heading('count', text='Kills')
        self.weapons_tree.column('#0', width=200)
        self.weapons_tree.column('count', width=80)
        self.weapons_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Recent activity with modern design
        recent_frame = ttk.LabelFrame(stats_frame, text="📋 Recent Activity", style='TLabelframe')
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.recent_tree = ttk.Treeview(recent_frame, columns=('time', 'event'), show='headings', height=10)
        self.recent_tree.heading('time', text='Time')
        self.recent_tree.heading('event', text='Event')
        self.recent_tree.column('time', width=100)
        self.recent_tree.column('event', width=400)
        self.recent_tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
    
    def create_settings_tab(self):
        """Create the settings configuration tab with modern design"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Player name setting with modern design
        name_frame = ttk.LabelFrame(settings_frame, text="👤 Player Configuration", style='TLabelframe')
        name_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(name_frame, text="Your In-Game Name:", bg='#0a0a0a', fg='#ffffff', 
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=15, pady=(15, 5))
        self.player_name_var = tk.StringVar(value=self.player_name)
        player_entry = ttk.Entry(name_frame, textvariable=self.player_name_var, width=50)
        player_entry.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Log file setting with modern design
        log_frame = ttk.LabelFrame(settings_frame, text="📁 Log File Configuration", style='TLabelframe')
        log_frame.pack(fill=tk.X, padx=15, pady=15)
        
        tk.Label(log_frame, text="Star Citizen Game.log Path:", bg='#0a0a0a', fg='#ffffff', 
                font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=15, pady=(15, 5))
        
        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.log_path_var = tk.StringVar(value=self.log_file_path)
        log_entry = ttk.Entry(log_path_frame, textvariable=self.log_path_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_button = ttk.Button(log_path_frame, text="🔍 Browse", command=self.browse_log_file)
        browse_button.pack(side=tk.RIGHT)
        
        # Auto-detect button with modern styling
        auto_detect_button = ttk.Button(log_frame, text="🔍 Auto-detect Game.log", 
                                       command=self.auto_detect_log, style='TButton')
        auto_detect_button.pack(pady=15)
        
        # Save settings button with modern styling
        save_button = ttk.Button(settings_frame, text="💾 Save Settings", 
                                command=self.save_settings, style='Success.TButton')
        save_button.pack(pady=25)
    
    def create_export_tab(self):
        """Create the data export tab with modern design"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="📤 Export Data")
        
        # Export options with modern design
        options_frame = ttk.LabelFrame(export_frame, text="📋 Export Options", style='TLabelframe')
        options_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.export_csv_var = tk.BooleanVar(value=True)
        csv_check = ttk.Checkbutton(options_frame, text="📊 Export as CSV", 
                                   variable=self.export_csv_var)
        csv_check.pack(anchor='w', padx=15, pady=10)
        
        self.export_json_var = tk.BooleanVar(value=False)
        json_check = ttk.Checkbutton(options_frame, text="📄 Export as JSON", 
                                    variable=self.export_json_var)
        json_check.pack(anchor='w', padx=15, pady=10)
        
        # Export button with modern styling
        export_button = ttk.Button(export_frame, text="📤 Export Data", 
                                  command=self.export_data, style='Success.TButton')
        export_button.pack(pady=25)
        
        # Export status with modern styling
        self.export_status = tk.Label(export_frame, text="", bg='#0a0a0a', fg='#0a0a0a', 
                                    font=('Segoe UI', 10), pady=10)
        self.export_status.pack(pady=15)
    
    def browse_log_file(self):
        """Browse for Star Citizen log file"""
        file_path = filedialog.askopenfilename(
            title="Select Star Citizen Game.log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if file_path:
            self.log_path_var.set(file_path)
    
    def auto_detect_log(self):
        """Auto-detect Star Citizen log file"""
        common_paths = [
            os.path.expanduser("~/AppData/Local/Star Citizen/LIVE/Game.log"),
            os.path.expanduser("~/Documents/Star Citizen/LIVE/Game.log"),
            "C:/Program Files/Roberts Space Industries/StarCitizen/LIVE/Game.log"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.log_path_var.set(path)
                messagebox.showinfo("Auto-detect", f"Found Game.log at:\n{path}")
                return
        
        messagebox.showwarning("Auto-detect", "Could not auto-detect Game.log file.\nPlease browse manually.")
    
    def save_settings(self):
        """Save current settings"""
        self.player_name = self.player_name_var.get().strip()
        self.log_file_path = self.log_path_var.get().strip()
        
        if not self.player_name:
            messagebox.showerror("Error", "Please enter your in-game name.")
            return
        
        if not self.validate_file_path(self.log_file_path):
            messagebox.showerror("Error", "Please select a valid Game.log file. The file must exist and be a .log file.")
            return
        
        # Update config
        self.config['user']['ingame_name'] = self.player_name
        self.config['user']['log_path'] = self.log_file_path
        self.save_config()
        
        # Update UI
        self.player_label.config(text=f"Player: {self.player_name}")
        self.status_var.set("Settings saved successfully")
        
        messagebox.showinfo("Success", "Settings saved successfully!")
    
    def toggle_monitoring(self):
        """Toggle kill feed monitoring"""
        if not self.player_name or not self.log_file_path:
            messagebox.showerror("Error", "Please configure your settings first.")
            return
        
        if not self.validate_file_path(self.log_file_path):
            messagebox.showerror("Error", "Game.log file not found or invalid. Please check the path.")
            return
        
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start monitoring the log file"""
        self.is_monitoring = True
        self.start_button.config(text="Stop Monitoring")
        self.status_var.set("Monitoring started - Watching for kill events...")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_log_file, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring the log file"""
        self.is_monitoring = False
        self.start_button.config(text="Start Monitoring")
        self.status_var.set("Monitoring stopped")
    
    def monitor_log_file(self):
        """Monitor the log file for kill events with improved performance"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, os.SEEK_END)
                last_position = f.tell()
                
                while self.is_monitoring:
                    # Check if file has grown
                    current_position = f.tell()
                    if current_position < last_position:
                        # File was truncated, reset to end
                        f.seek(0, os.SEEK_END)
                        last_position = f.tell()
                    elif current_position > last_position:
                        # File has new content, read it
                        f.seek(last_position)
                        lines_read = 0
                        
                        # Process multiple lines at once for better performance
                        while lines_read < self.MAX_LINES_PER_CHECK and self.is_monitoring:
                            line = f.readline()
                            if not line:
                                break
                            
                            lines_read += 1
                            if '<Actor Death>' in line:
                                self.process_kill_event(line.strip())
                        
                        last_position = f.tell()
                    else:
                        # No new content, sleep briefly
                        time.sleep(self.FILE_CHECK_INTERVAL)
                        
        except FileNotFoundError as e:
            self.root.after(0, lambda: self.status_var.set(f"Log file not found: {str(e)}"))
        except PermissionError as e:
            self.root.after(0, lambda: self.status_var.set(f"Permission denied accessing log file: {str(e)}"))
        except UnicodeDecodeError as e:
            self.root.after(0, lambda: self.status_var.set(f"Error reading log file encoding: {str(e)}"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Unexpected error monitoring file: {str(e)}"))
    
    def process_kill_event(self, line: str):
        """Process a kill event line"""
        match = self.KILL_LINE_RE.search(line)
        if not match:
            return
        
        victim = match.group('victim')
        killer = match.group('killer')
        weapon = match.group('weapon')
        timestamp = datetime.now()
        
        # Store kill data
        kill_data = {
            'timestamp': timestamp,
            'victim': victim,
            'killer': killer,
            'weapon': weapon
        }
        
        # Thread-safe data access
        with self.data_lock:
            self.kills_data.append(kill_data)
            self.update_statistics(kill_data)
        
        # Update UI in main thread with debouncing
        self.root.after(0, lambda: self.display_kill_event(kill_data))
        self.debounced_update_statistics()
    
    def update_statistics(self, kill_data):
        """Update statistics based on kill data"""
        victim = kill_data['victim']
        killer = kill_data['killer']
        weapon = kill_data['weapon']
        
        # Update counters
        self.stats['weapons_used'][weapon] += 1
        self.stats['weapons_against'][weapon] += 1
        self.stats['victims'][victim] += 1
        self.stats['killers'][killer] += 1
        
        # Handle suicides first
        if killer == victim:
            if killer == self.player_name:
                # Player suicide counts as a death for the player
                self.stats['total_deaths'] += 1
                self.stats['death_streak'] += 1
                self.stats['kill_streak'] = 0
                self.stats['max_death_streak'] = max(self.stats['max_death_streak'], self.stats['death_streak'])
            # For non-player suicides, do not affect player's kill/death counts
            return
        
        # Check if player was involved (non-suicide)
        if killer == self.player_name:
            self.stats['total_kills'] += 1
            self.stats['kill_streak'] += 1
            self.stats['death_streak'] = 0
            self.stats['max_kill_streak'] = max(self.stats['max_kill_streak'], self.stats['kill_streak'])
        elif victim == self.player_name:
            self.stats['total_deaths'] += 1
            self.stats['death_streak'] += 1
            self.stats['kill_streak'] = 0
            self.stats['max_death_streak'] = max(self.stats['max_death_streak'], self.stats['death_streak'])
    
    def display_kill_event(self, kill_data):
        """Display kill event in the feed"""
        timestamp = kill_data['timestamp'].strftime('%H:%M:%S')
        victim = kill_data['victim']
        killer = kill_data['killer']
        weapon = kill_data['weapon']
        
        # Determine colors based on player involvement
        # Suicides
        if killer == victim:
            if killer == self.player_name:
                event_text = f"[{timestamp}] YOU died (suicide) using {weapon}\n"
                tags = ["player_death"]
            else:
                event_text = f"[{timestamp}] {killer} died (suicide) using {weapon}\n"
                tags = ["other_kill"]
        elif killer == self.player_name:
            event_text = f"[{timestamp}] YOU killed {victim} using {weapon}\n"
            tags = ["player_kill"]
        elif victim == self.player_name:
            event_text = f"[{timestamp}] {killer} killed YOU using {weapon}\n"
            tags = ["player_death"]
        else:
            event_text = f"[{timestamp}] {killer} killed {victim} using {weapon}\n"
            tags = ["other_kill"]
        
        # Insert into text widget
        self.kill_feed_text.insert(tk.END, event_text, tags)
        self.kill_feed_text.see(tk.END)
        
        # Update statistics display (removed immediate update - now debounced)
    
    def update_statistics_display(self):
        """Update the statistics display"""
        # Thread-safe data access
        with self.data_lock:
            # Create copies to avoid holding lock during UI updates
            stats_copy = self.stats.copy()
            recent_kills = list(self.kills_data)[-10:]  # Convert deque to list for slicing
        
        # Update main stats
        self.kills_label.config(text=f"Kills: {stats_copy['total_kills']}")
        self.deaths_label.config(text=f"Deaths: {stats_copy['total_deaths']}")
        
        # Calculate K/D ratio
        if stats_copy['total_deaths'] > 0:
            kd_ratio = stats_copy['total_kills'] / stats_copy['total_deaths']
        else:
            kd_ratio = stats_copy['total_kills'] if stats_copy['total_kills'] > 0 else 0
        
        self.kd_ratio_label.config(text=f"K/D Ratio: {kd_ratio:.2f}")
        
        # Current streak
        current_streak = stats_copy['kill_streak'] if stats_copy['kill_streak'] > 0 else -stats_copy['death_streak']
        self.streak_label.config(text=f"Current Streak: {current_streak}")
        
        # Update weapons tree
        self.weapons_tree.delete(*self.weapons_tree.get_children())
        for weapon, count in stats_copy['weapons_used'].most_common(10):
            self.weapons_tree.insert('', 'end', text=weapon, values=(count,))
        
        # Update recent activity
        self.recent_tree.delete(*self.recent_tree.get_children())
        for kill in recent_kills:  # Show last 10 events
            time_str = kill['timestamp'].strftime('%H:%M:%S')
            if kill['killer'] == kill['victim']:
                if kill['killer'] == self.player_name:
                    event = f"You died (suicide) ({kill['weapon']})"
                else:
                    event = f"{kill['killer']} died (suicide) ({kill['weapon']})"
            elif kill['killer'] == self.player_name:
                event = f"You killed {kill['victim']} ({kill['weapon']})"
            elif kill['victim'] == self.player_name:
                event = f"{kill['killer']} killed you ({kill['weapon']})"
            else:
                event = f"{kill['killer']} killed {kill['victim']} ({kill['weapon']})"
            
            self.recent_tree.insert('', 'end', values=(time_str, event))
    
    def debounced_update_statistics(self):
        """Debounced statistics update to prevent excessive UI updates"""
        self._pending_updates += 1
        
        # Cancel previous timer if it exists
        if self._update_timer:
            self.root.after_cancel(self._update_timer)
        
        # Schedule update after 100ms delay
        self._update_timer = self.root.after(100, self._perform_statistics_update)
    
    def _perform_statistics_update(self):
        """Actually perform the statistics update"""
        if self._pending_updates > 0:
            self.update_statistics_display()
            self._pending_updates = 0
        self._update_timer = None
    
    def clear_kill_feed(self):
        """Clear the kill feed display"""
        self.kill_feed_text.delete(1.0, tk.END)
        self.kills_data.clear()  # deque.clear() works the same as list.clear()
        self.stats = {
            'total_kills': 0,
            'total_deaths': 0,
            'kill_streak': 0,
            'death_streak': 0,
            'max_kill_streak': 0,
            'max_death_streak': 0,
            'weapons_used': Counter(),
            'weapons_against': Counter(),
            'victims': Counter(),
            'killers': Counter()
        }
        self.update_statistics_display()
        self.status_var.set("Kill feed cleared")
    
    def export_data(self):
        """Export kill data to file"""
        if not self.kills_data:
            messagebox.showwarning("Warning", "No data to export.")
            return
        
        # Get export format
        formats = []
        if self.export_csv_var.get():
            formats.append("CSV")
        if self.export_json_var.get():
            formats.append("JSON")
        
        if not formats:
            messagebox.showerror("Error", "Please select at least one export format.")
            return
        
        # Choose save location
        file_path = filedialog.asksaveasfilename(
            title="Export Kill Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            if "CSV" in formats and file_path.endswith('.csv'):
                self.export_csv(file_path)
            elif "JSON" in formats and file_path.endswith('.json'):
                self.export_json(file_path)
            else:
                # Export both formats
                base_path = os.path.splitext(file_path)[0]
                if "CSV" in formats:
                    self.export_csv(f"{base_path}.csv")
                if "JSON" in formats:
                    self.export_json(f"{base_path}.json")
            
            self.export_status.config(text=f"Data exported successfully to {file_path}")
            messagebox.showinfo("Success", "Data exported successfully!")
            
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Export directory not found: {str(e)}")
        except PermissionError as e:
            messagebox.showerror("Error", f"Permission denied writing export file: {str(e)}")
        except UnicodeEncodeError as e:
            messagebox.showerror("Error", f"Error encoding export data: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def export_csv(self, file_path):
        """Export data as CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'killer', 'victim', 'weapon'])
            for kill in self.kills_data:
                writer.writerow([
                    kill['timestamp'].isoformat(),
                    kill['killer'],
                    kill['victim'],
                    kill['weapon']
                ])
    
    def export_json(self, file_path):
        """Export data as JSON"""
        data = {
            'player_name': self.player_name,
            'export_time': datetime.now().isoformat(),
            'statistics': {
                'total_kills': self.stats['total_kills'],
                'total_deaths': self.stats['total_deaths'],
                'kill_death_ratio': self.stats['total_kills'] / max(self.stats['total_deaths'], 1),
                'max_kill_streak': self.stats['max_kill_streak'],
                'max_death_streak': self.stats['max_death_streak']
            },
            'kill_events': [
                {
                    'timestamp': kill['timestamp'].isoformat(),
                    'killer': kill['killer'],
                    'victim': kill['victim'],
                    'weapon': kill['weapon']
                }
                for kill in self.kills_data
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

def main():
    """Main entry point"""
    app = StarCitizenKillFeedGUI()
    app.run()

if __name__ == '__main__':
    main()

