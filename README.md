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

CI/CD (GitHub Actions)
--------------------

### Continuous Integration

- The `test` job runs on `ubuntu-latest` and executes the unit tests with `python -m unittest discover -v`.
- The `build-windows` job runs on `windows-latest`, installs the build requirements from `requirements-build.txt`, runs the `build.ps1` PowerShell script to produce a Windows single-file executable using PyInstaller, and uploads the resulting `release\*.exe` as a workflow artifact.

### Continuous Deployment / Releases

The CD pipeline automatically creates releases when you push a tag starting with `v` (e.g., `v2.0.4`) or manually trigger a release:

**Automatic Release (tag push):**
```bash
git tag v2.0.4
git push origin v2.0.4
```

**Manual Release:**
Go to Actions → CD - Release → Run workflow → Enter version tag (e.g., `v2.0.4`)

The workflow will:
1. Run tests on Linux
2. Build the Windows executable
3. Create a GitHub Release with the built artifact attached
4. Mark as pre-release if version contains `-alpha`, `-beta`, `-rc`, or `-`

Downloading releases
--------------------------

Pre-built Windows executables are available in the [Releases](https://github.com/Ponder001/SCKillFeed/releases) section. Each release includes a download link for the `SCKillFeed-<version>.exe` file.
