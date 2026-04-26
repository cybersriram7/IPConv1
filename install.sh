#!/bin/bash
# -----------------------------------------------------------------------
# IP Changer - Installation Script (Robust Ultra Fast Edition)
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
echo "|      IP Changer - Robust Setup           |"
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
fi

# Step 2: Python Libraries
echo -e "${CYAN}[*] Installing Python libraries...${NC}"
pip3 install -q stem PySocks requests --break-system-packages 2>/dev/null || \
pip3 install -q stem PySocks requests 2>/dev/null

# Step 3: Tor Config (Optimized but Stable)
echo -e "${CYAN}[*] Configuring Tor...${NC}"
TORRC="/etc/tor/torrc"
cat <<EOF > "$TORRC"
# Optimized by IPConv V.1 - MAXIMUM FORCE
ControlPort 9051
CookieAuthentication 0
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
chown debian-tor:debian-tor "$TORRC" 2>/dev/null || chown tor:tor "$TORRC" 2>/dev/null
chmod 644 "$TORRC"

# Step 4: Symlink
ln -sf "$(pwd)/ipchanger.py" /usr/local/bin/ipchanger
chmod +x ipchanger.py

# Step 5: Service Setup
echo -e "${CYAN}[*] Configuring Tor services...${NC}"
if command -v systemctl &> /dev/null; then
    # Try to enable both master and default instance
    systemctl enable tor 2>/dev/null || true
    systemctl enable tor@default 2>/dev/null || true
    systemctl restart tor 2>/dev/null || systemctl restart tor@default
elif command -v service &> /dev/null; then
    service tor restart
fi

echo -e "\n${GREEN}${BOLD}[V] Installation Complete!${NC}"
echo -e "Usage: sudo ipchanger -s 10"
echo ""
