# Losna CLI Installer for Windows
# Usage: irm https://raw.githubusercontent.com/snui1s/losna-cli/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$INSTALL_DIR = Join-Path $env:USERPROFILE ".losna"
$BIN_DIR = Join-Path $INSTALL_DIR "bin"
$REPO_URL = "https://github.com/snui1s/losna-cli.git"

Write-Host ""
Write-Host "  Losna CLI Installer" -ForegroundColor Yellow
Write-Host "  ===================" -ForegroundColor Yellow
Write-Host ""

# --- Check prerequisites ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  [ERROR] git is required. Install from https://git-scm.com" -ForegroundColor Red
    exit 1
}

$pythonCmd = $null
if (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCmd = "python3" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $pythonCmd = "python" }

if (-not $pythonCmd) {
    Write-Host "  [ERROR] Python 3.10+ is required. Install from https://python.org" -ForegroundColor Red
    exit 1
}

# --- Clone or update ---
if (Test-Path (Join-Path $INSTALL_DIR ".git")) {
    Write-Host "  [1/4] Updating repository..." -ForegroundColor Cyan
    Push-Location $INSTALL_DIR
    git pull --quiet
    Pop-Location
} else {
    if (Test-Path $INSTALL_DIR) { Remove-Item -Recurse -Force $INSTALL_DIR }
    Write-Host "  [1/4] Cloning repository..." -ForegroundColor Cyan
    git clone --quiet $REPO_URL $INSTALL_DIR
}

# --- Create venv ---
Write-Host "  [2/4] Creating virtual environment..." -ForegroundColor Cyan
& $pythonCmd -m venv (Join-Path $INSTALL_DIR ".venv")

# --- Install package (editable so git pull updates take effect immediately) ---
Write-Host "  [3/4] Installing dependencies..." -ForegroundColor Cyan
$pip = Join-Path $INSTALL_DIR ".venv\Scripts\pip.exe"
& $pip install --quiet -e $INSTALL_DIR

# --- Create wrapper command & add to PATH ---
Write-Host "  [4/4] Creating losna command..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path $BIN_DIR -Force | Out-Null

$wrapper = @"
@echo off
"%USERPROFILE%\.losna\.venv\Scripts\losna.exe" %*
"@
Set-Content -Path (Join-Path $BIN_DIR "losna.cmd") -Value $wrapper -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BIN_DIR*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$BIN_DIR", "User")
    $env:Path = "$env:Path;$BIN_DIR"
}

Write-Host ""
Write-Host "  Losna CLI installed successfully!" -ForegroundColor Green
Write-Host "  Restart your terminal, then type 'losna' to start." -ForegroundColor Yellow
Write-Host ""
