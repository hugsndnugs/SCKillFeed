# Test script to verify MSIX packaging works locally
param(
    [switch]$SkipBuild = $false
)

Write-Host "Testing MSIX packaging setup..."

# Check prerequisites
Write-Host "Checking prerequisites..."

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion"
} catch {
    Write-Error "✗ Python not found"
    exit 1
}

# Check if PyInstaller is available
try {
    $pyinstallerVersion = pyinstaller --version 2>&1
    Write-Host "✓ PyInstaller found: $pyinstallerVersion"
} catch {
    Write-Error "✗ PyInstaller not found. Run: pip install -r requirements-build.txt"
    exit 1
}

# Check if Windows SDK is available
$makeAppxPath = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"
if (-not (Test-Path $makeAppxPath)) {
    $altPaths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\x64\makeappx.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\x64\makeappx.exe"
    )
    
    $found = $false
    foreach ($path in $altPaths) {
        if (Test-Path $path) {
            $makeAppxPath = $path
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Warning "✗ MakeAppx not found. You may need to install Windows SDK"
        Write-Host "  Try: winget install Microsoft.WindowsSDK.10.0.22621"
    } else {
        Write-Host "✓ MakeAppx found: $makeAppxPath"
    }
} else {
    Write-Host "✓ MakeAppx found: $makeAppxPath"
}

# Check if required files exist
$requiredFiles = @(
    "launcher.py",
    "sc_kill_feed_gui.py", 
    "AppxManifest.xml",
    "build-msix.ps1",
    "assets/sckt-icon.ico"
)

Write-Host "Checking required files..."
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file"
    } else {
        Write-Error "✗ $file not found"
        exit 1
    }
}

if (-not $SkipBuild) {
    Write-Host "`nRunning MSIX build test..."
    try {
        & .\build-msix.ps1 -Clean
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ MSIX build test completed successfully!"
            
            # Check if MSIX file was created
            $msixFiles = Get-ChildItem -Path "msix-release" -Filter "*.msix" -ErrorAction SilentlyContinue
            if ($msixFiles) {
                Write-Host "✓ MSIX package created: $($msixFiles[0].Name)"
                Write-Host "  Size: $([math]::Round($msixFiles[0].Length / 1MB, 2)) MB"
            } else {
                Write-Warning "✗ No MSIX file found in msix-release directory"
            }
        } else {
            Write-Error "✗ MSIX build test failed"
            exit 1
        }
    } catch {
        Write-Error "✗ MSIX build test failed: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "Skipping build test (use -SkipBuild to run prerequisites check only)"
}

Write-Host "`nMSIX packaging setup verification completed!"
