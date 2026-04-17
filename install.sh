#!/bin/bash
# -----------------------------------------------------------------------
# IP Changer - Installation Script
# -----------------------------------------------------------------------

set -e

# ANSI Color Constants
RED='\033[0;91m'
GREEN='\033[0;92m'
CYAN='\033[0;96m'
YELLOW='\033[0;93m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}"
echo "+------------------------------------------+"
echo "|      IP Changer - Installation           |"
echo "+------------------------------------------+"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] This script needs root privileges.${NC}"
    echo -e "${YELLOW}[*] Re-running with sudo...${NC}"
    exec sudo bash "$0" "$@"
fi

# Step 1: Install system dependencies
echo -e "${CYAN}[*] Installing system dependencies...${NC}"

if command -v apt-get &> /dev/null; then
    apt-get update -qq
    apt-get install -y tor curl python3 python3-pip iptables iproute2 iputils-ping dnsutils net-tools
elif command -v pacman &> /dev/null; then
    pacman -S --noconfirm tor curl python python-pip iptables iproute2
elif command -v dnf &> /dev/null; then
    dnf install -y tor curl python3 python3-pip iptables iproute2
else
    echo -e "${RED}[X] Unsupported package manager. Install tor, curl, python3, and iptables manually.${NC}"
fi

# Step 2: Install Python dependencies
echo -e "${CYAN}[*] Installing Python dependencies...${NC}"
pip3 install -q stem PySocks requests 2>/dev/null || \
pip install -q stem PySocks requests 2>/dev/null || \
sudo pip3 install stem PySocks requests --break-system-packages 2>/dev/null

# Step 3: Configure Tor
echo -e "${CYAN}[*] Configuring Tor...${NC}"

TORRC="/etc/tor/torrc"
if [ -f "$TORRC" ]; then
    if ! grep -q "ControlPort 9051" "$TORRC"; then
        echo "" | tee -a "$TORRC" > /dev/null
        echo "# Added by IPCO V.1" | tee -a "$TORRC" > /dev/null
        echo "ControlPort 9051" | tee -a "$TORRC" > /dev/null
        echo "CookieAuthentication 1" | tee -a "$TORRC" > /dev/null
        echo -e "${GREEN}[V] Tor control port configured${NC}"
    else
        echo -e "${GREEN}[V] Tor already configured${NC}"
    fi
else
    echo -e "${YELLOW}[!] torrc not found. Creating default config...${NC}"
    mkdir -p /etc/tor
    echo "SocksPort 9050" | tee "$TORRC" > /dev/null
    echo "ControlPort 9051" | tee -a "$TORRC" > /dev/null
    echo "CookieAuthentication 1" | tee -a "$TORRC" > /dev/null
fi

# Step 4: Fix permissions for Tor
echo -e "${CYAN}[*] Fixing Tor permissions...${NC}"
ACTUAL_USER=${SUDO_USER:-$USER}
if [ "$ACTUAL_USER" != "root" ]; then
    usermod -aG debian-tor "$ACTUAL_USER" 2>/dev/null || true
    usermod -aG tor "$ACTUAL_USER" 2>/dev/null || true
    echo -e "${GREEN}[V] Added user $ACTUAL_USER to Tor groups${NC}"
fi

# Step 5: Create symlink for easy access
echo -e "${CYAN}[*] Creating command symlink...${NC}"
chmod +x "$SCRIPT_DIR/ipchanger.py"
ln -sf "$SCRIPT_DIR/ipchanger.py" /usr/local/bin/ipchanger 2>/dev/null || true

# Step 6: Enable and start Tor
echo -e "${CYAN}[*] Starting Tor service...${NC}"
if command -v systemctl &> /dev/null; then
    systemctl daemon-reload 2>/dev/null || true
    systemctl unmask tor 2>/dev/null || true
    systemctl enable tor 2>/dev/null || true
    systemctl restart tor 2>/dev/null || true
fi
service tor restart 2>/dev/null || true

# Wait for Tor to bootstrap
echo -e "${CYAN}[*] Waiting for Tor to bootstrap...${NC}"
MAX_RETRIES=30
COUNT=0
BOOTSTRAPPED=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    if ss -tln | grep -q ":9052" || ss -tln | grep -q ":9050"; then
        BOOTSTRAPPED=true
        break
    fi
    sleep 1
    COUNT=$((COUNT + 1))
    echo -ne "\r[*] Progress: $((COUNT * 100 / MAX_RETRIES))%"
done
echo -e "\r[*] Ready!                        "

# Verify
if [ "$BOOTSTRAPPED" = true ]; then
    echo -e "${GREEN}[V] Tor SOCKS port is active${NC}"
else
    echo -e "${YELLOW}[!] Tor bootstrap timed out. It might still be starting in the background.${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}+------------------------------------------+"
echo -e "|     Installation Complete!               |"
echo -e "+------------------------------------------+"
echo -e "${NC}"
echo ""
echo -e "${CYAN}Usage:${NC}"
echo -e "  ${BOLD}sudo ipchanger run -s 10${NC}     Change IP every 10 seconds"
echo -e "  ${BOLD}sudo ipchanger run -c us${NC}     Use US region only"
echo ""
