#!/usr/bin/env python3
"""
Star Citizen Kill Feed Tracker - Launcher

Choose between command-line and GUI versions
"""

import sys
import os

def main():
    print("Star Citizen Kill Feed Tracker")
    print("=" * 40)
    print("1. GUI Version (Recommended)")
    print("2. Command Line Version")
    print("3. Exit")
    print("=" * 40)
    
    while True:
        choice = input("Select version (1-3): ").strip()
        
        if choice == '1':
            print("Starting GUI version...")
            try:
                from sc_kill_feed_gui import main as gui_main
                gui_main()
            except ImportError as e:
                print(f"Error starting GUI: {e}")
                print("Make sure all dependencies are installed.")
            break
            
        elif choice == '2':
            print("Starting command line version...")
            try:
                from sc_kill_feed import main as cli_main
                cli_main()
            except ImportError as e:
                print(f"Error starting CLI: {e}")
            break
            
        elif choice == '3':
            print("Goodbye!")
            sys.exit(0)
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    main()

