# Script to create MSIX assets from existing icon
param(
    [string]$IconPath = "assets/sckt-icon.ico",
    [string]$OutputDir = "msix-assets"
)

Write-Host "Creating MSIX assets from icon: $IconPath"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Check if ImageMagick is available for icon conversion
$magickPath = Get-Command magick -ErrorAction SilentlyContinue
if ($magickPath) {
    Write-Host "Using ImageMagick for icon conversion..."
    
    # Convert ICO to various PNG sizes needed for MSIX
    $sizes = @(
        @{size="44x44"; name="Square44x44Logo.png"},
        @{size="150x150"; name="Square150x150Logo.png"},
        @{size="310x150"; name="Wide310x150Logo.png"},
        @{size="50x50"; name="StoreLogo.png"},
        @{size="620x300"; name="SplashScreen.png"}
    )
    
    foreach ($sizeInfo in $sizes) {
        $outputPath = Join-Path $OutputDir $sizeInfo.name
        try {
            & magick $IconPath -resize $sizeInfo.size $outputPath
            Write-Host "Created: $($sizeInfo.name)"
        } catch {
            Write-Warning "Failed to create $($sizeInfo.name): $($_.Exception.Message)"
        }
    }
} else {
    Write-Host "ImageMagick not found. Creating placeholder assets..."
    
    # Create simple placeholder PNG files
    $placeholderContent = @"
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==
"@
    
    $sizes = @("Square44x44Logo.png", "Square150x150Logo.png", "Wide310x150Logo.png", "StoreLogo.png", "SplashScreen.png")
    
    foreach ($name in $sizes) {
        $outputPath = Join-Path $OutputDir $name
        [System.Convert]::FromBase64String($placeholderContent) | Set-Content -Path $outputPath -Encoding Byte
        Write-Host "Created placeholder: $name"
    }
}

Write-Host "MSIX assets created in: $OutputDir"
