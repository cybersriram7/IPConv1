# IPConv1 - Windows Installation Script
# Professional Tor-Based IP Rotation System

$ErrorActionPreference = "Stop"

Clear-Host

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      IP Changer - Windows Setup          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 0: Check for Administrator Privileges
Write-Host "[*] Checking for Administrator privileges..." -ForegroundColor Cyan
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[✗] This installer requires Administrator privileges. Please Relaunch PowerShell as Administrator." -ForegroundColor Red
    exit 1
}
Write-Host "[✓] Running as Administrator" -ForegroundColor Green
Write-Host ""

# Step 1: Check Python
Write-Host "[*] Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[✗] Python not found! Please install Python from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Install Dependencies
Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install stem PySocks requests pyyaml

# Step 3: Check Tor
Write-Host "[*] Checking for Tor..." -ForegroundColor Cyan
$torCheck = Get-Command tor -ErrorAction SilentlyContinue
if ($torCheck) {
    Write-Host "[✓] Tor is installed and in PATH." -ForegroundColor Green
} else {
    Write-Host "[!] Tor not found in PATH." -ForegroundColor Yellow
    Write-Host "[*] You need the Tor Expert Bundle or Tor Browser installed." -ForegroundColor Yellow
    Write-Host "[*] Attempting to find Tor via winget..." -ForegroundColor Cyan
    try {
        winget install TorProject.Tor --accept-source-agreements --accept-package-agreements
        Write-Host "[✓] Tor installed via winget! Please RESTART your terminal after setup." -ForegroundColor Green
    } catch {
        Write-Host "[!] Could not install Tor via winget. Please download it manually from https://www.torproject.org/download/tor/" -ForegroundColor Red
    }
}

# Step 4: Finalize
Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║     Installation Complete!                ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  python ipchanger.py -s 10" -ForegroundColor White
Write-Host "  python ipcon.py start --interval 30" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: The Windows version now supports System-wide Proxy and Kill Switch!" -ForegroundColor Green
Write-Host "Remember to always run your terminal as Administrator." -ForegroundColor Yellow
Write-Host ""
