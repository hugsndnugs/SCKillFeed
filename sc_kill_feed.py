#!/usr/bin/env python3
"""
Star Citizen kill feed tracker

Parses the Game.log file to extract kill information

Prompts the user for their in-game name and a path to the game log.
Stores the configuraton alongside the script/executable

Colors:
 - kill and killed-by names: green if matches player's name, red otherwise

"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import Optional, Tuple
import csv
from datetime import datetime
import configparser

try:
	import tkinter as tk
	from tkinter import filedialog
except Exception:
	tk = None

# ANSI color codes
RESET = "\x1b[0m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
BLUE = "\x1b[34m"

def color_name(name: str, player_name: str) -> str:
	if name == player_name:
		return f"{GREEN}{name}{RESET}"
	return f"{RED}{name}{RESET}"

KILL_LINE_RE = re.compile(
	r"<Actor Death>\s+CActor::Kill:\s*'(?P<victim>[^']+)'\s*\[[^\]]+\]\s*in zone '[^']+'\s*killed by\s*'(?P<killer>[^']+)'\s*\[[^\]]+\]\s*using\s*'(?P<weapon>[^']+)'",
	re.IGNORECASE,
)

def parse_actor_death(line: str) -> Optional[Tuple[str, str, str]]:
	m = KILL_LINE_RE.search(line)
	if not m:
		return None
	return m.group('victim'), m.group('killer'), m.group('weapon')

def tail_file(path: str):
	with open(path, 'r', encoding='utf-8', errors='ignore') as f:
		f.seek(0, os.SEEK_END)
		while True:
			line = f.readline()
			if not line:
				time.sleep(0.2)
				continue
			yield line.rstrip('\n')

def pick_game_directory(initialdir: Optional[str] = None) -> Optional[str]:
	if tk is None:
		print("tkinter not available. Please enter the path to your Star Citizen LIVE game folder:")
		return input('Game folder path: ').strip()

	root = tk.Tk()
	root.withdraw()
	print('Select the Star Citizen LIVE game folder')
	dir_path = filedialog.askdirectory(title='Select game folder', initialdir=initialdir)
	root.destroy()
	return dir_path or None

def create_csv_writer(log_dir: str, csv_dir: Optional[str] = None):
	preferred_dir = csv_dir if csv_dir else log_dir
	csv_path = os.path.join(preferred_dir, 'kill_log.csv')
	csv_file = None
	csv_writer = None
	csv_enabled = False
	try:
		csv_file = open(csv_path, 'a', newline='', encoding='utf-8')
		csv_writer = csv.writer(csv_file)
		try:
			if os.path.getsize(csv_path) == 0:
				csv_writer.writerow(['timestamp', 'killer', 'victim', 'weapon'])
				csv_file.flush()
		except OSError:
			pass
		csv_enabled = True
		try:
			print(f"Logging CSV to: {csv_path}")
		except Exception:
			pass
		return csv_writer, csv_file, csv_path, csv_enabled
	except PermissionError:
		print(f"Warning: permission denied writing CSV to {csv_path}. Attempting fallback to home directory.")
	except OSError as e:
		print(f"Warning: could not open CSV at {csv_path}: {e}. Attempting fallback to home directory.")

	home_dir = os.path.expanduser('~')
	fallback_path = os.path.join(home_dir, 'kill_log.csv')
	try:
		csv_file = open(fallback_path, 'a', newline='', encoding='utf-8')
		csv_writer = csv.writer(csv_file)
		try:
			if os.path.getsize(fallback_path) == 0:
				csv_writer.writerow(['timestamp', 'killer', 'victim', 'weapon'])
				csv_file.flush()
		except OSError:
			pass
		csv_enabled = True
		print(f"Logging CSV to fallback location: {fallback_path}")
		return csv_writer, csv_file, fallback_path, csv_enabled
	except Exception as e:
		print(f"Warning: could not open fallback CSV at {fallback_path}: {e}. CSV logging disabled.")
		return None, None, None, False

def main():
	if getattr(sys, 'frozen', False):
		exe_dir = os.path.dirname(sys.executable)
	else:
		exe_dir = os.path.dirname(os.path.abspath(__file__))
	config_path = os.path.join(exe_dir, 'sc-kill-feed.cfg')

	config = configparser.ConfigParser()
	config.read(config_path)
	if 'user' not in config:
		config['user'] = {}

	parser = argparse.ArgumentParser(description='Parse the Star Citizen Game.log for kill events')
	parser.add_argument('--player', '-p', help="Your in-game name")
	parser.add_argument('--file', '-f', help="Path to the Star Citizen LIVE directory")
	args = parser.parse_args()

	player = args.player or config['user'].get('ingame_name')
	if not player:
		player = input('Enter your in-game name: ').strip()
		config['user']['ingame_name'] = player

	file_path = args.file or config['user'].get('log_path')
	if file_path and not os.path.isfile(file_path):
		print(f'File not found: {file_path}')
		file_path = None

	if not file_path:
		guess = os.path.expanduser('~')
		game_dir = pick_game_directory(initialdir=guess)
		if not game_dir:
			print('No folder selected, exiting.')
			sys.exit(1)
		candidate = os.path.join(game_dir, 'Game.log')
		if not os.path.isfile(candidate):
			print(f"Game.log not found in selected folder: {candidate}")
			print('Make sure you are selecting the Star Citizen LIVE game folder')
			sys.exit(1)
		file_path = candidate
		config['user']['log_path'] = file_path

	with open(config_path, 'w') as f:
		config.write(f)

	print(f"Watching file: {file_path}")

	log_dir = os.path.dirname(os.path.abspath(file_path))
	if getattr(sys, 'frozen', False):
		exe_dir = os.path.dirname(sys.executable)
		csv_dir = exe_dir
	else:
		csv_dir = os.getcwd()
	csv_writer, csv_file, csv_path, csv_enabled = create_csv_writer(log_dir, csv_dir=csv_dir)
	
	print("Exit terminal or press Ctrl+C to quit")
	
	# Do the parsing
	try:
		for line in tail_file(file_path):
			if '<Actor Death>' not in line:
				continue
			parsed = parse_actor_death(line)
			if not parsed:
				continue
			victim, killer, weapon = parsed
			ts = datetime.now().strftime('%H:%M:%S')
			victim_colored = color_name(victim, player)
			killer_colored = color_name(killer, player)
			weapon_colored = f"{BLUE}{weapon}{RESET}"
			
			# The formed terminal output line
			out_line = f"{ts}  {killer_colored} killed {victim_colored} using {weapon_colored}"
			print(out_line)

			if csv_enabled and csv_writer:
				try:
					csv_writer.writerow([datetime.now().isoformat(), killer, victim, weapon])
					csv_file.flush()
				except Exception:
					print("Warning: CSV write failed; disabling CSV logging.")
					try:
						csv_file.close()
					except Exception:
						pass
					csv_enabled = False
	except KeyboardInterrupt:
		print('\nExiting')
	finally:
		try:
			csv_file.close()
		except Exception:
			pass
	

if __name__ == '__main__':
	main()
