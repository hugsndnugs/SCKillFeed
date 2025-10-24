# MSIX Packaging Script for SCKillFeed
param(
    [string]$entry = "launcher.py",
    [string]$name = "SCKillFeed",
    [string]$Icon = "assets/sckt-icon.ico",
    [string]$OutDir = "msix-release",
    [string]$Version = "",
    [switch]$Clean = $false
)

Write-Host "Starting MSIX packaging process..."

# Read version from version.txt if present
$versionFile = Join-Path (Get-Location) 'version.txt'
if ((Test-Path $versionFile) -and ($Version -eq "")) {
    $fileVersion = Get-Content $versionFile -Raw | ForEach-Object { $_.Trim() }
    if ($fileVersion -ne "") { $Version = $fileVersion }
}

if ($Version -eq "") {
    $Version = "2.0.2"
}

Write-Host "Using version: $Version"

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous MSIX build artifacts..."
    $msixDir = Join-Path (Get-Location) $OutDir
    if (Test-Path $msixDir) {
        Remove-Item -Recurse -Force -Path $msixDir
    }
}

# Create output directory
$msixDir = Join-Path (Get-Location) $OutDir
if (-not (Test-Path $msixDir)) {
    New-Item -ItemType Directory -Path $msixDir | Out-Null
}

# Step 1: Build the executable using existing build script
Write-Host "Building executable..."
$buildArgs = @(
    "-entry", $entry,
    "-name", $name,
    "-onefile",
    "-OutDir", "temp-build",
    "-Clean"
)

if ($Icon -ne "") {
    $buildArgs += "-Icon"
    $buildArgs += $Icon
}

& .\build.ps1 @buildArgs

# Step 2: Create MSIX package structure
Write-Host "Creating MSIX package structure..."

# Create package directory
$packageDir = Join-Path $msixDir "SCKillFeed_$Version"
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force -Path $packageDir
}
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Copy executable
$exeSource = Join-Path (Get-Location) "temp-build" "$name.exe"
$exeDest = Join-Path $packageDir "$name.exe"
if (Test-Path $exeSource) {
    Copy-Item -Path $exeSource -Destination $exeDest -Force
    Write-Host "Copied executable to package directory"
} else {
    Write-Error "Executable not found at $exeSource"
    exit 1
}

# Create Assets directory and copy icon
$assetsDir = Join-Path $packageDir "Assets"
New-Item -ItemType Directory -Path $assetsDir | Out-Null

if (Test-Path $Icon) {
    # Convert ICO to PNG for MSIX (simplified - you might need proper conversion)
    $iconDest = Join-Path $assetsDir "Square44x44Logo.png"
    Copy-Item -Path $Icon -Destination $iconDest -Force
    Write-Host "Copied icon to Assets directory"
}

# Copy and update AppxManifest.xml
$manifestSource = Join-Path (Get-Location) "AppxManifest.xml"
$manifestDest = Join-Path $packageDir "AppxManifest.xml"
if (Test-Path $manifestSource) {
    Copy-Item -Path $manifestSource -Destination $manifestDest -Force
    
    # Update version in manifest
    $manifestContent = Get-Content $manifestDest -Raw
    $manifestContent = $manifestContent -replace 'Version="[^"]*"', "Version=`"$Version.0`""
    $manifestContent = $manifestContent -replace 'Name="[^"]*"', "Name=`"$name`""
    Set-Content -Path $manifestDest -Value $manifestContent -Encoding UTF8
    Write-Host "Updated AppxManifest.xml with version $Version"
} else {
    Write-Error "AppxManifest.xml not found"
    exit 1
}

# Step 3: Create MSIX package using MakeAppx
Write-Host "Creating MSIX package..."

# Check if MakeAppx is available
$makeAppxPath = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"
if (-not (Test-Path $makeAppxPath)) {
    # Try alternative paths
    $altPaths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\x64\makeappx.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\x64\makeappx.exe"
    )
    
    foreach ($path in $altPaths) {
        if (Test-Path $path) {
            $makeAppxPath = $path
            break
        }
    }
}

if (-not (Test-Path $makeAppxPath)) {
    Write-Warning "MakeAppx not found. Installing Windows SDK components..."
    
    # Try to install Windows SDK via winget
    try {
        winget install Microsoft.WindowsSDK.10.0.22621
        $makeAppxPath = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\makeappx.exe"
    } catch {
        Write-Error "Could not install Windows SDK. Please install manually."
        exit 1
    }
}

# Create MSIX package
$msixFile = Join-Path $msixDir "SCKillFeed_$Version.msix"
$makeAppxArgs = @(
    "pack",
    "/d", $packageDir,
    "/p", $msixFile,
    "/o"
)

Write-Host "Running: $makeAppxPath $($makeAppxArgs -join ' ')"
& $makeAppxPath @makeAppxArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "MSIX package created successfully: $msixFile"
} else {
    Write-Error "Failed to create MSIX package"
    exit 1
}

# Step 4: Clean up temporary files
Write-Host "Cleaning up temporary files..."
$tempBuildDir = Join-Path (Get-Location) "temp-build"
if (Test-Path $tempBuildDir) {
    Remove-Item -Recurse -Force -Path $tempBuildDir
}

Write-Host "MSIX packaging completed successfully!"
Write-Host "Package location: $msixFile"
