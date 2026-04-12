# IPConv v.1 & IP Changer

Professional IP Rotation System using the Tor network. This tool provides system-wide transparent proxying, multi-provider support, and a robust kill-switch.

## 🚀 Features
- **Automatic IP Rotation**: Change your public IP address at set intervals.
- **Transparent Proxy**: Routes all system-wide TCP traffic through Tor automatically.
- **Kill Switch**: Prevents IP leaks if the connection drops.
- **Multi-Provider Support**: Compatible with Tor, OpenVPN, and WireGuard.
- **DNS Leak Protection**: Forces requests through Tor's DNS port.
- **Fast Mode**: Optimized for high-speed IP rotation (down to 5 seconds).

---

## 🛠 Installation & Setup

Copy and paste the following commands into your terminal to get started.

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

---

## 📖 Usage

### Start IP Rotation (Fast Mode - 5s)
```bash
sudo ipchanger -s 5
```

### Start IP Rotation (Default Mode - 10s)
```bash
sudo ipchanger -s 10
```

### Advanced Usage Flags
| Flag | Description | Example |
|------|-------------|---------|
| `-c` | Change Country | `sudo ipchanger -s 10 -c us` |
| `-k` | Enable Kill Switch | `sudo ipchanger -s 10 -k` |
| `stop` | Stop all services | `sudo ipchanger stop` |

---

## 📜 Verification Tests
Verify your anonymity and connection:

```bash
# Check current IP and Latency
python3 ipcon.py test

# Monitor system-wide rotation in real-time
watch -n 5 curl https://api.ipify.org
```

---

## 🛑 How to Stop
To stop the rotation and restore original network settings locally or via CLI:
```bash
sudo ipchanger stop
```


