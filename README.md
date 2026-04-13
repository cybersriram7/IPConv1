# IPCon v.1 & IP Changer

Professional IP Rotation System using the Tor network. This tool provides system-wide transparent proxying, multi-provider support, and a robust kill-switch.

## 🚀 Features
- **Automatic IP Rotation**: Change your public IP address at set intervals.
- **Transparent Proxy**: Routes all system-wide TCP traffic through Tor automatically.
- **Kill Switch**: Prevents IP leaks if the connection drops.
- **Multi-Provider Support**: Compatible with Tor, OpenVPN, and WireGuard.
- **DNS Leak Protection**: Forces requests through Tor's DNS port.
- **Fast Mode**: Optimized for high-speed IP rotation (down to 5 seconds).

---

Select your operating system below for tailored installation steps.

### 🐧 Linux (Ubuntu, Arch, Fedora, etc.)
Copy and paste the following commands to get started:

### 1. Clone & Set Permissions
```bash
git clone https://github.com/cybersriram7/IPConv1.git && cd IPConv1
chmod +x install.sh
```

### 2. Install System Dependencies
Select the command for your Linux distribution:

**Ubuntu / Debian:**
```bash
sudo apt-get update && sudo apt-get install -y tor curl python3 python3-pip
```

**Arch Linux:**
```bash
sudo pacman -Sy --noconfirm tor curl python python-pip
```

**Fedora / RHEL:**
```bash
sudo dnf install -y tor curl python3 python3-pip
```

### 3. Install Python Libraries
```bash
pip3 install -r requirements.txt --break-system-packages
```

### 4. Run the Professional Installer
This script configures Tor, sets up transparent proxying, and enables the CLI.
```bash
sudo ./install.sh
```

### 🪟 Windows (10/11)
Follow these steps to set up IPConv1 on Windows:

1.  **Open PowerShell** as Administrator.
2.  **Navigate** to the project directory:
    ```powershell
    cd Downloads\IPConv1
    ```
3.  **Run the Installer**:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; .\install.ps1
    ```
4.  **Restart PowerShell** to apply PATH changes if Tor was installed.

---

## 📖 Usage

### Start IP Rotation (Fast Mode - 5s)
```bash
sudo ipchanger -s 5
```


**Linux:**
```bash
sudo ipchanger -s 10
```

**Windows (Admin Required):**
```powershell
python ipchanger.py -s 10
```

| Flag | Description | Linux Example | Windows Example |
|------|-------------|---------------|-----------------|
| `-c` | Change Country | `sudo ipchanger -s 10 -c us` | `python ipchanger.py -c us` |
| `-k` | Kill Switch | `sudo ipchanger -k` | `python ipchanger.py -k` |
| `stop` | Stop all services | `sudo ipchanger stop` | `python ipchanger.py stop` |

> [!IMPORTANT]
> **Windows Administrator Rights**: On Windows, you MUST run your PowerShell or Command Prompt as **Administrator** to use the Kill Switch and System Proxy features.
>
> **Windows System Proxy**: On Windows, the tool automatically configures your **System-wide Proxy Settings**. This routes your browsers (Chrome, Edge) and most apps through Tor without any manual configuration!

---

## 📜 Verification Tests
Verify your anonymity and connection:

```bash
# Check current IP and Latency
    while true; do curl -s https://api.ipify.org; echo " - Checked at $(date +%H:%M:%S)"; sleep 5; done
---

## 🛑 How to Stop
 CRTL+C TO TERMINATE
    
```

---
*Developed by Sriram*
