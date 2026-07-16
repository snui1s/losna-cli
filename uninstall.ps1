# Losna CLI Uninstaller for Windows
# Usage: irm https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.ps1 | iex

$ErrorActionPreference = "Stop"
$INSTALL_DIR = Join-Path $env:USERPROFILE ".losna"
$BIN_DIR = Join-Path $INSTALL_DIR "bin"

Write-Host ""
Write-Host "  Losna CLI Uninstaller" -ForegroundColor Yellow
Write-Host "  =====================" -ForegroundColor Yellow
Write-Host ""

# --- Remove installation directory ---
if (Test-Path $INSTALL_DIR) {
    Write-Host "  [1/2] Removing $INSTALL_DIR ..." -ForegroundColor Cyan
    Remove-Item -Recurse -Force $INSTALL_DIR
} else {
    Write-Host "  [1/2] No installation found at $INSTALL_DIR" -ForegroundColor Gray
}

# --- Remove from PATH ---
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -like "*$BIN_DIR*") {
    Write-Host "  [2/2] Removing from PATH..." -ForegroundColor Cyan
    $newPath = ($userPath -split ";" | Where-Object { $_ -ne $BIN_DIR }) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
} else {
    Write-Host "  [2/2] PATH already clean" -ForegroundColor Gray
}

Write-Host ""
Write-Host "  Losna CLI uninstalled successfully." -ForegroundColor Green
Write-Host ""
