Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$targets = @(
    (Join-Path $repoRoot "build"),
    (Join-Path $repoRoot "dist"),
    (Join-Path $repoRoot "angels_and_demons_game\__pycache__"),
    (Join-Path $repoRoot "angels_and_demons_game\mechanics\__pycache__"),
    (Join-Path $repoRoot "angels_and_demons_game\models\__pycache__"),
    (Join-Path $repoRoot "angels_and_demons_game\ui\__pycache__"),
    (Join-Path $repoRoot "tools\__pycache__")
)

foreach ($target in $targets) {
    if (Test-Path -LiteralPath $target) {
        Write-Host "Removing $target"
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

Write-Host "Cleanup complete."
