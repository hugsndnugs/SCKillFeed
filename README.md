# SC Kill Feed

Tool that tracks Star Citizen kills and displays the data in real time.

Building an .exe:

1. Install pyinstaller (or use the provided `build.ps1` on Windows):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 (optional: -Clean)
```

2. Build using PyInstaller (single-file exe):

```powershell
pyinstaller --onefile --name sc-kill-parser launcher.py
```

CI (GitHub Actions)
--------------------

- The `test` job runs on `ubuntu-latest` and executes the unit tests with `python -m unittest discover -v`.
- The `build-windows` job runs on `windows-latest`, installs the build requirements from `requirements-build.txt`, runs the `build.ps1` PowerShell script to produce a Windows single-file executable using PyInstaller, and uploads the resulting `release\*.exe` as a workflow artifact.

Downloading build artifacts
--------------------------

After a successful build the Windows executable will be available as an artifact on the workflow run page in GitHub Actions.
