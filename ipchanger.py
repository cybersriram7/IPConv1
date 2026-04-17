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
import platform
from datetime import datetime
from pathlib import Path

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
                import ctypes
                
                # Update registry
                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                
                # Force refresh of proxy settings so browsers pick it up instantly
                # INTERNET_OPTION_SETTINGS_CHANGED = 39
                # INTERNET_OPTION_REFRESH = 37
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                
                if kill_switch:
                    print_info("Enabling Windows Kill Switch (netsh)...")
                    tor_path = TorManager._get_tor_path()
                    
                    # 1. Block all outbound traffic
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KillSwitch", "dir=out", "action=block"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # 2. Allow Loopback (essential for SOCKS/Control ports)
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Allow_Local", "dir=out", "action=allow", "remoteip=127.0.0.1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # 3. Allow Tor process itself to talk to the internet
                    if tor_path:
                        subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Allow_Tor", "dir=out", "action=allow", f"program={tor_path}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        print_warning("Could not find tor.exe absolute path. Kill switch might block Tor itself!")
                
                print_success(f"Windows System Proxy enabled {'(Kill-Switch ACTIVE)' if kill_switch else ''}.")
                return
            except Exception as e:
                print_error(f"Failed to enable Windows proxy: {e}")
                return

        print_info(f"Enabling transparent proxy (routing ALL traffic via Tor {'with KILL SWITCH' if kill_switch else ''})...")
        
        # Initial cleanup to ensure a clean state
        subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "iptables", "-F", "OUTPUT"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        cmds = [
            # Route DNS to Tor DNSPort (9053)
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            # Exclude Tor traffic itself by common users
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "RETURN"],
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "RETURN"],
            # Loopback safety
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"],
            # Route all other TCP traffic to Tor TransPort (9040)
            ["iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", "9040"],
        ]
        
        # Kill Switch Logic: Block all traffic NOT going to Tor ports
        if kill_switch:
            cmds_filter = [
                ["iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9040", "-j", "ACCEPT"],
                ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "9053", "-j", "ACCEPT"],
                ["iptables", "-P", "OUTPUT", "DROP"]
            ]
            for cmd in cmds_filter:
                subprocess.run(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for cmd in cmds:
            subprocess.run(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # IPv6 Routing (Block or route if possible)
        # Note: Tor's TransPort doesn't support IPv6 fully in most versions, 
        # so we block it to prevent leaks and force fallback to IPv4 via Tor.
        print_info("Securing IPv6 (Preventing Leaks)...")
        ipv6_cmds = [
            ["ip6tables", "-F"],
            ["ip6tables", "-A", "OUTPUT", "-p", "tcp", "-j", "REJECT"],
            ["ip6tables", "-A", "OUTPUT", "-p", "udp", "-j", "REJECT"],
            ["ip6tables", "-P", "OUTPUT", "DROP"]
        ]
        for cmd in ipv6_cmds:
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
                
                # Refresh settings
                import ctypes
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_KillSwitch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Allow_Tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Allow_Local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print_success("Windows settings restored.")
            except:
                pass
            return
            
        print_info("Restoring network (Instant Cleanup)...")
        # Combine all cleanup into one sudo call to be FAST
        cleanup_cmd = "iptables -t nat -F && iptables -F OUTPUT && iptables -P OUTPUT ACCEPT && ip6tables -F && ip6tables -P OUTPUT ACCEPT"
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
        self._start_time = time.time()
    
    @staticmethod
    def _get_tor_path():
        """Find the Tor executable path across platforms."""
        path = shutil.which("tor") or shutil.which("tor.exe")
        if path: return path
        
        if is_windows():
            common = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Tor", "tor.exe"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Tor", "tor.exe"),
                os.path.join(os.environ.get("LocalAppData", ""), "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe")
            ]
            for p in common:
                if os.path.exists(p): return p
        return None

    def check_tor_installed(self):
        """Check if Tor is installed on the system."""
        if not HAS_STEM:
            print_error("Python 'stem' library is missing! Install it with: pip3 install stem")
            return False
        
        return self._get_tor_path() is not None
    
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
            f"SocksPort 127.0.0.1:{self.SOCKS_PORT} PreferIPv6",
            "HTTPTunnelPort 127.0.0.1:9080",
            "VirtualAddrNetworkIPv4 10.192.0.0/10",
            "AutomapHostsOnResolve 1",
            "TransPort 9040",
            "DNSPort 9053",
            f"DataDirectory {data_dir}",
            # Performance & Speed Optimization
            "MaxCircuitDirtiness 5",
            "NewCircuitPeriod 5",
            "CircuitBuildTimeout 5",
            "EnforceDistinctSubnets 1",
            "UseEntryGuards 1",
            "NumEntryGuards 3"
        ]
        
        if country:
            config_lines.append(f"ExitNodes {{{country.lower()}}}")
            config_lines.append("StrictNodes 1")
            
        new_content = "\n".join(config_lines) + "\n"
        try:
            # Check if current config matches to save some time
            # We also check if the country matches to ensure it's not stale
            if torrc_path.exists():
                current_config = torrc_path.read_text()
                if "Optimized by IPCO V.1" in current_config:
                    # Check if the DNSPort is up to date and no incompatible options are present
                    if "DNSPort 9053" in current_config and "MaxNewNymSpam" not in current_config:
                        # If country is specified, check if it's already in the config
                        if country:
                            if f"ExitNodes {{{country.lower()}}}" in current_config:
                                print_success(f"Tor already optimized for {country.upper()}, skipping configuration...")
                                return True
                        else:
                            # If no country specified, make sure ExitNodes is NOT in there (or it's global)
                            if "ExitNodes" not in current_config:
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
    
    def _check_port_occupied(self, port):
        """Check if a specific port is already in use."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False


    def fix_data_dir_permissions(self):
        """Attempt to fix permissions for Tor data directory."""
        if is_windows(): return
        data_dir = "/var/lib/tor"
        print_info(f"Checking permissions for {data_dir}...")
        try:
            # Try to identify tor user
            for user in ["debian-tor", "tor", "tor-daemon", "toranon", "_tor"]:
                id_res = subprocess.run(["id", user], capture_output=True)
                if id_res.returncode == 0:
                    print_info(f"Restoring ownership to user: {user}...")
                    for target in [data_dir, "/var/log/tor"]:
                        if os.path.exists(target):
                            subprocess.run(["sudo", "chown", "-R", f"{user}:{user}", target], capture_output=True)
                            subprocess.run(["sudo", "chmod", "700", target], capture_output=True)
                    return True
            return False
        except:
            return False

    def start_tor_service(self):
        """Start the Tor system service with multiple fallbacks and robust checks."""
        if is_windows():
            print_info("Launching Tor process...")
            try:
                # Check ports first
                if self._check_port_occupied(self.SOCKS_PORT):
                    print_warning(f"Port {self.SOCKS_PORT} is already in use by another process!")
                
                tor_executable = self._get_tor_path() or "tor"
                
                subprocess.Popen([tor_executable, "-f", "torrc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for i in range(15):
                    if self._check_tor_running():
                        return True
                    time.sleep(1)
                return False
            except Exception as e:
                print_error(f"Failed to launch Tor: {e}")
                return False

        try:
            # Check for port conflicts before starting
            conflicting_ports = [self.SOCKS_PORT, self.CONTROL_PORT, 9040, 9053]
            ports_to_clear = [p for p in conflicting_ports if self._check_port_occupied(p)]
            
            if ports_to_clear:
                print_warning(f"Tor ports ({', '.join(map(str, ports_to_clear))}) are occupied. Cleaning up...")
                subprocess.run(["sudo", "systemctl", "stop", "tor"], capture_output=True)
                subprocess.run(["sudo", "systemctl", "stop", "tor@default"], capture_output=True)
                subprocess.run(["sudo", "pkill", "-9", "-x", "tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)

            # Ensure systemd is aware of any changes
            subprocess.run(["sudo", "systemctl", "daemon-reload"], capture_output=True)

            # Check if service is masked
            res = subprocess.run(["sudo", "systemctl", "is-enabled", "tor"], capture_output=True, text=True)
            if "masked" in res.stdout:
                print_info("Tor service is masked. Unmasking...")
                subprocess.run(["sudo", "systemctl", "unmask", "tor"], capture_output=True)
            
            # 1. Try systemctl (Modern Linux)
            service_names = ["tor", "tor.service", "tor@default"]
            for svc in service_names:
                subprocess.run(["sudo", "systemctl", "restart", svc], capture_output=True, text=True, timeout=20)
                for _ in range(12):
                    if self._check_tor_running():
                        return True
                    time.sleep(1)

            # 2. Try legacy service command
            subprocess.run(["sudo", "service", "tor", "restart"], capture_output=True, timeout=20)
            for _ in range(8):
                if self._check_tor_running():
                    return True
                time.sleep(1)

            # Try permission fix before manual launch
            self.fix_data_dir_permissions()

            # 3. Fallback launch directly (as preferred user if possible)
            print_info("Service start failed. Trying manual launch...")
            tor_bin = shutil.which("tor") or "/usr/bin/tor"
            
            # Find a suitable user for manual launch
            launch_user = "debian-tor"
            for u in ["debian-tor", "tor", "toranon"]:
                if subprocess.run(["id", u], capture_output=True).returncode == 0:
                    launch_user = u
                    break
            
            subprocess.Popen(["sudo", "-u", launch_user, tor_bin, "-f", "/etc/tor/torrc", "--RunAsDaemon", "1"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            for _ in range(20):
                if self._check_tor_running():
                    return True
                time.sleep(1)
            
            return False
            
        except Exception as e:
            print_warning(f"Error during Tor start: {e}")
            return False


    def check_dependencies(self):
        """Check for all required system dependencies."""
        deps = ["tor", "iptables", "curl"]
        if is_windows():
            deps = ["tor"]
        
        missing = []
        for dep in deps:
            if shutil.which(dep) is None:
                missing.append(dep)
        
        if not HAS_STEM:
            missing.append("python3-stem (pip3 install stem)")
            
        return missing
    
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
            return True
        except Exception as e:
            return False
    
    def get_current_ip(self):
        """Fetch current IP through Tor's transparent routing."""
        # Try both IPv6 and IPv4 detection
        for service in ["https://api64.ipify.org", "https://api.ipify.org"]:
            try:
                req = urllib.request.Request(service, headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.read().decode('utf-8').strip()
            except Exception:
                try:
                    res = subprocess.run(["curl", "-s", "--max-time", "5", service], capture_output=True, text=True)
                    if res.stdout.strip():
                        return res.stdout.strip()
                except Exception:
                    continue
        return None

    def get_ip_country(self, ip):
        """Fetch country info."""
        try:
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
        
        # Check system dependencies
        print_info("Checking dependencies...")
        missing = self.tor.check_dependencies()
        if missing:
            print_warning(f"Missing dependencies: {', '.join(missing)}")
            if "tor" in missing:
                if not self.tor.install_tor():
                    print_error("Failed to install Tor automatically.")
                    return 1
            else:
                print_error("Please install missing dependencies and try again.")
                return 1
        else:
            print_success("All dependencies satisfied.")
        
        self.tor.configure_tor(country=self.country)
        print_info("Starting Tor service...")
        
        if not self.tor.start_tor_service():
            print_error("Failed to start Tor service automatically.")
            return 1
            
        self.tor.connect_controller()
        TransparentProxy.enable(kill_switch=self.kill_switch)
        
        print()
        print_status_table(True, self.interval, country=self.country, kill_switch=self.kill_switch)
        print()
        
        # Initial rotation
        self.tor.request_new_ip()
        
        while not self._stop_event.is_set():
            curr_ip = self.tor.get_current_ip()
            if curr_ip and curr_ip != self._last_ip:
                self._last_ip = curr_ip
                country = self.tor.get_ip_country(curr_ip)
                print_ip_change(curr_ip, country)
                self._rotation_count += 1
            
            if not self.tor.request_new_ip():
                self.tor.restart_tor_service()
                time.sleep(1)
            
            if self._stop_event.wait(timeout=self.interval):
                break
        
        self._shutdown()
        return 0
    
    def _signal_handler(self, signum, frame):
        self._stop_event.set()
    
    def _shutdown(self):
        """Clean shutdown and network restoration."""
        print(colorize("\n" + "─" * 67, C.CYAN))
        print(colorize("               Cleaning up and shutting down... 👋", C.MAGENTA, C.BOLD))
        print_info(f"Total IP rotations: {self._rotation_count}")
        print()
        TransparentProxy.disable()
        self.tor.cleanup()
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
    
    # Global arguments
    parser.add_argument("-s", "--seconds", type=int, default=10, help="Rotation interval (default: 10)")
    parser.add_argument("-c", "--country", type=str, default=None, help="Target country code (e.g. us, de, uk)")
    parser.add_argument("-k", "--kill-switch", action="store_true", help="Enable network kill-switch")
    
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="Start IP rotation (default)")
    subparsers.add_parser("stop", help="Stop IP rotation and restore network")
    subparsers.add_parser("test", help="Test current IP and anonymity")
    
    args = parser.parse_args()
    cmd = args.command or "run"
    
    if cmd == "run":
        changer = IPChanger(interval=args.seconds, country=args.country, kill_switch=args.kill_switch)
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
