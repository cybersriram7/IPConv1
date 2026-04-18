#!/usr/bin/env python3
"""
IP Changer - Professional Tor-Based IP Rotation Tool
SUPER ROBUST EDITION - Enhanced Error Handling & Diagnostics
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

# Attempt to import stem for Tor control
try:
    import stem
    from stem.control import Controller
    from stem import Signal
    HAS_STEM = True
except ImportError:
    HAS_STEM = False

# -----------------------------------------------------------------------
# ANSI Color Constants
# -----------------------------------------------------------------------

class C:
    RST  = '\033[0m'
    BOLD = '\033[1m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    GRAY    = '\033[90m'

def colorize(text, *colors):
    return f"{''.join(colors)}{text}{C.RST}"

def is_admin():
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        return os.geteuid() == 0
    except: return False

def is_windows():
    return platform.system() == "Windows"

def clear_screen():
    if is_windows():
        os.system('cls')
    else:
        os.system('clear')

# -----------------------------------------------------------------------
# Banner & UI
# -----------------------------------------------------------------------

def get_banner():
    if is_windows():
        return r"""
  ___  ____   ____ ___  _   _ _   _ _ 
 |_ _|  _ \ / ___/ _ \| \ | | | | | |
  | || |_) | |  | | | |  \| | | | | |
  | ||  __/| |__| |_| | |\  | |_| | |
 |___|_|    \____\___/|_| \_|\___/|_|
                                VERSION: 3.1.0-WINDOWS-STABLE"""
    else:
        return r"""
  ___ ____   ____ ___  _   _ __     __  _ 
 |_ _|  _ \ / ___/ _ \| \ | |\ \   / / / |
  | || |_) | |  | | | |  \| | \ \ / /  | |
  | ||  __/| |__| |_| | |\  |  \ V /   | |
 |___|_|    \____\___/|_| \_|   \_/    |_|
                                VERSION: 2.5.0-ULTIMATE"""

def print_banner():
    print(colorize(get_banner(), C.CYAN, C.BOLD))
    print(colorize("                                          [ DEVELOPED BY SRIRAM ]", C.MAGENTA, C.BOLD))

def print_status_table(tor_status, interval, country=None, kill_switch=False):
    if is_windows():
        border = colorize("+-------------------------+----------------------------------------+", C.CYAN)
        print(border)
        print(f"{colorize('|', C.CYAN)} {colorize('Service', C.WHITE, C.BOLD).ljust(23+9)} {colorize('|', C.CYAN)} {colorize('Information', C.WHITE, C.BOLD).ljust(38+9)} {colorize('|', C.CYAN)}")
        print(border)
        
        status_text = colorize("Tor Active", C.GREEN, C.BOLD) if tor_status else colorize("Tor Inactive", C.RED, C.BOLD)
        print(f"{colorize('|', C.CYAN)} Tor Status              {colorize('|', C.CYAN)} {status_text.ljust(38+9)} {colorize('|', C.CYAN)}")
        
        rot_text = colorize(f"Rotate every {interval}s", C.YELLOW)
        print(f"{colorize('|', C.CYAN)} IP Rotation             {colorize('|', C.CYAN)} {rot_text.ljust(38+9)} {colorize('|', C.CYAN)}")
        
        region = f"Region: {country.upper()}" if country else "Region: Global"
        reg_text = colorize(region, C.CYAN)
        print(f"{colorize('|', C.CYAN)} Target Area             {colorize('|', C.CYAN)} {reg_text.ljust(38+9)} {colorize('|', C.CYAN)}")
        
        ks_val = colorize("ON (Protected)", C.GREEN, C.BOLD) if kill_switch else colorize("OFF (Unprotected)", C.GRAY)
        print(f"{colorize('|', C.CYAN)} Kill Switch             {colorize('|', C.CYAN)} {ks_val.ljust(38+9)} {colorize('|', C.CYAN)}")
        
        print(f"{colorize('|', C.CYAN)} CTRL+C                  {colorize('|', C.CYAN)} {colorize('Terminate Program', C.RED).ljust(38+9)} {colorize('|', C.CYAN)}")
        print(border)
    else:
        border = colorize("+-------------------------+----------------------------------------+", C.CYAN)
        print(border)
        print(colorize("|", C.CYAN) + colorize(" Service                 ", C.WHITE, C.BOLD) + colorize("|", C.CYAN) + colorize(" Information                            ", C.WHITE, C.BOLD) + colorize("|", C.CYAN))
        print(border)
        
        status_text = colorize("Tor service started", C.GREEN) if tor_status else colorize("Tor service failed", C.RED)
        print(f"{colorize('|', C.CYAN)} Tor Status              {colorize('|', C.CYAN)} {status_text.ljust(39+9)} {colorize('|', C.CYAN)}")
        
        rot_text = colorize(f"IP change every {interval} sec", C.YELLOW)
        print(f"{colorize('|', C.CYAN)} IP Rotation             {colorize('|', C.CYAN)} {rot_text.ljust(39+9)} {colorize('|', C.CYAN)}")
        
        region = f"Region: {country.upper()}" if country else "Region: All (Global)"
        reg_text = colorize(region, C.CYAN)
        print(f"{colorize('|', C.CYAN)} Target Region           {colorize('|', C.CYAN)} {reg_text.ljust(39+9)} {colorize('|', C.CYAN)}")
        
        ks_val = colorize("ACTIVE", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
        print(f"{colorize('|', C.CYAN)} Network Kill Switch     {colorize('|', C.CYAN)} {ks_val.ljust(39+9)} {colorize('|', C.CYAN)}")
        
        print(f"{colorize('|', C.CYAN)} CTRL+C                  {colorize('|', C.CYAN)} {colorize('Press CTRL+C to Terminate', C.RED).ljust(39+9)} {colorize('|', C.CYAN)}")
        print(border)

def print_ip_change(ip, country=None):
    now = datetime.now().strftime("%I:%M:%S %p")
    c_info = f" ({country})" if country else ""
    print(f"{colorize(f'[{now}]', C.GRAY)} {colorize('Current IP -> ', C.WHITE)}{colorize(ip, C.GREEN, C.BOLD)}{colorize(c_info, C.YELLOW)}")

def print_msg(prefix, msg, color):
    print(colorize(f"[{prefix}] {msg}", color))

# -----------------------------------------------------------------------
# Networking & Proxy
# -----------------------------------------------------------------------

class TransparentProxy:
    @staticmethod
    def run_cmd(args, silent=True):
        try:
            subprocess.run(args, stdout=subprocess.DEVNULL if silent else None, stderr=subprocess.DEVNULL if silent else None)
            return True
        except: return False

    @staticmethod
    def enable(kill_switch=False):
        if is_windows():
            try:
                import winreg, ctypes
                # 1. Update Proxy Settings
                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                
                # 2. Refresh Windows settings
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0) # SETTINGS_CHANGED
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0) # REFRESH
                
                # 3. Handle Kill Switch
                if kill_switch:
                    tor_path = TorManager._get_tor_path()
                    # Clean up old rules first to prevent errors
                    for rule in ["IPConv_KS", "IPConv_Local", "IPConv_Tor"]:
                        TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "delete", "rule", f"name={rule}"])
                    
                    # Add new rules
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KS", "dir=out", "action=block"])
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Local", "dir=out", "action=allow", "remoteip=127.0.0.1"])
                    if tor_path:
                        TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Tor", "dir=out", "action=allow", f"program={tor_path}"])
                
                print_msg("V", "Windows Proxy enabled.", C.GREEN)
                return True
            except Exception as e:
                print_msg("X", f"Failed to enable Windows proxy: {e}", C.RED)
                return False

        # Linux iptables logic
        try:
            for t in ["iptables", "ip6tables"]:
                if shutil.which(t):
                    TransparentProxy.run_cmd(["sudo", t, "-t", "nat", "-F"])
                    TransparentProxy.run_cmd(["sudo", t, "-F", "OUTPUT"])
                    TransparentProxy.run_cmd(["sudo", t, "-P", "OUTPUT", "ACCEPT"])

            if not shutil.which("iptables"):
                print_msg("X", "iptables not found!", C.RED)
                return False

            cmds = [
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "RETURN"],
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "RETURN"],
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"],
                ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--syn", "-j", "REDIRECT", "--to-ports", "9040"],
            ]
            if kill_switch:
                cmds += [
                    ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"],
                    ["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
                    ["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9040", "-j", "ACCEPT"],
                    ["sudo", "iptables", "-P", "OUTPUT", "DROP"]
                ]
            for cmd in cmds: TransparentProxy.run_cmd(cmd)
            if shutil.which("ip6tables"):
                TransparentProxy.run_cmd(["sudo", "ip6tables", "-P", "OUTPUT", "DROP"])
            print_msg("V", "Transparent proxy enabled.", C.GREEN)
            return True
        except Exception as e:
            print_msg("X", f"Failed to enable Linux proxy: {e}", C.RED)
            return False

    @staticmethod
    def disable():
        if is_windows():
            try:
                import winreg, ctypes
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_KS"])
                TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Local"])
                TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Tor"])
                print_msg("V", "Windows Proxy disabled.", C.GREEN)
            except: pass
            return

        for t in ["iptables", "ip6tables"]:
            if shutil.which(t):
                TransparentProxy.run_cmd(["sudo", t, "-t", "nat", "-F"])
                TransparentProxy.run_cmd(["sudo", t, "-F", "OUTPUT"])
                TransparentProxy.run_cmd(["sudo", t, "-P", "OUTPUT", "ACCEPT"])
        print_msg("V", "Network restored.", C.GREEN)

# -----------------------------------------------------------------------
# Tor Manager
# -----------------------------------------------------------------------

class TorManager:
    def __init__(self):
        self.socks_port = 9052
        self.ctrl_port = 9051
        self.controller = None

    @staticmethod
    def _get_tor_path():
        """Find the Tor executable path across platforms."""
        # 1. Check if it's already in the system PATH
        path = shutil.which("tor") or shutil.which("tor.exe")
        if path: return path

        if is_windows():
            # 2. Define common search locations
            script_dir = os.path.dirname(os.path.abspath(__file__))
            user_profile = os.environ.get("USERPROFILE", "")
            local_appdata = os.environ.get("LocalAppData", "")
            prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            prog_data = os.environ.get("ProgramData", "C:\\ProgramData")

            search_paths = [
                # Project & Runtime directories
                os.path.join(script_dir, "tor.exe"),
                os.path.join(script_dir, "Tor", "tor.exe"),
                os.path.join(os.getcwd(), "tor.exe"),
                os.path.join(os.getcwd(), "Tor", "tor.exe"),
                
                # AppData location (for restricted environments)
                os.path.join(os.environ.get("LocalAppData", ""), "IPConv1", "Tor", "tor.exe"),
                os.path.join(os.environ.get("LocalAppData", ""), "IPConv1", "tor.exe"),
                
                # Official Tor Expert Bundle / Service paths
                os.path.join(prog_files, "Tor", "tor.exe"),
                os.path.join(prog_files_x86, "Tor", "tor.exe"),
                os.path.join(prog_data, "Tor", "tor.exe"),
                
                # Tor Browser common locations
                os.path.join(local_appdata, "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
                os.path.join(user_profile, "Desktop", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
                os.path.join(user_profile, "Downloads", "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
                
                # Brave Browser (built-in Tor)
                os.path.join(local_appdata, "BraveSoftware", "Brave-Browser", "User Data", "tor", "tor.exe")
            ]
            
            for p in search_paths:
                if p and os.path.exists(p):
                    return os.path.abspath(p)
            
            # 3. Final Fail-Safe: Recursive search in script and AppData dirs
            search_bases = [script_dir, os.path.join(os.environ.get("LocalAppData", ""), "IPConv1")]
            for base in search_bases:
                if not base or not os.path.exists(base): continue
                try:
                    for root, dirs, files in os.walk(base):
                        if "tor.exe" in files:
                            return os.path.abspath(os.path.join(root, "tor.exe"))
                except: pass
        
        return None

    @staticmethod
    def get_latest_tor_url():
        """Scrape the Tor distribution server for the latest expert bundle URL."""
        base_url = "https://dist.torproject.org/torbrowser/"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(base_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode()
                # Find version folders (e.g., 15.0.9/)
                import re
                versions = re.findall(r'(\d+\.\d+\.\d+)/', content)
                if not versions:
                    return None
                
                # Sort versions and get latest
                def version_key(v): return [int(x) for x in v.split('.')]
                latest_v = sorted(versions, key=version_key, reverse=True)[0]
                
                # Construct the full download URL
                return f"{base_url}{latest_v}/tor-expert-bundle-windows-x86_64-{latest_v}.tar.gz"
        except Exception as e:
            print_msg("!", f"Failed to detect latest version: {e}", C.YELLOW)
            # Fallback to a relatively recent known version
            return "https://dist.torproject.org/torbrowser/15.0.9/tor-expert-bundle-windows-x86_64-15.0.9.tar.gz"

    @staticmethod
    def auto_install_tor():
        """Automatically download and install Tor Expert Bundle on Windows."""
        if not is_windows(): return False
        
        print_msg("*", "Tor not found. Attempting automatic installation...", C.CYAN)
        url = TorManager.get_latest_tor_url()
        if not url:
            print_msg("X", "Could not determine Tor download URL.", C.RED)
            return False
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Safety check: Avoid installing inside system32
        if "system32" in script_dir.lower():
            script_dir = os.path.join(os.environ.get("LocalAppData", os.getcwd()), "IPConv1")
            
        target_dir = os.path.join(script_dir, "Tor")
        tar_path = os.path.join(script_dir, "tor_expert.tar.gz")
        
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            
            print_msg("*", "Downloading Tor Expert Bundle (approx. 20MB)...", C.GRAY)
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(tar_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            import tarfile
            print_msg("*", "Extracting files...", C.GRAY)
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=target_dir)
            
            if os.path.exists(tar_path):
                os.remove(tar_path)
            
            # Verify extraction
            new_path = TorManager._get_tor_path()
            if new_path:
                print_msg("V", f"Tor installed and verified at: {new_path}", C.GREEN)
                return True
            else:
                print_msg("X", "Extraction succeeded but tor.exe was not found in the expected location.", C.RED)
                return False
        except Exception as e:
            print_msg("X", f"Auto-installation failed: {e}", C.RED)
            return False

    def start(self, country=None):
        path = self._get_tor_path()
        if not path:
            if is_windows():
                print_msg("!", "Tor is missing. Forcing automatic installation...", C.YELLOW)
                if self.auto_install_tor():
                    path = self._get_tor_path()
            
            if not path:
                print_msg("X", "FATAL: Could not locate or install Tor.", C.RED)
                return False

        # Cleanup existing processes to avoid port conflicts
        print_msg("*", "Preparing Tor environment...", C.CYAN)
        try:
            if is_windows():
                subprocess.run(["taskkill", "/f", "/im", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["sudo", "pkill", "-9", "-x", "tor"], capture_output=True)
            time.sleep(1)
        except: pass

        if is_windows():
            try:
                # Define a safe path for TorData (not in system32)
                tordata_path = os.path.join(os.environ.get("LocalAppData", os.getcwd()), "IPConv1", "TorData")
                if not os.path.exists(tordata_path): os.makedirs(tordata_path, exist_ok=True)

                # Launch Tor with open ControlPort (no auth needed for local)
                cmd = [
                    path, 
                    "-SocksPort", str(self.socks_port), 
                    "-ControlPort", str(self.ctrl_port), 
                    "--HashedControlPassword", "", # Disable password requirement
                    "--DataDirectory", tordata_path
                ]
                flags = 0
                if hasattr(subprocess, 'CREATE_NO_WINDOW'):
                    flags = subprocess.CREATE_NO_WINDOW
                
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
                print_msg("*", "Tor process launched.", C.GRAY)
                time.sleep(3) # Give it plenty of time
            except Exception as e:
                print_msg("X", f"Failed to launch Tor: {e}", C.RED)
                return False
        else:
            if shutil.which("systemctl"):
                subprocess.run(["sudo", "systemctl", "restart", "tor"], capture_output=True)
            else:
                subprocess.Popen(["sudo", path, "--SocksPort", str(self.socks_port), "--ControlPort", str(self.ctrl_port), "--RunAsDaemon", "1"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for bootstrap
        for i in range(25):
            if self.is_running(): return True
            time.sleep(1)
        return False

    def is_running(self):
        try:
            with socket.create_connection(("127.0.0.1", self.socks_port), timeout=1): return True
        except: return False

    def connect(self):
        if not HAS_STEM:
            return False
        try:
            # Try connecting to the control port
            self.controller = Controller.from_port(port=self.ctrl_port)
            self.controller.authenticate() # Now works without password/cookie
            return True
        except: return False

    def rotate(self):
        if not HAS_STEM: return False
        try:
            if not self.controller or not self.controller.is_alive():
                if not self.connect(): return False
            self.controller.signal(Signal.NEWNYM)
            return True
        except: return False

    def get_ip(self):
        """Fetch current IP address using Tor proxy if available."""
        services = ["https://api.ipify.org", "https://icanhazip.com", "https://ifconfig.me/ip"]
        
        # Try to use SOCKS5 proxy via PySocks if available
        try:
            import socks, socket
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.socks_port)
            socket.socket = socks.socksocket
        except: pass

        for url in services:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as res:
                    return res.read().decode().strip()
            except: continue
        return None

    def get_country(self, ip):
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country", timeout=5) as res:
                return json.loads(res.read().decode()).get('country')
        except: return None

# -----------------------------------------------------------------------
# Main Runner
# -----------------------------------------------------------------------

class IPChanger:
    def __init__(self, interval, country, kill_switch):
        self.interval = interval
        self.country = country
        self.kill_switch = kill_switch
        self.tor = TorManager()
        self.stop_event = threading.Event()
        self.rotation_count = 0

    def run(self):
        try:
            clear_screen()
            print_banner()
            print_msg("*", "Checking dependencies...", C.CYAN)
            
            if not HAS_STEM:
                print_msg("!", "Python library 'stem' is missing. Rotation will not work.", C.YELLOW)
                choice = input(colorize("[?] Would you like to install it now? (y/n): ", C.WHITE, C.BOLD)).lower()
                if choice == 'y':
                    print_msg("*", "Installing 'stem'...", C.GRAY)
                    try:
                        subprocess.run([sys.executable, "-m", "pip", "install", "stem"], check=True)
                        print_msg("V", "Library 'stem' installed successfully! Please restart the tool.", C.GREEN)
                        return
                    except:
                        print_msg("X", "Failed to install 'stem'. Please run: pip install stem", C.RED)
                        return
                else:
                    print_msg("!", "Rotation disabled due to missing 'stem'.", C.YELLOW)

            if not self.tor.start(self.country):
                print_msg("X", "FATAL: Tor service could not be initialized.", C.RED)
                return

            if not TransparentProxy.enable(self.kill_switch):
                print_msg("!", "Warning: Proxy could not be enabled. Manual configuration may be needed.", C.YELLOW)

            print_status_table(True, self.interval, self.country, self.kill_switch)
            
            last_ip = None
            while not self.stop_event.is_set():
                curr_ip = self.tor.get_ip()
                if curr_ip and curr_ip != last_ip:
                    last_ip = curr_ip
                    country = self.tor.get_country(curr_ip)
                    print_ip_change(curr_ip, country)
                    self.rotation_count += 1
                
                if not self.tor.rotate():
                    if HAS_STEM:
                        print_msg("!", "IP rotation signal failed. Re-attempting...", C.YELLOW)
                
                if self.stop_event.wait(self.interval): break
        except Exception as e:
            print_msg("X", f"CRITICAL ERROR in main loop: {e}", C.RED)
        finally:
            self.shutdown()

    def shutdown(self):
        print_msg("*", "Performing clean shutdown...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller:
            try: self.tor.controller.close()
            except: pass
        print_msg("V", f"Shutdown complete. Total rotations: {self.rotation_count}", C.GREEN)
        os._exit(0)

def main():
    try:
        parser = argparse.ArgumentParser(description="IP Changer - Professional IP Rotation Tool")
        parser.add_argument("-s", "--seconds", type=int, default=5, help="Interval in seconds (default: 5)")
        parser.add_argument("-c", "--country", type=str, help="Specific country code (e.g. us, de)")
        parser.add_argument("-k", "--kill-switch", action="store_true", help="Enable network kill switch")
        parser.add_argument("--check", action="store_true", help="Run system diagnostics")
        args = parser.parse_args()

        if args.check:
            print_banner()
            print_msg("*", "Running system diagnostics...", C.CYAN)
            print_msg("V", f"OS: {platform.system()} {platform.release()}", C.GREEN)
            
            if is_admin(): print_msg("V", "Privileges: Administrator/root", C.GREEN)
            else: print_msg("X", "Privileges: Standard User (Elevated required)", C.RED)
            
            path = TorManager._get_tor_path()
            if path: print_msg("V", f"Tor Executable: {path}", C.GREEN)
            else: print_msg("X", "Tor Executable: NOT FOUND", C.RED)
            
            if HAS_STEM: print_msg("V", "Library 'stem': INSTALLED", C.GREEN)
            else: print_msg("X", "Library 'stem': MISSING", C.RED)
            
            try:
                urllib.request.urlopen("https://google.com", timeout=5)
                print_msg("V", "Internet: CONNECTED", C.GREEN)
            except: print_msg("X", "Internet: DISCONNECTED", C.RED)
            
            print_msg("*", "Diagnostics complete.", C.CYAN)
            sys.exit(0)

        if not is_admin():
            msg = "Administrator on Windows" if is_windows() else "root (sudo) on Linux"
            print(colorize(f"[X] ERROR: This tool requires elevated privileges. Please run as {msg}.", C.RED, C.BOLD))
            sys.exit(1)

        changer = IPChanger(args.seconds, args.country, args.kill_switch)
        signal.signal(signal.SIGINT, lambda s, f: changer.stop_event.set())
        signal.signal(signal.SIGTERM, lambda s, f: changer.stop_event.set())
        changer.run()
    except Exception as e:
        print(colorize(f"[X] FATAL ERROR: {e}", C.RED, C.BOLD))
        sys.exit(1)

if __name__ == "__main__":
    main()
