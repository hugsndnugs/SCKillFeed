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
from collections import defaultdict, Counter
import json

class StarCitizenKillFeedGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Star Citizen Kill Feed Tracker")
        self.root.geometry("1200x800")
        self.root.configure(bg='#1e1e1e')
        
        # Configuration
        self.config = configparser.ConfigParser()
        self.config_path = self.get_config_path()
        self.load_config()
        
        # Data storage
        self.kills_data = []
        self.player_name = self.config.get('user', 'ingame_name', fallback='')
        self.log_file_path = self.config.get('user', 'log_path', fallback='')
        self.is_monitoring = False
        self.monitor_thread = None
        
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
        """Setup modern dark theme styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors for dark theme
        style.configure('TNotebook', background='#2d2d2d', borderwidth=0)
        style.configure('TNotebook.Tab', background='#3d3d3d', foreground='white', padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', '#4d4d4d')])
        
        style.configure('TFrame', background='#2d2d2d')
        style.configure('TLabel', background='#2d2d2d', foreground='white')
        style.configure('TButton', background='#4d4d4d', foreground='white')
        style.map('TButton', background=[('active', '#5d5d5d')])
        
        style.configure('Treeview', background='#3d3d3d', foreground='white', fieldbackground='#3d3d3d')
        style.map('Treeview', background=[('selected', '#4d4d4d')])
        
        style.configure('TEntry', background='#3d3d3d', foreground='white', fieldbackground='#3d3d3d')
        style.configure('TCombobox', background='#3d3d3d', foreground='white', fieldbackground='#3d3d3d')
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Star Citizen Kill Feed Tracker", 
                              font=('Arial', 20, 'bold'), bg='#1e1e1e', fg='#00ff88')
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_kill_feed_tab()
        self.create_statistics_tab()
        self.create_settings_tab()
        self.create_export_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - Configure settings to start monitoring")
        status_bar = tk.Label(main_frame, textvariable=self.status_var, 
                             bg='#1e1e1e', fg='white', anchor='w')
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def create_kill_feed_tab(self):
        """Create the real-time kill feed tab"""
        kill_feed_frame = ttk.Frame(self.notebook)
        self.notebook.add(kill_feed_frame, text="Kill Feed")
        
        # Control panel
        control_frame = ttk.Frame(kill_feed_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Monitoring", 
                                      command=self.toggle_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(control_frame, text="Clear Feed", 
                                      command=self.clear_kill_feed)
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Player name display
        self.player_label = tk.Label(control_frame, text=f"Player: {self.player_name}", 
                                   bg='#2d2d2d', fg='#00ff88', font=('Arial', 10, 'bold'))
        self.player_label.pack(side=tk.RIGHT)
        
        # Kill feed display
        feed_frame = ttk.Frame(kill_feed_frame)
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.kill_feed_text = scrolledtext.ScrolledText(feed_frame, 
                                                       bg='#1e1e1e', fg='white',
                                                       font=('Consolas', 10),
                                                       wrap=tk.WORD)
        self.kill_feed_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for coloring
        self.kill_feed_text.tag_configure("player_kill", foreground="#00ff88")
        self.kill_feed_text.tag_configure("player_death", foreground="#ff4444")
        self.kill_feed_text.tag_configure("other_kill", foreground="#ffffff")
        self.kill_feed_text.tag_configure("weapon", foreground="#4488ff")
        self.kill_feed_text.tag_configure("timestamp", foreground="#888888")
    
    def create_statistics_tab(self):
        """Create the statistics dashboard tab"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistics")
        
        # Main stats grid
        main_stats_frame = ttk.Frame(stats_frame)
        main_stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # K/D Ratio and Streaks
        kd_frame = ttk.LabelFrame(main_stats_frame, text="Kill/Death Statistics")
        kd_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.kills_label = tk.Label(kd_frame, text="Kills: 0", bg='#2d2d2d', fg='#00ff88', 
                                   font=('Arial', 14, 'bold'))
        self.kills_label.pack(pady=5)
        
        self.deaths_label = tk.Label(kd_frame, text="Deaths: 0", bg='#2d2d2d', fg='#ff4444', 
                                    font=('Arial', 14, 'bold'))
        self.deaths_label.pack(pady=5)
        
        self.kd_ratio_label = tk.Label(kd_frame, text="K/D Ratio: 0.00", bg='#2d2d2d', fg='white', 
                                      font=('Arial', 12))
        self.kd_ratio_label.pack(pady=5)
        
        self.streak_label = tk.Label(kd_frame, text="Current Streak: 0", bg='#2d2d2d', fg='#ffaa00', 
                                    font=('Arial', 12))
        self.streak_label.pack(pady=5)
        
        # Weapons stats
        weapons_frame = ttk.LabelFrame(main_stats_frame, text="Weapon Statistics")
        weapons_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.weapons_tree = ttk.Treeview(weapons_frame, columns=('count',), show='tree headings', height=8)
        self.weapons_tree.heading('#0', text='Weapon')
        self.weapons_tree.heading('count', text='Kills')
        self.weapons_tree.column('#0', width=200)
        self.weapons_tree.column('count', width=80)
        self.weapons_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Recent activity
        recent_frame = ttk.LabelFrame(stats_frame, text="Recent Activity")
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.recent_tree = ttk.Treeview(recent_frame, columns=('time', 'event'), show='headings', height=10)
        self.recent_tree.heading('time', text='Time')
        self.recent_tree.heading('event', text='Event')
        self.recent_tree.column('time', width=100)
        self.recent_tree.column('event', width=400)
        self.recent_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_settings_tab(self):
        """Create the settings configuration tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Player name setting
        name_frame = ttk.LabelFrame(settings_frame, text="Player Configuration")
        name_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(name_frame, text="Your In-Game Name:", bg='#2d2d2d', fg='white').pack(anchor='w', padx=5, pady=5)
        self.player_name_var = tk.StringVar(value=self.player_name)
        player_entry = ttk.Entry(name_frame, textvariable=self.player_name_var, width=50)
        player_entry.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Log file setting
        log_frame = ttk.LabelFrame(settings_frame, text="Log File Configuration")
        log_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(log_frame, text="Star Citizen Game.log Path:", bg='#2d2d2d', fg='white').pack(anchor='w', padx=5, pady=5)
        
        log_path_frame = ttk.Frame(log_frame)
        log_path_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        self.log_path_var = tk.StringVar(value=self.log_file_path)
        log_entry = ttk.Entry(log_path_frame, textvariable=self.log_path_var)
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_button = ttk.Button(log_path_frame, text="Browse", command=self.browse_log_file)
        browse_button.pack(side=tk.RIGHT)
        
        # Auto-detect button
        auto_detect_button = ttk.Button(log_frame, text="Auto-detect Game.log", 
                                       command=self.auto_detect_log)
        auto_detect_button.pack(pady=5)
        
        # Save settings button
        save_button = ttk.Button(settings_frame, text="Save Settings", 
                                command=self.save_settings)
        save_button.pack(pady=20)
    
    def create_export_tab(self):
        """Create the data export tab"""
        export_frame = ttk.Frame(self.notebook)
        self.notebook.add(export_frame, text="Export Data")
        
        # Export options
        options_frame = ttk.LabelFrame(export_frame, text="Export Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.export_csv_var = tk.BooleanVar(value=True)
        csv_check = ttk.Checkbutton(options_frame, text="Export as CSV", 
                                   variable=self.export_csv_var)
        csv_check.pack(anchor='w', padx=5, pady=5)
        
        self.export_json_var = tk.BooleanVar(value=False)
        json_check = ttk.Checkbutton(options_frame, text="Export as JSON", 
                                    variable=self.export_json_var)
        json_check.pack(anchor='w', padx=5, pady=5)
        
        # Export button
        export_button = ttk.Button(export_frame, text="Export Data", 
                                  command=self.export_data)
        export_button.pack(pady=20)
        
        # Export status
        self.export_status = tk.Label(export_frame, text="", bg='#2d2d2d', fg='white')
        self.export_status.pack(pady=10)
    
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
        
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            messagebox.showerror("Error", "Please select a valid Game.log file.")
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
        
        if not os.path.exists(self.log_file_path):
            messagebox.showerror("Error", "Game.log file not found. Please check the path.")
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
        """Monitor the log file for kill events"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, os.SEEK_END)
                while self.is_monitoring:
                    line = f.readline()
                    if not line:
                        time.sleep(0.2)
                        continue
                    
                    if '<Actor Death>' in line:
                        self.process_kill_event(line.strip())
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error monitoring file: {str(e)}"))
    
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
        self.kills_data.append(kill_data)
        
        # Update statistics
        self.update_statistics(kill_data)
        
        # Update UI in main thread
        self.root.after(0, lambda: self.display_kill_event(kill_data))
    
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
        
        # Update statistics display
        self.update_statistics_display()
    
    def update_statistics_display(self):
        """Update the statistics display"""
        # Update main stats
        self.kills_label.config(text=f"Kills: {self.stats['total_kills']}")
        self.deaths_label.config(text=f"Deaths: {self.stats['total_deaths']}")
        
        # Calculate K/D ratio
        if self.stats['total_deaths'] > 0:
            kd_ratio = self.stats['total_kills'] / self.stats['total_deaths']
        else:
            kd_ratio = self.stats['total_kills'] if self.stats['total_kills'] > 0 else 0
        
        self.kd_ratio_label.config(text=f"K/D Ratio: {kd_ratio:.2f}")
        
        # Current streak
        current_streak = self.stats['kill_streak'] if self.stats['kill_streak'] > 0 else -self.stats['death_streak']
        self.streak_label.config(text=f"Current Streak: {current_streak}")
        
        # Update weapons tree
        self.weapons_tree.delete(*self.weapons_tree.get_children())
        for weapon, count in self.stats['weapons_used'].most_common(10):
            self.weapons_tree.insert('', 'end', text=weapon, values=(count,))
        
        # Update recent activity
        self.recent_tree.delete(*self.recent_tree.get_children())
        for kill in self.kills_data[-10:]:  # Show last 10 events
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
    
    def clear_kill_feed(self):
        """Clear the kill feed display"""
        self.kill_feed_text.delete(1.0, tk.END)
        self.kills_data.clear()
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

