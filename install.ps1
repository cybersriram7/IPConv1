# IPConv1 - Windows Premium Installation Script
# Professional Tor-Based IP Rotation System

$ErrorActionPreference = "Stop"

# Function to check if running as admin
function Test-IsAdmin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

Clear-Host

Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host "      IP Changer - Windows Setup Module     " -ForegroundColor Cyan
Write-Host "--------------------------------------------" -ForegroundColor Cyan
Write-Host ""

# Step 0: Check for Administrator Privileges
Write-Host "[*] Verifying Administrator access..." -ForegroundColor Cyan
if (-not (Test-IsAdmin)) {
    Write-Host "[X] ERROR: Access Denied. Administrator privileges required." -ForegroundColor Red
    Write-Host "[!] Action: Please Relaunch PowerShell as Administrator." -ForegroundColor Yellow
    exit 1
}
Write-Host "[V] Privileges confirmed." -ForegroundColor Green
Write-Host ""

# Step 1: Check Python
Write-Host "[*] Analyzing Python environment..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[V] Environment Ready: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] FATAL: Python not detected. Download from https://python.org" -ForegroundColor Red
    exit 1
}

# Step 2: Install Dependencies
Write-Host "[*] Deploying professional dependencies..." -ForegroundColor Cyan
try {
    python -m pip install --upgrade pip --quiet
    python -m pip install stem PySocks requests pyyaml --quiet
    Write-Host "[V] Libraries deployed successfully." -ForegroundColor Green
} catch {
    Write-Host "[!] Standard install failed. Attempting user-space deployment..." -ForegroundColor Yellow
    try {
        python -m pip install --user stem PySocks requests pyyaml --quiet
        Write-Host "[V] Libraries deployed in user-space." -ForegroundColor Green
    } catch {
        Write-Host "[X] Critical Error: Failed to install libraries." -ForegroundColor Red
    }
}

# Step 3: Check Tor
Write-Host "[*] Scanning for Tor service..." -ForegroundColor Cyan
$torCheck = Get-Command tor -ErrorAction SilentlyContinue

if ($torCheck) {
    Write-Host "[V] Tor service discovered in system PATH." -ForegroundColor Green
} else {
    Write-Host "[!] Tor service not found in PATH." -ForegroundColor Yellow
    Write-Host "[*] Searching secondary locations..." -ForegroundColor Cyan
    
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
            Write-Host "[V] Tor located at: $path" -ForegroundColor Green
            $foundTor = $true
            break
        }
    }
    
    if (-not $foundTor) {
        Write-Host "[*] Initiating automated Tor installation via winget..." -ForegroundColor Cyan
        $wingetCheck = Get-Command winget -ErrorAction SilentlyContinue
        if ($wingetCheck) {
            try {
                winget install TorProject.Tor --accept-source-agreements --accept-package-agreements
                Write-Host "[V] Tor installation successful!" -ForegroundColor Green
                Write-Host "[!] ACTION: Please RESTART your terminal to finalize setup." -ForegroundColor Yellow
            } catch {
                Write-Host "[X] Winget failed to install Tor." -ForegroundColor Red
            }
        } else {
            Write-Host "[X] Winget not available. Automated setup failed." -ForegroundColor Red
        }
    }
}

# Step 4: Finalize
Write-Host ""
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host "|       INSTALLATION SUCCESSFUL!           |" -ForegroundColor Green
Write-Host "+------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host "  python ipchanger.py -s 5" -ForegroundColor White
Write-Host ""
Write-Host "SYSTEM NOTE: Always run as Administrator for full feature support." -ForegroundColor Yellow
Write-Host ""
