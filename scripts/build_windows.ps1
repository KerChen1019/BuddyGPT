Param(
    [switch]$SkipInstaller,
    [string]$PythonCmd = "py",
    [string]$PipIndexUrl = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== BuddyGPT Windows build =="

function Invoke-Step {
    param([string]$Command)
    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command"
    }
}

Write-Host "[1/4] Installing build dependencies..."
$pipIndexArg = ""
if ($PipIndexUrl) {
    $pipIndexArg = " --index-url `"$PipIndexUrl`""
}
Invoke-Step "$PythonCmd -m pip install --upgrade pip$pipIndexArg"
Invoke-Step "$PythonCmd -m pip install -r requirements.txt pyinstaller$pipIndexArg"

Write-Host "[2/4] Cleaning old build artifacts..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

Write-Host "[3/4] Building BuddyGPT.exe with PyInstaller..."
Invoke-Step "$PythonCmd -m PyInstaller --name BuddyGPT --noconfirm --clean --windowed --add-data `"assets;assets`" --add-data `"config.example.json;.`" main.py"

if ($SkipInstaller) {
    Write-Host "[4/4] Skipping installer build (requested)."
    Write-Host "Done. App output: dist\\BuddyGPT\\BuddyGPT.exe"
    exit 0
}

Write-Host "[4/4] Building Setup.exe with Inno Setup..."
$iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    Write-Warning "Inno Setup (iscc.exe) not found on PATH."
    Write-Host "Built app only: dist\\BuddyGPT\\BuddyGPT.exe"
    Write-Host "Install Inno Setup 6, then run: iscc.exe packaging\\BuddyGPT.iss"
    exit 0
}

Invoke-Step "`"$($iscc.Source)`" packaging\\BuddyGPT.iss"
Write-Host "Done. Installer output: dist\\installer\\BuddyGPT-Setup.exe"
