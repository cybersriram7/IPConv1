#!/bin/bash
# ═══════════════════════════════════════════════════════
# IP Changer - Installation Script
# ═══════════════════════════════════════════════════════

set -e

RED='\033[0;91m'
GREEN='\033[0;92m'
CYAN='\033[0;96m'
YELLOW='\033[0;93m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════╗"
echo "║      IP Changer - Installation           ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] Some features require root. Re-running with sudo...${NC}"
fi

# Step 1: Install system dependencies
echo -e "${CYAN}[*] Installing system dependencies...${NC}"

if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y tor curl python3 python3-pip iptables iproute2
    sudo apt-get install -y iputils-ping dnsutils net-tools
elif command -v pacman &> /dev/null; then
    sudo pacman -S --noconfirm tor curl python python-pip
elif command -v dnf &> /dev/null; then
    sudo dnf install -y tor curl python3 python3-pip
else
    echo -e "${RED}[✗] Unsupported package manager. Install tor, curl, python3, pip manually.${NC}"
fi

# Step 2: Install Python dependencies
echo -e "${CYAN}[*] Installing Python dependencies...${NC}"
pip3 install --user -q stem PySocks requests pyyaml 2>/dev/null || \
pip install --user -q stem PySocks requests pyyaml 2>/dev/null || \
sudo pip3 install stem PySocks requests pyyaml --break-system-packages 2>/dev/null || \
sudo pip3 install stem PySocks requests pyyaml 2>/dev/null

# Step 3: Configure Tor
echo -e "${CYAN}[*] Configuring Tor...${NC}"

TORRC="/etc/tor/torrc"
if [ -f "$TORRC" ]; then
    if ! grep -q "ControlPort 9051" "$TORRC"; then
        echo "" | sudo tee -a "$TORRC" > /dev/null
        echo "# Added by IP Changer" | sudo tee -a "$TORRC" > /dev/null
        echo "ControlPort 9051" | sudo tee -a "$TORRC" > /dev/null
        echo "CookieAuthentication 1" | sudo tee -a "$TORRC" > /dev/null
        echo -e "${GREEN}[✓] Tor control port configured${NC}"
    else
        echo -e "${GREEN}[✓] Tor already configured${NC}"
    fi
else
    echo -e "${YELLOW}[!] torrc not found. Creating default config...${NC}"
    sudo mkdir -p /etc/tor
    echo "SocksPort 9050" | sudo tee "$TORRC" > /dev/null
    echo "ControlPort 9051" | sudo tee -a "$TORRC" > /dev/null
    echo "CookieAuthentication 1" | sudo tee -a "$TORRC" > /dev/null
fi

# Step 4: Fix permissions for Tor cookie
echo -e "${CYAN}[*] Fixing Tor permissions...${NC}"
if id -nG "$USER" | grep -qw "debian-tor"; then
    echo -e "${GREEN}[✓] User already in debian-tor group${NC}"
else
    sudo usermod -aG debian-tor "$USER" 2>/dev/null || true
    echo -e "${GREEN}[✓] Added user to debian-tor group${NC}"
fi

# Step 5: Create symlink for easy access
echo -e "${CYAN}[*] Creating command symlink...${NC}"
chmod +x "$SCRIPT_DIR/ipchanger.py"
sudo ln -sf "$SCRIPT_DIR/ipchanger.py" /usr/local/bin/ipchanger 2>/dev/null || true

# Step 6: Enable and start Tor
echo -e "${CYAN}[*] Starting Tor service...${NC}"
sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl unmask tor 2>/dev/null || true
sudo systemctl enable tor 2>/dev/null || true
# Try restarting both master and default instance
sudo systemctl restart tor@default 2>/dev/null || true
sudo systemctl restart tor 2>/dev/null || sudo service tor restart 2>/dev/null || true

# Wait for Tor to bootstrap
echo -e "${CYAN}[*] Waiting for Tor to bootstrap...${NC}"
MAX_RETRIES=45
COUNT=0
BOOTSTRAPPED=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    # Check for SOCKS port (9052)
    if ss -tln | grep -q ":9052"; then
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
    echo -e "${GREEN}[✓] Tor SOCKS port (9052) is active${NC}"
    if ss -tlnp 2>/dev/null | grep -q ":9051" || ss -tln 2>/dev/null | grep -q ":9051"; then
        echo -e "${GREEN}[✓] Tor Control port (9051) is active${NC}"
    else
        echo -e "${YELLOW}[!] Tor Control port (9051) not detected, but SOCKS is ready.${NC}"
    fi
else
    echo -e "${RED}[✗] Tor bootstrap timed out. Please check 'sudo journalctl -u tor'${NC}"
fi


echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║     Installation Complete!                ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Usage:${NC}"
echo -e "  ${BOLD}ipchanger -s 10${NC}     Change IP every 10 seconds"
echo -e "  ${BOLD}ipchanger -s 30${NC}     Change IP every 30 seconds"
echo -e "  ${BOLD}python3 $SCRIPT_DIR/ipchanger.py -s 10${NC}"
echo ""
