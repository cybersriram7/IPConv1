#!/usr/bin/env python3
"""
IP Changer - Professional Tor-Based IP Rotation Tool
Optimized for stability, LAN connectivity, and "Maximum Force" leak protection.
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

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

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
    os.system('cls' if is_windows() else 'clear')

# -----------------------------------------------------------------------
# Banner & UI
# -----------------------------------------------------------------------

BANNER = r"""
  ___ ____   ____ ___  _   _ __     __  _ 
 |_ _|  _ \ / ___/ _ \| \ | |\ \   / / / |
  | || |_) | |  | | | |  \| | \ \ / /  | |
  | ||  __/| |__| |_| | |\  |  \ V /   | |
 |___|_|    \____\___/|_| \_|   \_/    |_|"""

def print_banner():
    print(colorize(BANNER, C.CYAN, C.BOLD))
    print(colorize("                                          [ DEVELOPED BY SRIRAM ]", C.MAGENTA, C.BOLD))

def print_status_table(tor_status, interval, country=None, kill_switch=False):
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
    
    ks_val = colorize("ACTIVE (MAX FORCE)", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
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
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                if kill_switch:
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KS", "dir=out", "action=block"])
                
                # Disable IPv6 on Windows
                TransparentProxy.run_cmd(["powershell", "-Command", "Disable-NetAdapterBinding -Name '*' -ComponentID ms_tcpip6"], silent=True)
                
                print_msg("V", "Windows Proxy enabled.", C.GREEN)
            except Exception as e: print_msg("X", f"Proxy fail: {e}", C.RED)
            return

        # Disable IPv6 on Linux
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"])
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"])

        for t in ["iptables", "ip6tables"]:
            if shutil.which(t):
                TransparentProxy.run_cmd(["sudo", t, "-t", "nat", "-F"])
                TransparentProxy.run_cmd(["sudo", t, "-F", "OUTPUT"])
                TransparentProxy.run_cmd(["sudo", t, "-P", "OUTPUT", "ACCEPT"])

        if not shutil.which("iptables"): return

        # Identify Tor User
        tor_users = ["debian-tor", "tor", "tor-socks", "tor-annex"]
        actual_tor_user = None
        for u in tor_users:
            try:
                import pwd
                pwd.getpwnam(u)
                actual_tor_user = u
                break
            except KeyError: continue

        if not actual_tor_user:
            print_msg("!", "Could not identify Tor user. Using default 'debian-tor'.", C.YELLOW)
            actual_tor_user = "debian-tor"

        # Hardened Networking Rules - "MAXIMUM FORCE" with LAN Protection
        cmds = [
            # Flush existing rules
            ["sudo", "iptables", "-t", "nat", "-F"],
            ["sudo", "iptables", "-F", "OUTPUT"],
            
            # --- NAT Table (Redirection) ---
            # Exclude Loopback & LAN from Redirection
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "127.0.0.0/8", "-j", "RETURN"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "192.168.0.0/16", "-j", "RETURN"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "10.0.0.0/8", "-j", "RETURN"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "172.16.0.0/12", "-j", "RETURN"],
            
            # Allow Tor User to bypass NAT
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", actual_tor_user, "-j", "RETURN"],
            
            # Redirect DNS (UDP 53) to Tor DNSPort
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            
            # Redirect all remaining TCP traffic to Tor's TransPort
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "-j", "REDIRECT", "--to-ports", "9040"],
            
            # --- Filter Table (Policy & Leaks) ---
            # Allow Loopback & LAN
            ["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "192.168.0.0/16", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "10.0.0.0/8", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "172.16.0.0/12", "-j", "ACCEPT"],
            
            # Allow Tor User to connect to the world
            ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", actual_tor_user, "-j", "ACCEPT"],
            
            # Allow traffic to TransPort & DNSPort (Already redirected)
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9040", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "9053", "-j", "ACCEPT"],
            
            # MAXIMUM FORCE: Block all other traffic to prevent any leaks
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "-j", "DROP"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "icmp", "-j", "DROP"],
            ["sudo", "iptables", "-P", "OUTPUT", "DROP"]
        ]
        
        for cmd in cmds: TransparentProxy.run_cmd(cmd)

        if shutil.which("ip6tables"):
            TransparentProxy.run_cmd(["sudo", "ip6tables", "-P", "OUTPUT", "DROP"])
        
        print_msg("V", "Maximum Force Transparent proxy active.", C.GREEN)

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
                # Re-enable IPv6 on Windows
                TransparentProxy.run_cmd(["powershell", "-Command", "Enable-NetAdapterBinding -Name '*' -ComponentID ms_tcpip6"], silent=True)
            except: pass
            return

        # Re-enable IPv6 on Linux
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"])

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

    def start(self, country=None):
        if is_windows():
            path = shutil.which("tor") or "tor.exe"
            subprocess.Popen([path, "-SocksPort", str(self.socks_port), "-ControlPort", str(self.ctrl_port)], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if shutil.which("systemctl"):
                subprocess.run(["sudo", "systemctl", "restart", "tor"], capture_output=True)
            elif shutil.which("service"):
                subprocess.run(["sudo", "service", "tor", "restart"], capture_output=True)
            else:
                bin_path = shutil.which("tor") or "/usr/bin/tor"
                subprocess.Popen(["sudo", bin_path, "--SocksPort", str(self.socks_port), "--ControlPort", str(self.ctrl_port), "--RunAsDaemon", "1"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for i in range(30):
            if self.is_running():
                if self.is_bootstrapped():
                    if country: self.apply_country_config(country)
                    return True
                if i % 5 == 0:
                    print_msg("*", f"Tor is bootstrapping... ({i*3}%)", C.YELLOW)
            time.sleep(1)
        return False

    def apply_country_config(self, country):
        if not self.connect(): return False
        try:
            self.controller.set_conf("ExitNodes", f"{{{country}}}")
            self.controller.set_conf("StrictNodes", "1")
            print_msg("V", f"Locked region to: {country.upper()}", C.CYAN)
            return True
        except Exception as e:
            print_msg("X", f"Region lock failed: {e}", C.RED)
            return False

    def is_bootstrapped(self):
        if not self.connect(): return False
        try:
            status = self.controller.get_info("status/bootstrap-phase")
            if "PROGRESS=100" in status: return True
            return False
        except: return False

    def is_running(self):
        try:
            with socket.create_connection(("127.0.0.1", self.socks_port), timeout=1): return True
        except: return False

    def connect(self):
        if not HAS_STEM: return False
        if self.controller and self.controller.is_alive(): return True
        try:
            self.controller = Controller.from_port(port=self.ctrl_port)
            self.controller.authenticate()
            return True
        except: return False

    def rotate(self):
        if not self.connect(): return False
        try:
            self.controller.signal(Signal.NEWNYM)
            return True
        except: return False

    def get_ip(self):
        urls = ["https://api.ipify.org", "https://icanhazip.com", "https://ifconfig.me/ip"]
        
        # Try via Transparent Proxy first
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=8) as res:
                    return res.read().decode().strip()
            except: continue
            
        # Fallback to direct SOCKS if Transparent Proxy fails
        if HAS_REQUESTS:
            proxies = {
                'http': f'socks5h://127.0.0.1:{self.socks_port}',
                'https': f'socks5h://127.0.0.1:{self.socks_port}'
            }
            for url in urls:
                try:
                    r = requests.get(url, proxies=proxies, timeout=10)
                    if r.status_code == 200: return r.text.strip()
                except: continue
        return None

    def get_country(self, ip):
        if not ip: return None
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country", timeout=5) as res:
                return json.loads(res.read().decode()).get('country')
        except:
            if HAS_REQUESTS:
                try:
                    proxies = {'http': f'socks5h://127.0.0.1:{self.socks_port}'}
                    r = requests.get(f"http://ip-api.com/json/{ip}?fields=country", proxies=proxies, timeout=5)
                    return r.json().get('country')
                except: pass
        return None

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

    def check_leaks(self):
        """Verifies that the connection is actually going through Tor."""
        try:
            with urllib.request.urlopen("https://check.torproject.org/api/ip", timeout=5) as res:
                data = json.loads(res.read().decode())
                return data.get("IsTor", False)
        except: return False

    def run(self):
        clear_screen()
        print_banner()
        print_msg("*", "Initializing Maximum Force system...", C.CYAN)
        
        if not self.tor.start(self.country):
            print_msg("X", "Could not start Tor service.", C.RED)
            return
        
        # Always enable transparent proxy for "Maximum Force"
        TransparentProxy.enable(True) # Force True for Maximum Force
        
        print_msg("*", "Verifying Tor connection...", C.YELLOW)
        if not self.check_leaks():
            print_msg("!", "WARNING: Potential Leak or Tor not active! Retrying...", C.RED)
            time.sleep(2)
            if not self.check_leaks():
                print_msg("X", "Critical Failure: Connection is NOT encrypted. Aborting.", C.RED)
                self.shutdown()
                return

        print_status_table(True, self.interval, self.country, True)
        
        try:
            while not self.stop_event.is_set():
                ip = self.tor.get_ip()
                if ip:
                    country = self.tor.get_country(ip)
                    print_ip_change(ip, country)
                
                if not self.tor.rotate():
                    print_msg("!", "Rotation signal failed, reconnecting...", C.YELLOW)
                    self.tor.connect()
                
                if self.stop_event.wait(self.interval): break
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        print_msg("*", "Cleaning up and restoring network...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller: self.tor.controller.close()
        print_msg("V", "Safe to exit. Bye!", C.GREEN)
        os._exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--seconds", type=int, default=10)
    parser.add_argument("-c", "--country", type=str)
    parser.add_argument("-k", "--kill-switch", action="store_true", help="Force maximum leak protection")
    args = parser.parse_args()

    if not is_admin():
        msg = "Administrator on Windows" if is_windows() else "root/administrator on Linux"
        print(colorize(f"[X] ERROR: Must run as {msg}.", C.RED, C.BOLD))
        sys.exit(1)

    changer = IPChanger(args.seconds, args.country, args.kill_switch)
    signal.signal(signal.SIGINT, lambda s, f: changer.stop_event.set())
    signal.signal(signal.SIGTERM, lambda s, f: changer.stop_event.set())
    changer.run()

if __name__ == "__main__":
    main()
