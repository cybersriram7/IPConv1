#!/bin/bash
# -----------------------------------------------------------------------
# IP Changer - Installation Script (Robust Edition)
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
echo "|      IP Changer - Installation           |"
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

# Step 3: Tor Config
echo -e "${CYAN}[*] Configuring Tor...${NC}"
TORRC="/etc/tor/torrc"
if [ -f "$TORRC" ]; then
    if ! grep -q "ControlPort 9051" "$TORRC"; then
        echo -e "\nControlPort 9051\nCookieAuthentication 1" >> "$TORRC"
    fi
fi

# Step 4: Permissions
ACTUAL_USER=${SUDO_USER:-$USER}
if [ "$ACTUAL_USER" != "root" ]; then
    usermod -aG debian-tor "$ACTUAL_USER" 2>/dev/null || true
    echo -e "${GREEN}[V] Permissions updated for $ACTUAL_USER${NC}"
fi

# Step 5: Symlink
ln -sf "$(pwd)/ipchanger.py" /usr/local/bin/ipchanger
chmod +x ipchanger.py

echo -e "\n${GREEN}${BOLD}[V] Installation Complete!${NC}"
echo -e "Usage: sudo ipchanger -s 10"
echo ""
