# IPConv1 - Professional IP Rotation Tool
**Maximum Force Anonymity & Protection**

IPConv1 is a state-of-the-art IP rotation system designed for security researchers and privacy advocates. It forces your entire machine (Linux or Windows) through the Tor network with a cryptographically verified kill switch.

## 🚀 Key Features
- **Automatic IP Rotation**: High-speed public IP changes (minimum 5s interval).
- **Maximum Force Kill Switch**: Zero-leak policy. If Tor drops, your internet drops.
- **LAN Protection**: Stay connected to your Wi-Fi, Router, and Local Devices while being anonymous.
- **Region Lock**: Force your traffic to exit through specific countries (e.g., US, UK, DE).
- **Identity Verification**: Real-time health checks against Tor Project servers.
- **Cross-Platform**: Full support for Linux (Transparent Proxy) and Windows (System Proxy + Firewall).

---

## 🐧 Linux Setup
```bash
git clone https://github.com/cybersriram7/IPConv1.git && cd IPConv1
chmod +x install.sh
sudo ./install.sh
```

## 🪟 Windows Setup
1. Open **PowerShell as Administrator**.
2. Run:
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; .\install.ps1
```

---

## 📖 Usage

### Start Rotation (10s interval)
```bash
sudo ipchanger -s 10
```

### Start with Region Lock (e.g., United States)
```bash
sudo ipchanger -s 10 -c us
```

### Stop all services
```bash
sudo ipchanger stop
```

| Flag | Description | Example |
|------|-------------|---------|
| `-s` | Seconds between rotation | `sudo ipchanger -s 5` |
| `-c` | Country Code (2-letter) | `sudo ipchanger -c uk` |
| `stop` | Deactivate all settings | `sudo ipchanger stop` |

---

## 📜 Verification
While the tool is running, your traffic is locked. You can verify this by running:
```bash
curl https://check.torproject.org/api/ip
```
Expected Output: `{"IsTor":true, ...}`

---
*Developed with ❤️ by Sriram*
