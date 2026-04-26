#!/bin/bash
# -----------------------------------------------------------------------
# IP Changer - Installation Script (Ultra Fast Edition)
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
echo "|      IP Changer - Ultra Fast Setup       |"
echo "+------------------------------------------+"
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] Please run this script with sudo.${NC}"
    exit 1
fi

# Step 1: System Packages
echo -e "${CYAN}[*] Installing system dependencies...${NC}"
if command -v apt-get &> /dev/null; then
    apt-get update -qq && apt-get install -y tor curl python3 python3-pip iptables
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm tor curl python python-pip iptables
else
    echo -e "${YELLOW}[!] Unknown package manager. Ensure tor, curl, and iptables are installed.${NC}"
fi

# Step 2: Python Libraries
echo -e "${CYAN}[*] Installing Python libraries...${NC}"
pip3 install -q stem PySocks requests --break-system-packages 2>/dev/null || \
pip3 install -q stem PySocks requests 2>/dev/null

# Step 3: Tor Config (Optimized for ULTRA SPEED)
echo -e "${CYAN}[*] Configuring Tor for Ultra Speed...${NC}"
TORRC="/etc/tor/torrc"
cat <<EOF > "$TORRC"
# Optimized by IPConv V.1 - ULTRA FAST MODE
ControlPort 9051
CookieAuthentication 0
SocksPort 127.0.0.1:9052
HTTPTunnelPort 127.0.0.1:9080
VirtualAddrNetworkIPv4 10.192.0.0/10
AutomapHostsOnResolve 1
TransPort 127.0.0.1:9040
DNSPort 127.0.0.1:9053
DataDirectory /var/lib/tor

# Ultra Fast Rotation Settings
MaxCircuitDirtiness 5
NewCircuitPeriod 5
CircuitBuildTimeout 5
KeepalivePeriod 60
MaxCircuitBuildRetries 2
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
chown debian-tor:debian-tor "$TORRC" 2>/dev/null || chown tor:tor "$TORRC" 2>/dev/null
chmod 644 "$TORRC"

# Step 4: Permissions
ACTUAL_USER=${SUDO_USER:-$USER}
if [ "$ACTUAL_USER" != "root" ]; then
    usermod -aG debian-tor "$ACTUAL_USER" 2>/dev/null || true
    echo -e "${GREEN}[V] Permissions updated for $ACTUAL_USER${NC}"
fi

# Step 5: Symlink
ln -sf "$(pwd)/ipchanger.py" /usr/local/bin/ipchanger
chmod +x ipchanger.py

# Step 6: Service Restart
echo -e "${CYAN}[*] Restarting Tor service (Ultra Fast Mode)...${NC}"
if command -v systemctl &> /dev/null; then
    systemctl restart tor
    systemctl enable tor
elif command -v service &> /dev/null; then
    service tor restart
fi

echo -e "\n${GREEN}${BOLD}[V] Ultra Fast Installation Complete!${NC}"
echo -e "Usage: sudo ipchanger -s 5"
echo ""
