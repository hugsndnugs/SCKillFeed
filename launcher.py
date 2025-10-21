#!/usr/bin/env python3
"""
Star Citizen Kill Feed Tracker - Launcher

Note: keeping this entrypoint for now in case we want to add functionality to it later
"""

import sys
import os

def main():
    try:
        from sc_kill_feed_gui import main as gui_main
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)
    gui_main()

if __name__ == '__main__':
    main()

