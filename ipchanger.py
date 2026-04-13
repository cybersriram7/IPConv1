#!/usr/bin/env python3
"""
IP Changer - Professional Tor-Based IP Rotation Tool
Uses the Tor network to automatically rotate your public IP address.
"""

import sys
import os
import time
import signal
import argparse
import subprocess
import shutil
import threading
import socket
import json
import urllib.request
from datetime import datetime
from pathlib import Path
import platform

try:
    import stem
    from stem.control import Controller
    from stem import Signal
    HAS_STEM = True
except ImportError:
    HAS_STEM = False

# ═══════════════════════════════════════════════════════════════════════
# ANSI Color Constants
# ═══════════════════════════════════════════════════════════════════════

class C:
    """ANSI color codes for terminal output."""
    RST  = '\033[0m'
    BOLD = '\033[1m'
    DIM  = '\033[2m'
    
    # Regular colors
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    GRAY    = '\033[90m'
    
    # Background
    BG_RED   = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE  = '\033[44m'
    BG_CYAN  = '\033[46m'


def colorize(text, *colors):
    """Apply multiple color codes to text."""
    prefix = ''.join(colors)
    return f"{prefix}{text}{C.RST}"


def is_admin():
    """Check if process has administrator privileges."""
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False


def is_windows():
    return platform.system() == "Windows"


def clear_screen():
    os.system('cls' if is_windows() else 'clear')


def run_cmd(cmd, sudo=True, capture=False, timeout=None):
    """Run a command with optional sudo on Linux/macOS."""
    if sudo and not is_windows():
        full_cmd = ["sudo"] + cmd
    else:
        full_cmd = cmd
    
    if capture:
        return subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
    else:
        return subprocess.run(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)


# ═══════════════════════════════════════════════════════════════════════
# Banner & Display
# ═══════════════════════════════════════════════════════════════════════

BANNER = r"""
██╗██████╗  ██████╗ ██████╗     ██╗   ██╗ ██╗
██║██╔══██╗██╔════╝██╔═══██╗    ██║   ██║███║
██║██████╔╝██║     ██║   ██║    ██║   ██║╚██║
██║██╔═══╝ ██║     ██║   ██║    ╚██╗ ██╔╝ ██║
██║██║     ╚██████╗╚██████╔╝     ╚████╔╝  ██║
╚═╝╚═╝      ╚═════╝ ╚═════╝      ╚═══╝    ╚═╝"""


def print_banner():
    """Print the application banner."""
    print(colorize(BANNER, C.CYAN, C.BOLD))
    print(colorize("                                          [ DEVELOPED BY SRIRAM ]", C.MAGENTA, C.BOLD))


def print_status_table(tor_status, interval, country=None, kill_switch=False):
    """Print the status table exactly like ipchanger format."""
    # Top border
    print(colorize("┌─────────────────────────┬────────────────────────────────────────┐", C.CYAN))
    
    # Header
    print(colorize("│", C.CYAN) + colorize(" Service                 ", C.WHITE, C.BOLD) + 
          colorize("│", C.CYAN) + colorize(" Information                            ", C.WHITE, C.BOLD) + 
          colorize("│", C.CYAN))
    
    # Separator
    print(colorize("├─────────────────────────┼────────────────────────────────────────┤", C.CYAN))
    
    # Tor Status
    tor_text = colorize("Tor service started", C.GREEN) if tor_status else colorize("Tor service failed", C.RED)
    print(colorize("│", C.CYAN) + colorize(" Tor Status              ", C.WHITE) + 
          colorize("│", C.CYAN) + f" {tor_text}" + " " * (39 - len("Tor service started")) + 
          colorize("│", C.CYAN))
    
    # Separator
    print(colorize("├─────────────────────────┼────────────────────────────────────────┤", C.CYAN))
    
    # IP Rotation
    rot_text = f"IP change every {interval} sec"
    padding = 39 - len(rot_text)
    print(colorize("│", C.CYAN) + colorize(" IP Rotation             ", C.WHITE) + 
          colorize("│", C.CYAN) + colorize(f" {rot_text}", C.YELLOW) + " " * padding + 
          colorize("│", C.CYAN))
    
    # Separator
    print(colorize("├─────────────────────────┼────────────────────────────────────────┤", C.CYAN))
    
    # Target Region
    region_text = f"Selected Region: {country.upper()}" if country else "Region: All (Global)"
    padding = 39 - len(region_text)
    print(colorize("│", C.CYAN) + colorize(" Target Region           ", C.WHITE) + 
          colorize("│", C.CYAN) + colorize(f" {region_text}", C.CYAN) + " " * padding + 
          colorize("│", C.CYAN))
    
    # Separator
    print(colorize("├─────────────────────────┼────────────────────────────────────────┤", C.CYAN))

    # Kill Switch
    ks_text = colorize("ENABLED (No Leaks)", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
    padding = 39 - (len("ENABLED (No Leaks)") if kill_switch else len("DISABLED"))
    print(colorize("│", C.CYAN) + colorize(" Network Kill Switch     ", C.WHITE) + 
          colorize("│", C.CYAN) + f" {ks_text}" + " " * padding + 
          colorize("│", C.CYAN))
    
    # Separator
    print(colorize("├─────────────────────────┼────────────────────────────────────────┤", C.CYAN))
    
    # CTRL+C
    print(colorize("│", C.CYAN) + colorize(" CTRL+C                  ", C.WHITE) + 
          colorize("│", C.CYAN) + colorize(" Press CTRL+C to Terminate              ", C.RED) + 
          colorize("│", C.CYAN))
    
    # Bottom border
    print(colorize("└─────────────────────────┴────────────────────────────────────────┘", C.CYAN))


def print_ip_change(ip, country=None):
    """Print an IP change event with timestamp."""
    now = datetime.now().strftime("%I:%M:%S %p")
    
    if country:
        print(colorize(f"[{now}]", C.GRAY) + 
              colorize(" Current IP → ", C.WHITE) + 
              colorize(f"{ip}", C.GREEN, C.BOLD) + 
              colorize(f"  ({country})", C.YELLOW))
    else:
        print(colorize(f"[{now}]", C.GRAY) + 
              colorize(" Current IP → ", C.WHITE) + 
              colorize(f"{ip}", C.GREEN, C.BOLD))


def print_error(msg):
    """Print error message."""
    print(colorize(f"[✗] {msg}", C.RED, C.BOLD))


def print_info(msg):
    """Print info message."""
    print(colorize(f"[*] {msg}", C.CYAN))


def print_success(msg):
    """Print success message."""
    print(colorize(f"[✓] {msg}", C.GREEN, C.BOLD))


def print_warning(msg):
    """Print warning message."""
    print(colorize(f"[!] {msg}", C.YELLOW))


# ═══════════════════════════════════════════════════════════════════════
# Transparent Proxy (Global Routing)
# ═══════════════════════════════════════════════════════════════════════

class TransparentProxy:
    """Manages iptables for global transparent proxying through Tor."""
    
    @staticmethod
    def enable(kill_switch=False):
        if is_windows():
            print_info(f"Enabling Windows System Proxy {'with KILL SWITCH' if kill_switch else ''}...")
            try:
                import winreg
                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                
                if kill_switch:
                    print_info("Enabling Windows Kill Switch (netsh)...")
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KillSwitch", "dir=out", "action=block"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Allow_Local", "dir=out", "action=allow", "remoteip=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                print_success(f"Windows System Proxy enabled {'(Kill-Switch ACTIVE)' if kill_switch else ''}.")
                return
            except Exception as e:
                print_error(f"Failed to enable Windows proxy: {e}")
                return

        print_info(f"Enabling transparent proxy (routing ALL traffic via Tor {'with KILL SWITCH' if kill_switch else ''})...")
        cmds = [
            ["iptables", "-t", "nat", "-F"],
            # Route DNS
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "5353"],
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "5353"],
            # Exclude Tor traffic itself
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "RETURN"],
            # Loopback safety
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"],
            # Route all other TCP traffic to Tor TransPort
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", "9040"],
        ]
        
        # Kill Switch Logic: Block all traffic NOT going to Tor ports
        if kill_switch:
            cmds_filter = [
                ["iptables", "-F", "OUTPUT"],
                ["iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9040", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "5353", "-j", "ACCEPT"],
                ["iptables", "-P", "OUTPUT", "DROP"]
            ]
            for cmd in cmds_filter:
                subprocess.run(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for cmd in cmds:
            subprocess.run(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        print_success(f"Global transparent proxy routing enabled {'(Kill-Switch ACTIVE)' if kill_switch else ''}.")

    @staticmethod
    def disable():
        if is_windows():
            print_info("Restoring Windows Proxy & Firewall settings...")
            try:
                import winreg
                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_KillSwitch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Allow_Local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print_success("Windows settings restored.")
            except:
                pass
            return
            
        print_info("Restoring network (Instant Cleanup)...")
        # Combine all cleanup into one sudo call to be FAST
        cleanup_cmd = "iptables -t nat -F && iptables -F OUTPUT && iptables -P OUTPUT ACCEPT"
        subprocess.run(["sudo", "bash", "-c", cleanup_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print_success("Network restored.")

# ═══════════════════════════════════════════════════════════════════════
# Tor Management
# ═══════════════════════════════════════════════════════════════════════

class TorManager:
    """Manages the Tor service and IP rotation via the Tor control port."""
    
    SOCKS_PORT = 9052
    CONTROL_PORT = 9051
    TOR_PASSWORD = ""  # Using cookie auth or no password by default
    
    def __init__(self):
        self._controller = None
        self._running = False
        self._ip_count = 0
        self._start_time = None
    
    def check_tor_installed(self):
        """Check if Tor is installed on the system."""
        if not HAS_STEM:
            print_error("Python 'stem' library is missing! Install it with: pip3 install stem")
            return False
        return shutil.which("tor") is not None
    
    def install_tor(self):
        """Attempt to install Tor."""
        print_info("Tor is not installed. Attempting to install...")
        
        # Detect package manager
        if shutil.which("apt-get"):
            cmd = ["sudo", "apt-get", "install", "-y", "tor"]
        elif shutil.which("pacman"):
            cmd = ["sudo", "pacman", "-S", "--noconfirm", "tor"]
        elif shutil.which("dnf"):
            cmd = ["sudo", "dnf", "install", "-y", "tor"]
        elif shutil.which("yum"):
            cmd = ["sudo", "yum", "install", "-y", "tor"]
        else:
            if is_windows():
                print_error("Tor is not found in PATH. Please install Tor Browser or Tor Expert Bundle.")
            else:
                print_error("Could not detect package manager. Please install Tor manually.")
            return False
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print_success("Tor installed successfully!")
                return True
            else:
                print_error(f"Tor installation failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            print_error(f"Failed to install Tor: {e}")
            return False
    
    def configure_tor(self, country=None):
        """Configure Tor for IP rotation, HTTP Tunneling, and Region Selection."""
        if is_windows():
            # Windows: usually we use a local data directory in the current folder or AppData
            torrc_path = Path("torrc")
            data_dir = Path("tor_data").absolute()
            data_dir.mkdir(exist_ok=True)
        else:
            torrc_path = Path("/etc/tor/torrc")
            data_dir = Path("/var/lib/tor")
        
        # Build configuration content
        config_lines = [
            "# Optimized by IPCO V.1",
            f"ControlPort {self.CONTROL_PORT}",
            "CookieAuthentication 1",
            f"SocksPort 127.0.0.1:{self.SOCKS_PORT}",
            "HTTPTunnelPort 127.0.0.1:9080",
            "VirtualAddrNetworkIPv4 10.192.0.0/10",
            "AutomapHostsOnResolve 1",
            "TransPort 9040",
            "DNSPort 5353",
            f"DataDirectory {data_dir}",
            # Performance & Speed Optimization
            "MaxCircuitDirtiness 5",
            "NewCircuitPeriod 5",
            "CircuitBuildTimeout 5",
            "MaxNewNymSpam 1",
            "EnforceDistinctSubnets 1",
            "UseEntryGuards 1",
            "NumEntryGuards 3",
            "LearnCircuitBuildTimeout 0"
        ]
        
        if country:
            config_lines.append(f"ExitNodes {{{country.lower()}}}")
            config_lines.append("StrictNodes 1")
            
        new_content = "\n".join(config_lines) + "\n"
        try:
            # Check if current config matches to save some time
            if torrc_path.exists() and "Optimized by IPCO V.1" in torrc_path.read_text():
                print_success("Tor already optimized, skipping configuration...")
                return True

            print_info(f"Applying Tor configuration {' (Region: ' + country + ')' if country else ''}...")
            
            if not is_windows():
                # Write config (needs sudo)
                proc = subprocess.run(
                    ["sudo", "tee", str(torrc_path)],
                    input=new_content.encode(),
                    capture_output=True, timeout=10
                )
            else:
                torrc_path.write_text(new_content)
                return True
            
            if proc.returncode != 0:
                # Fallback: temp file
                tmp_path = Path("/tmp/ipchanger_torrc")
                tmp_path.write_text(new_content)
                subprocess.run(
                    ["sudo", "cp", str(tmp_path), str(torrc_path)],
                    capture_output=True, timeout=10
                )
                tmp_path.unlink(missing_ok=True)
            
            print_success("Tor successfully re-configured")
            return True
            
        except Exception as e:
            print_warning(f"Could not update torrc: {e}")
            return True
    
    def start_tor_service(self):
        """Start the Tor system service."""
        if is_windows():
            print_info("Launching Tor process...")
            try:
                # Try to launch tor.exe (assuming it's in PATH)
                subprocess.Popen(["tor", "-f", "torrc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                return self._check_tor_running()
            except Exception as e:
                print_error(f"Failed to launch Tor: {e}")
                return False

        try:
            # First try pkill to clean any stuck instances
            subprocess.run(["sudo", "pkill", "-f", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
            
            # Start service
            subprocess.run(["sudo", "systemctl", "start", "tor"], capture_output=True, timeout=30)
            time.sleep(1)
            
            return self._check_tor_running()
            
        except Exception:
            # Fallback launch
            print_info("Trying fallback launch...")
            subprocess.Popen(["sudo", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)
            return self._check_tor_running()
    
    def stop_tor_service(self):
        """Stop the Tor service."""
        if is_windows():
            os.system("taskkill /f /im tor.exe >nul 2>&1")
            return
        subprocess.run(["sudo", "systemctl", "stop", "tor"], capture_output=True, timeout=10)
    
    def restart_tor_service(self):
        """Restart the Tor service."""
        self.stop_tor_service()
        return self.start_tor_service()
    
    def _check_tor_running(self):
        """Check if Tor SOCKS port is responding."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', self.SOCKS_PORT))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _check_control_port(self):
        """Check if Tor control port is responding."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', self.CONTROL_PORT))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def connect_controller(self):
        """Connect to the Tor control port using stem."""
        if not HAS_STEM: return False
        try:
            self._controller = Controller.from_port(port=self.CONTROL_PORT)
            self._controller.authenticate() # Use cookie auth
            return True
        except Exception as e:
            # Try once more with restart if needed
            return False
    
    def request_new_ip(self):
        """Request a new IP via stem signal."""
        if not HAS_STEM: return False
        try:
            if not self._controller or not self._controller.is_alive():
                if not self.connect_controller():
                    return False
            
            self._controller.signal(Signal.NEWNYM)
            self._ip_count += 1
            return True
        except Exception as e:
            return False
    
    def get_current_ip(self):
        """Fetch current IP through Tor's transparent routing."""
        try:
            # Transparent proxy handles this now
            import urllib.request
            req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.read().decode('utf-8').strip()
        except Exception:
            try:
                # Fallback to curl
                res = subprocess.run(["curl", "-s", "--max-time", "5", "https://api.ipify.org"], capture_output=True, text=True)
                return res.stdout.strip()
            except Exception:
                return None

    def get_ip_country(self, ip):
        """Fetch country info."""
        try:
            import urllib.request, json
            req = urllib.request.Request(f"http://ip-api.com/json/{ip}?fields=country", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('country', '')
        except Exception:
            return None

    def cleanup(self):
        """Cleanup controller."""
        if self._controller:
            try: self._controller.close()
            except Exception: pass


# ═══════════════════════════════════════════════════════════════════════
# Main Application Loop
# ═══════════════════════════════════════════════════════════════════════

class IPChanger:
    def __init__(self, interval=10, country=None, kill_switch=False):
        self.interval = interval
        self.country = country
        self.kill_switch = kill_switch
        self.tor = TorManager()
        self._stop_event = threading.Event()
        self._last_ip = None
        self._rotation_count = 0
    
    def run(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        clear_screen()
        print_banner()
        print()
        
        self.tor.configure_tor(country=self.country)
        print_info("Starting Tor service...")
        
        if not self.tor.start_tor_service():
            print_error("Failed to start Tor service automatically.")
            print_info("Try: sudo systemctl restart tor")
            return 1
            
        tor_running = self.tor._check_tor_running()
        self.tor.connect_controller()
        TransparentProxy.enable(kill_switch=self.kill_switch)
        
        print()
        print_status_table(tor_running, self.interval, country=self.country, kill_switch=self.kill_switch)
        print()
        
        # Initial rotation
        self.tor.request_new_ip()
        
        while not self._stop_event.is_set():
            # Get IP in background or with short timeout
            curr_ip = self.tor.get_current_ip()
            
            if curr_ip and curr_ip != self._last_ip:
                self._last_ip = curr_ip
                country = self.tor.get_ip_country(curr_ip)
                print_ip_change(curr_ip, country)
                self._rotation_count += 1
            
            # Request NEWNYM (with MaxNewNymSpam 1, this works very fast)
            if not self.tor.request_new_ip():
                # Fallback only if controller dies
                self.tor.restart_tor_service()
                time.sleep(1)
            
            # Wait for next interval
            if self._stop_event.wait(timeout=self.interval):
                break
        
        self._shutdown()
        return 0
    
    def _signal_handler(self, signum, frame):
        self._stop_event.set()
    
    def _shutdown(self):
        """Ultra-fast shutdown with immediate feedback."""
        # Visual feedback FIRST
        print(colorize("\n" + "─" * 67, C.CYAN))
        print(colorize("               Good byee! 👋💗", C.MAGENTA, C.BOLD))
        print_info(f"Total IP rotations: {self._rotation_count}")
        print()

        # Restore pure networking in the background/fast
        TransparentProxy.disable()
        
        # Non-blocking cleanup
        self.tor.cleanup()
        
        # Force exit immediately
        os._exit(0)


# ═══════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════════

def main():
    if not is_admin():
        if is_windows():
            print_error("ERROR: Must be run as Administrator on Windows.")
        else:
            print_error("ERROR: Must be run as root (sudo) on Linux.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="IP Changer - Tor IP Rotation Tool")
    
    # Optional flags that can be used directly or within 'run' command
    parser.add_argument("-s", "--seconds", type=int, default=10, help="Rotation interval (default: 10)")
    parser.add_argument("-c", "--country", type=str, default=None, help="Target country code (e.g. us, de, uk)")
    parser.add_argument("-k", "--kill-switch", action="store_true", help="Enable network kill-switch")
    
    subparsers = parser.add_subparsers(dest="command")
    
    run_parser = subparsers.add_parser("run", help="Start IP rotation (default)")
    run_parser.add_argument("-s", "--seconds", type=int, help="Rotation interval")
    run_parser.add_argument("-c", "--country", type=str, help="Target country code")
    run_parser.add_argument("-k", "--kill-switch", action="store_true", help="Enable kill-switch")
    
    subparsers.add_parser("stop", help="Stop IP rotation and restore network")
    subparsers.add_parser("test", help="Test current IP and anonymity")
    
    args, unknown = parser.parse_known_args()
    
    # Handle the command
    cmd = args.command or "run"
    
    # Consolidate arguments (favor subparser args if provided)
    secs = getattr(args, "seconds", 10) or 10
    country = getattr(args, "country", None)
    kill_switch = getattr(args, "kill_switch", False)
    
    if cmd == "run":
        changer = IPChanger(interval=secs, country=country, kill_switch=kill_switch)
        changer.run()
    elif cmd == "stop":
        print_info("Stopping IP Changer...")
        if not is_windows():
            subprocess.run(["sudo", "pkill", "-f", "ipchanger.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        TransparentProxy.disable()
    elif cmd == "test":
        tor = TorManager()
        ip = tor.get_current_ip()
        country_name = tor.get_ip_country(ip) if ip else "Unknown"
        print_banner()
        print()
        if ip:
            print_success(f"Connection Secure! Current IP: {ip} ({country_name})")
        else:
            print_error("Connection Failed or Not Routed through Tor.")

if __name__ == "__main__":
    main()
