#!/bin/bash
# -----------------------------------------------------------------------
# IP Changer - Installation Script (Universal Linux Edition)
# Works on: Ubuntu, Debian, Kali, Arch, Fedora, Manjaro, Pop!_OS
# -----------------------------------------------------------------------

set -e

# ANSI Colors
RED='\033[0;91m'
GREEN='\033[0;92m'
CYAN='\033[0;96m'
YELLOW='\033[0;93m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}"
echo "+------------------------------------------+"
echo "|      IP Changer - Universal Setup        |"
echo "+------------------------------------------+"
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] Please run this script with sudo.${NC}"
    exit 1
fi

# Step 1: Detect Package Manager & Install
echo -e "${CYAN}[*] Installing system dependencies...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get update -qq && apt-get install -y tor curl python3 python3-pip iptables
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm tor curl python python-pip iptables
elif command -v dnf &> /dev/null; then
    dnf install -y tor curl python3 python3-pip iptables
elif command -v zypper &> /dev/null; then
    zypper install -y tor curl python3 python3-pip iptables
else
    echo -e "${YELLOW}[!] Unknown package manager. Ensure tor, curl, and iptables are installed.${NC}"
fi

# Step 2: Python Libraries
echo -e "${CYAN}[*] Installing Python libraries...${NC}"
pip3 install -q stem PySocks requests --break-system-packages 2>/dev/null || \
pip3 install -q stem PySocks requests 2>/dev/null

# Step 3: Fix Tor Defaults (THE KEY FIX for Ubuntu/Debian)
# The tor-service-defaults-torrc sets CookieAuthentication=1 and SocksPort=9050
# which conflicts with our torrc. We MUST override it.
echo -e "${CYAN}[*] Patching Tor configuration for cross-distro compatibility...${NC}"

DEFAULTS_TORRC="/usr/share/tor/tor-service-defaults-torrc"
if [ -f "$DEFAULTS_TORRC" ]; then
    # Backup original
    cp "$DEFAULTS_TORRC" "${DEFAULTS_TORRC}.bak.ipconv" 2>/dev/null || true
    
    # Remove conflicting lines from defaults
    sed -i 's/^CookieAuthentication.*/#IPConv_Patched: &/' "$DEFAULTS_TORRC"
    sed -i 's/^CookieAuthFile.*/#IPConv_Patched: &/' "$DEFAULTS_TORRC"
    sed -i 's/^CookieAuthFileGroupReadable.*/#IPConv_Patched: &/' "$DEFAULTS_TORRC"
    # Comment out default SocksPort lines so ours takes priority
    sed -i '/^SocksPort /s/^/#IPConv_Patched: /' "$DEFAULTS_TORRC"
    echo -e "${GREEN}[V] Patched defaults-torrc (backup saved).${NC}"
fi

# Step 4: Write our torrc
echo -e "${CYAN}[*] Writing optimized torrc...${NC}"
TORRC="/etc/tor/torrc"
cat <<EOF > "$TORRC"
# Optimized by IPConv V.1 - Universal Linux Edition
ControlPort 9051
CookieAuthentication 0
HashedControlPassword
SocksPort 127.0.0.1:9052
HTTPTunnelPort 127.0.0.1:9080
VirtualAddrNetworkIPv4 10.192.0.0/10
AutomapHostsOnResolve 1
TransPort 127.0.0.1:9040
DNSPort 127.0.0.1:9053
DataDirectory /var/lib/tor

# Fast Rotation Settings
MaxCircuitDirtiness 10
NewCircuitPeriod 10
CircuitBuildTimeout 15
HardwareAccel 1
AvoidDiskWrites 1
EnforceDistinctSubnets 1
UseEntryGuards 1
NumEntryGuards 1

# IPv4 Enforcement
ClientUseIPv4 1
ClientUseIPv6 0
ClientPreferIPv6ORPort 0
EOF

# Detect Tor user and set ownership
if id "debian-tor" &>/dev/null; then
    chown debian-tor:debian-tor "$TORRC"
elif id "tor" &>/dev/null; then
    chown tor:tor "$TORRC"
fi
chmod 644 "$TORRC"

# Step 5: Symlink
ln -sf "$(pwd)/ipchanger.py" /usr/local/bin/ipchanger
chmod +x ipchanger.py

# Step 6: Restart Tor (handle all service naming schemes)
echo -e "${CYAN}[*] Restarting Tor service...${NC}"
if command -v systemctl &> /dev/null; then
    # Stop all variants first
    systemctl stop tor 2>/dev/null || true
    systemctl stop tor@default 2>/dev/null || true
    # Re-enable and start
    systemctl enable tor 2>/dev/null || true
    systemctl start tor 2>/dev/null || true
    systemctl restart tor@default 2>/dev/null || true
    
    # Wait and verify
    sleep 3
    if systemctl is-active --quiet tor@default 2>/dev/null || systemctl is-active --quiet tor 2>/dev/null; then
        echo -e "${GREEN}[V] Tor service is running.${NC}"
    else
        echo -e "${RED}[X] Tor failed to start. Check: journalctl -u tor@default${NC}"
    fi
elif command -v service &> /dev/null; then
    service tor restart
fi

echo -e "\n${GREEN}${BOLD}[V] Installation Complete!${NC}"
echo -e "Usage: sudo ipchanger -s 10"
echo ""
