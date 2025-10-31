# Build script to create a single-file executable using PyInstaller
param(
    [string]$entry = "launcher.py",
    [string]$name = "SCKillFeed",
    [string]$Icon = "",
    [switch]$onefile,
    [string]$SpecFile = "",
    [string]$OutDir = "release",
    [string]$Version = "",
    [switch]$Clean = $false
)

Write-Host "Creating virtual environment for build"
python -m venv .venv; .\.venv\Scripts\Activate; python -m pip install --upgrade pip
Write-Host "Installing build requirements"
python -m pip install -r requirements-build.txt

if ($SpecFile -ne "") {
    # Use specified spec file
    $piArgs = @($SpecFile)
} else {
    # If a default spec file exists, use it
    $defaultSpec = Join-Path (Get-Location) "build_sc_kill_feed.spec"
    if (Test-Path $defaultSpec) {
        Write-Host "Default spec file found: $($defaultSpec) - using it."
        $piArgs = @($defaultSpec)
    } else {
        $piArgs = @("--name", $name)
        # Default to onefile=true if not explicitly set to false
        if ($onefile -or (-not $PSBoundParameters.ContainsKey('onefile'))) { 
            $piArgs += "--onefile" 
        }
        $piArgs += "--windowed"
        # Add icon if provided
        if ($Icon -ne "") {
            $piArgs += "--icon"
            $piArgs += $Icon
        }
        $piArgs += $entry
    }
}

# Clean build/dist directories if requested
if ($Clean) {
    Write-Host "Cleaning previous build artifacts..."
    $distDir = Join-Path (Get-Location) 'dist'
    $buildDir = Join-Path (Get-Location) 'build'

    function Remove-IfExists([string]$path) {
        if (Test-Path $path) {
            Write-Host " - Found: $path"
            try {
                Remove-Item -Recurse -Force -Path $path -ErrorAction Stop
                Write-Host "   Removed: $path"
            } catch {
                Write-Host "   Failed to remove: $path ($($_.Exception.Message))"
            }
        } else {
            Write-Host " - Not found: $path"
        }
    }

    Remove-IfExists $distDir
    Remove-IfExists $buildDir
}

Write-Host "Running PyInstaller..."
pyinstaller @($piArgs)

Write-Host "Build finished. The executable is at dist\$name"

# If OutDir specified, copy built exe into versioned release folder
if ($OutDir -ne "") {
    # Read version from version.txt if present (overrides -Version only if -Version not provided)
    $versionFile = Join-Path (Get-Location) 'version.txt'
    if ((Test-Path $versionFile) -and ($Version -eq "")) {
        $fileVersion = Get-Content $versionFile -Raw | ForEach-Object { $_.Trim() }
        if ($fileVersion -ne "") { $Version = $fileVersion }
    }

    # Use timestamp as fallback if no version is available
    if ($Version -eq "") {
        $timestamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmm')
        $Version = $timestamp
        Write-Host "Warning: No version specified and version.txt not found. Using timestamp as version: $Version"
    }

    $sourceExe = Join-Path (Join-Path (Get-Location) 'dist') ($name + '.exe')
    if (Test-Path $sourceExe) {
        $releaseDir = Join-Path (Get-Location) $OutDir
        if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir | Out-Null }

        # Copy versioned artifact
        $verName = "{0}-{1}.exe" -f $name, $Version
        $verPath = Join-Path $releaseDir $verName
        Copy-Item -Path $sourceExe -Destination $verPath -Force
        Write-Host "Copied versioned build artifact to $($verPath)"
    } else {
        Write-Host "Warning: expected built executable not found at $($sourceExe)"
    }
}
