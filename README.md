# SC Kill Feed

Tool that tracks Star Citizen kill events and outputs them to a terminal

Usage:

1. Ensure you have Python 3.8+ installed.
2. Run the script:

```
python sc_kill_feed.py
```

Output:
- Killer (green if it's you, otherwise red)
- Victim (green if it's you, otherwise red)
- Weapon (blue)
 
Behavior:
- The script writes a `kill_log.csv` file alongside the running script/executable (current working directory). If writing there fails, it falls back to your home directory and prints the CSV path used.

Building an .exe:

1. Install pyinstaller (or use the provided `build.ps1` on Windows):

```
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 (optional: -Clean)
```

2. Build using PyInstaller (single-file exe):

```
pyinstaller --onefile --name sc-kill-parser sc_kill_feed.py 
```
