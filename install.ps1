# IPConv1 - Windows Installation Script
# Professional Tor-Based IP Rotation System

$ErrorActionPreference = "Stop"

# Function to check if running as admin
function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Clear-Host

Write-Host "+------------------------------------------+" -ForegroundColor Cyan
Write-Host "|      IP Changer - Windows Setup          |" -ForegroundColor Cyan
Write-Host "+------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# Step 0: Check for Administrator Privileges
Write-Host "[*] Checking for Administrator privileges..." -ForegroundColor Cyan
if (-not (Test-IsAdmin)) {
    Write-Host "[X] This installer requires Administrator privileges." -ForegroundColor Red
    Write-Host "[!] Please Relaunch PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}
Write-Host "[V] Running as Administrator" -ForegroundColor Green
Write-Host ""

# Step 1: Check Python
Write-Host "[*] Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[V] Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] Python not found! Please install Python from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Install Dependencies
Write-Host "[*] Installing Python dependencies..." -ForegroundColor Cyan
try {
    python -m pip install --upgrade pip
    python -m pip install stem PySocks requests pyyaml
    Write-Host "[V] Python dependencies installed." -ForegroundColor Green
} catch {
    Write-Host "[!] Pip install failed. Trying with --user..." -ForegroundColor Yellow
    try {
        python -m pip install --user stem PySocks requests pyyaml
        Write-Host "[V] Python dependencies installed." -ForegroundColor Green
    } catch {
        Write-Host "[X] Failed to install dependencies. Please run: pip install stem PySocks requests pyyaml" -ForegroundColor Red
    }
}

# Step 3: Check Tor
Write-Host "[*] Checking for Tor..." -ForegroundColor Cyan
$torCheck = Get-Command tor -ErrorAction SilentlyContinue

if ($torCheck) {
    Write-Host "[V] Tor is installed and in PATH." -ForegroundColor Green
} else {
    Write-Host "[!] Tor not found in PATH." -ForegroundColor Yellow
    Write-Host "[*] Checking common installation paths..." -ForegroundColor Cyan
    
    $commonPaths = @(
        "$env:ProgramFiles\Tor\tor.exe",
        "$env:ProgramFiles (x86)\Tor\tor.exe",
        "$env:ProgramData\Tor\tor.exe",
        "$env:LocalAppData\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
        "$HOME\Desktop\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
        "$HOME\Downloads\Tor Browser\Browser\TorBrowser\Tor\tor.exe",
        "$PSScriptRoot\tor.exe",
        "$PSScriptRoot\Tor\tor.exe"
    )
    
    $foundTor = $false
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            Write-Host "[V] Found Tor at: $path" -ForegroundColor Green
            Write-Host "[!] Note: To run 'tor' from anywhere, add this path to your Environment Variables." -ForegroundColor Yellow
            $foundTor = $true
            break
        }
    }
    
    if (-not $foundTor) {
        Write-Host "[!] Tor not found in common locations. Attempting to install via winget..." -ForegroundColor Cyan
        $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCheck) {
            try {
                winget install TorProject.Tor --accept-source-agreements --accept-package-agreements
                Write-Host "[V] Tor installation initiated via winget!" -ForegroundColor Green
                Write-Host "[!] Please RESTART your terminal after setup to update PATH." -ForegroundColor Yellow
            } catch {
                Write-Host "[X] Winget failed to install Tor." -ForegroundColor Red
                Write-Host "[*] Please download it manually: https://www.torproject.org/download/tor/" -ForegroundColor Cyan
            }
        } else {
            Write-Host "[X] winget not found. Please install Tor manually." -ForegroundColor Red
        }
    }
}

# Step 4: Finalize
Write-Host ""
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host "|     Installation Complete!               |" -ForegroundColor Green
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  python ipchanger.py run -s 10" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: The Windows version supports System-wide Proxy and Kill Switch." -ForegroundColor Green
Write-Host "Remember to always run your terminal as Administrator for full features." -ForegroundColor Yellow
Write-Host ""
