# SC Kill Feed

**SC Kill Feed** is a live tracking tool for *Star Citizen* that monitors your in-game kills and deaths in real time - all wrapped in a clean, modern graphical interface.

---

## 🚀 What It Does

This tool reads your `Game.log` file from Star Citizen and instantly shows your combat activity in a real-time feed. Whether you’re dogfighting in space or battling on the ground, every kill, death, and streak is tracked, displayed, and saved for later.

---

## ✨ Key Features

### 🖥️ Modern GUI Interface
- Clean, dark-themed interface built with Tkinter.  
- Organized tabs for **Kill Feed**, **Statistics**, **Settings**, and **Export**.  
- Fully resizable with simple “A- / A+ / Reset” scaling controls.  

### ⚔️ Real-Time Kill Feed
- Instantly detects kill events in your `Game.log`.  
- Highlights player kills, deaths, and suicides with color-coded text.  
- Displays timestamp, weapon used, and who killed who - live.  

### 📊 Combat Statistics
- Tracks total kills, deaths, and kill/death (K/D) ratio.  
- Shows current and best streaks.  
- Lists your most-used weapons and recent activity.  

### ⚙️ Customizable Settings
- Save your in-game name and log file path directly in the app.  
- Auto-detects the most common Star Citizen log locations.  
- Saves your settings automatically for next time.  

### 💾 Easy Data Export
- Export your session data to **CSV** or **JSON**.  
- Includes all kills, deaths, and session statistics.  
- Perfect for sharing or analyzing your gameplay data.  

### 🧠 Smart Error Handling
- Detects missing or invalid log paths before starting.  
- Gracefully handles log rotations, permission issues, and encoding errors.  
- Keeps running smoothly even if the log temporarily disappears.  

### ⚡ Optimized for Performance
- Uses threaded log monitoring for smooth, non-blocking performance.  
- Auto-limits stored stats to prevent memory bloat.  
- Thread-safe communication ensures your GUI never freezes.  

---

## 🧩 Building a Windows Executable

You can build a standalone `.exe` version if you’d rather not run the script directly.

1. Install PyInstaller (or use the included `build.ps1` PowerShell script):  
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 (optional: -Clean)
   ```

2. Or build manually with PyInstaller:  
   ```powershell
   pyinstaller --onefile --name sc-kill-parser launcher.py
   ```

---

## ▶️ Running from Source

If you have Python installed, you can simply run the script:

```bash
python sc_kill_feed_gui.py
```

Then:
1. Open the **⚙️ Settings** tab.  
2. Enter your **in-game name** and select your `Game.log` file.  
3. Click **💾 Save Settings** — monitoring starts automatically.

---

## ⚙️ Configuration File

Your preferences are saved in `sc_kill_feed.ini` (in the same folder as the executable or script).  
This file stores:
- Your in-game name  
- Log file location  
- GUI scaling preferences  
- Performance tuning values  

You can edit this file manually if needed.

---

## 🔁 Continuous Integration (GitHub Actions)

The project includes CI workflows that automatically test and build the Windows version:
- **Tests** run on Ubuntu using `unittest discover -v`.
- **Builds** run on Windows, installing build dependencies and creating a one-file `.exe` via PyInstaller.
- The built executable is uploaded as an artifact for download.

---

## 📦 Downloading Builds

Once the GitHub Actions workflow completes, you can download the Windows executable (`.exe`) directly from the build artifacts section of the workflow run page.

---

Enjoy smoother, smarter kill tracking in the ‘Verse with **SC Kill Feed** - your personal combat companion for Star Citizen.
