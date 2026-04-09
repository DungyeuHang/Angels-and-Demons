Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "[1/4] Regenerating visual assets..."
python .\tools\generate_brand_assets.py

Write-Host "[2/4] Regenerating sound effects..."
python .\tools\generate_sound_fx.py

Write-Host "[3/4] Running compile check..."
python -m compileall angels_and_demons_game

Write-Host "[4/4] Building executable..."
pyinstaller "Angels and Demons.spec"

Write-Host "Build complete."
