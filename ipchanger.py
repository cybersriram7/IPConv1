#!/usr/bin/env python3
"""
IP Changer - Ultimate Professional Edition
FIXED: Global System-Wide IP Rotation
"""

import os
import sys
import time
import socket
import subprocess
import signal
import shutil
import argparse
import threading
import json
import urllib.request
import requests
import platform
import random
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

# ═══════════════════════════════════════════════════════════════════════
# ANSI Color Constants
# ═══════════════════════════════════════════════════════════════════════

class C:
    RST  = '\033[0m'
    BOLD = '\033[1m'
    DIM  = '\033[2m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
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
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return os.geteuid() == 0
    except: return False

def is_windows():
    return platform.system() == "Windows"

def clear_screen():
    os.system('cls' if is_windows() else 'clear')

# ═══════════════════════════════════════════════════════════════════════
# Banner & UI
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
    print(colorize("+-------------------------+----------------------------------------+", C.CYAN))
    print(colorize("|", C.CYAN) + colorize(" Service                 ", C.WHITE, C.BOLD) + colorize("|", C.CYAN) + colorize(" Information                            ", C.WHITE, C.BOLD) + colorize("|", C.CYAN))
    print(colorize("+-------------------------+----------------------------------------+", C.CYAN))
    
    tor_text = colorize("Tor Engine Active", C.GREEN) if tor_status else colorize("Tor Engine Failed", C.RED)
    print(f"{colorize('|', C.CYAN)} Tor Status              {colorize('|', C.CYAN)} {tor_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    rot_text = colorize(f"System-Wide every {interval}s", C.YELLOW)
    print(f"{colorize('|', C.CYAN)} IP Rotation             {colorize('|', C.CYAN)} {rot_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    region = f"Region: {country.upper()}" if country else "Region: All (Global)"
    reg_text = colorize(region, C.CYAN)
    print(f"{colorize('|', C.CYAN)} Target Area             {colorize('|', C.CYAN)} {reg_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    ks_val = colorize("ACTIVE", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
    print(f"{colorize('|', C.CYAN)} Kill Switch             {colorize('|', C.CYAN)} {ks_val.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    print(f"{colorize('|', C.CYAN)} CTRL+C                  {colorize('|', C.CYAN)} {colorize('Safely Restore Network', C.RED).ljust(39+9)} {colorize('|', C.CYAN)}")
    print(colorize("+-------------------------+----------------------------------------+", C.CYAN))

def print_ip_change(ip, country=None):
    now = datetime.now().strftime("%I:%M:%S %p")
    c_info = f" ({country})" if country else ""
    print(f"{colorize(f'[{now}]', C.GRAY)} {colorize('Current IP -> ', C.WHITE)}{colorize(ip, C.GREEN, C.BOLD)}{colorize(c_info, C.YELLOW)}")

def print_msg(prefix, msg, color):
    print(colorize(f"[{prefix}] {msg}", color))

# ═══════════════════════════════════════════════════════════════════════
# Networking & Proxy (FIXED GLOBAL ROUTING)
# ═══════════════════════════════════════════════════════════════════════

class TransparentProxy:
    @staticmethod
    def enable(kill_switch=False):
        if is_windows():
            try:
                import winreg, ctypes
                reg_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                # Redirect everything to the SOCKS port
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                
                if kill_switch:
                    tor_path = TorManager._get_tor_path()
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KS", "dir=out", "action=block"], stdout=subprocess.DEVNULL)
                    subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Local", "dir=out", "action=allow", "remoteip=127.0.0.1"], stdout=subprocess.DEVNULL)
                    if tor_path:
                        subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Tor", "dir=out", "action=allow", f"program={tor_path}"], stdout=subprocess.DEVNULL)
                return True
            except: return False

        # Linux iptables logic - FIXED TO USE TRANSPARENT PORTS
        try:
            curr_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"
            # Flush existing rules
            subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], capture_output=True)
            subprocess.run(["sudo", "iptables", "-F", "OUTPUT"], capture_output=True)
            
            # 1. Block IPv6 entirely to force IPv4
            subprocess.run(["sudo", "ip6tables", "-P", "INPUT", "DROP"], capture_output=True)
            subprocess.run(["sudo", "ip6tables", "-P", "OUTPUT", "DROP"], capture_output=True)
            subprocess.run(["sudo", "ip6tables", "-P", "FORWARD", "DROP"], capture_output=True)
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"], capture_output=True)
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"], capture_output=True)

            # 2. Route DNS to Tor DNSPort (9053)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"], capture_output=True)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"], capture_output=True)
            
            # 3. Exclude Tor processes
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "RETURN"], capture_output=True)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "RETURN"], capture_output=True)
            
            # 4. Loopback safety
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"], capture_output=True)
            
            # 5. Route ALL remaining TCP traffic to Tor TransPort (9040)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "-j", "REDIRECT", "--to-ports", "9040"], capture_output=True)
            
            if kill_switch:
                subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "DROP"], capture_output=True)
                subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"], capture_output=True)
                subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], capture_output=True)
            
            return True
        except: return False

    @staticmethod
    def disable():
        if is_windows():
            try:
                import winreg, ctypes
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_KS"], stdout=subprocess.DEVNULL)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Local"], stdout=subprocess.DEVNULL)
                subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Tor"], stdout=subprocess.DEVNULL)
            except: pass
            return

        subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], capture_output=True)
        subprocess.run(["sudo", "iptables", "-F", "OUTPUT"], capture_output=True)
        subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "ip6tables", "-P", "INPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "ip6tables", "-P", "OUTPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"], capture_output=True)
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=0"], capture_output=True)

# ═══════════════════════════════════════════════════════════════════════
# Tor Management (FIXED WITH TRANSPORTS)
# ═══════════════════════════════════════════════════════════════════════

class TorManager:
    def __init__(self):
        self.socks_port = 9052
        self.ctrl_port = 9051
        self.trans_port = 9040
        self.dns_port = 9053
        self.controller = None

    @staticmethod
    def _get_tor_path():
        path = shutil.which("tor") or shutil.which("tor.exe")
        if path: return path
        if is_windows():
            local_appdata = os.environ.get("LocalAppData", "")
            common = [
                os.path.join(local_appdata, "Tor Browser", "Browser", "TorBrowser", "Tor", "tor.exe"),
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Tor", "tor.exe")
            ]
            for p in common:
                if os.path.exists(p): return p
        return None

    def start(self, country=None):
        path = self._get_tor_path()
        if not path: return False

        # Kill existing
        try:
            if is_windows(): subprocess.run(["taskkill", "/f", "/im", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else: subprocess.run(["sudo", "pkill", "-9", "-x", "tor"], capture_output=True)
            time.sleep(1)
        except: pass

        tordata = os.path.join(os.environ.get("LocalAppData", "/tmp"), "tor_ipcon")
        if not os.path.exists(tordata): os.makedirs(tordata, exist_ok=True)

        # START TOR WITH TRANSPORTS ENABLED
        cmd = [
            path, 
            "--SocksPort", str(self.socks_port), 
            "--ControlPort", str(self.ctrl_port),
            "--TransPort", str(self.trans_port), 
            "--DNSPort", str(self.dns_port),
            "--CookieAuthentication", "0", 
            "--MaxCircuitDirtiness", "5", 
            "--NewCircuitPeriod", "5",
            "--ClientUseIPv4", "1",
            "--ClientUseIPv6", "0",
            "--ClientPreferIPv6ORPort", "0",
            "--DataDirectory", tordata, 
            "--RunAsDaemon", "1"
        ]
        
        if country:
            cmd += ["--ExitNodes", f"{{{country.lower()}}}", "--StrictNodes", "1"]

        if is_windows():
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
        else:
            subprocess.Popen(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for bootstrap
        for i in range(25):
            if self.connect(): return True
            time.sleep(1)
        return False

    def connect(self):
        if not HAS_STEM: return False
        try:
            self.controller = Controller.from_port(port=self.ctrl_port)
            self.controller.authenticate(password="")
            return True
        except: return False

    def rotate(self):
        if not HAS_STEM: return False
        try:
            if not self.controller or not self.controller.is_alive():
                if not self.connect(): return False
            try:
                self.controller.signal(Signal.NEWNYM)
            except Exception as e:
                if "451" in str(e) or "Rate limited" in str(e):
                    for circ in self.controller.get_circuits():
                        try: self.controller.close_circuit(circ.id)
                        except: pass
                else: raise e
            return True
        except: return False

    def get_ip(self):
        """Fetch current IPv4 address through the Tor proxy."""
        # Force IPv4 only services
        services = ["https://api.ipify.org", "https://ipv4.icanhazip.com", "https://v4.ident.me"]
        random.shuffle(services)
        
        proxies = {
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        }
        for url in services:
            try:
                res = requests.get(url, proxies=proxies, timeout=5)
                if res.status_code == 200: 
                    ip = res.text.strip()
                    # Filter out any IPv6 just in case
                    if ":" in ip: continue
                    return ip
            except: continue
        return None

    def get_country(self, ip):
        try:
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=country", timeout=3)
            return res.json().get('country')
        except: return None

# ═══════════════════════════════════════════════════════════════════════
# Main Runner
# ═══════════════════════════════════════════════════════════════════════

class IPChanger:
    def __init__(self, interval, country, kill_switch):
        self.interval = interval
        self.country = country
        self.kill_switch = kill_switch
        self.tor = TorManager()
        self.stop_event = threading.Event()
        self.rotation_count = 0

    def run(self):
        clear_screen()
        print_banner()
        if not is_admin():
            print_msg("X", "Elevated privileges required!", C.RED)
            return

        print_msg("*", "Initializing global IP rotation...", C.CYAN)
        if not self.tor.start(self.country):
            print_msg("X", "Could not start Tor engine. Check if Tor is installed.", C.RED)
            return

        if not TransparentProxy.enable(self.kill_switch):
            print_msg("!", "Warning: Global routing failed. Only proxied apps will change IP.", C.YELLOW)

        print_status_table(True, self.interval, self.country, self.kill_switch)
        
        last_ip = None
        while not self.stop_event.is_set():
            curr_ip = self.tor.get_ip()
            if curr_ip and curr_ip != last_ip:
                last_ip = curr_ip
                country = self.tor.get_country(curr_ip)
                print_ip_change(curr_ip, country)
                self.rotation_count += 1
            
            self.tor.rotate()
            if self.stop_event.wait(self.interval): break
        
        self.shutdown()

    def shutdown(self):
        print_msg("*", "Restoring network and shutting down...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller: self.tor.controller.close()
        print_msg("V", f"Done. Total rotations: {self.rotation_count}", C.GREEN)
        os._exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--seconds", type=int, default=5)
    parser.add_argument("-c", "--country", type=str)
    parser.add_argument("-k", "--kill-switch", action="store_true")
    args = parser.parse_args()
    
    changer = IPChanger(args.seconds, args.country, args.kill_switch)
    signal.signal(signal.SIGINT, lambda s,f: changer.stop_event.set())
    changer.run()

if __name__ == "__main__":
    main()
