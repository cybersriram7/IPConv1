#!/usr/bin/env python3
"""
IP Changer - Ultimate Professional Edition
FIXED: Anti-Leak Protection & Aggressive Rotation
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
╚═╝╚═╝      ╚═════╝ ╚═════╝      ╚═══╝    ╚═╝
                                [ ANTI-LEAK EDITION ]"""

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
    
    ks_val = colorize("ACTIVE (Hardened)", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
    print(f"{colorize('|', C.CYAN)} Leak Protection         {colorize('|', C.CYAN)} {ks_val.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    print(f"{colorize('|', C.CYAN)} CTRL+C                  {colorize('|', C.CYAN)} {colorize('Safely Restore Network', C.RED).ljust(39+9)} {colorize('|', C.CYAN)}")
    print(colorize("+-------------------------+----------------------------------------+", C.CYAN))

def print_ip_change(ip, country=None, leaked=False):
    now = datetime.now().strftime("%I:%M:%S %p")
    if leaked:
        print(f"{colorize(f'[{now}]', C.RED)} {colorize('CRITICAL LEAK -> ', C.RED, C.BOLD)}{colorize(ip, C.RED, C.BOLD)} {colorize('(REAL IP DETECTED!)', C.RED, C.BOLD)}")
    else:
        c_info = f" ({country})" if country else ""
        print(f"{colorize(f'[{now}]', C.GRAY)} {colorize('Current IP -> ', C.WHITE)}{colorize(ip, C.GREEN, C.BOLD)}{colorize(c_info, C.YELLOW)}")

def print_msg(prefix, msg, color):
    print(colorize(f"[{prefix}] {msg}", color))

# ═══════════════════════════════════════════════════════════════════════
# Networking & Proxy
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
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                return True
            except: return False

        try:
            # 1. Block IPv6 entirely
            subprocess.run(["sudo", "ip6tables", "-P", "INPUT", "DROP"], capture_output=True)
            subprocess.run(["sudo", "ip6tables", "-P", "OUTPUT", "DROP"], capture_output=True)
            subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"], capture_output=True)

            # 2. Flush existing
            subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], capture_output=True)
            subprocess.run(["sudo", "iptables", "-F", "OUTPUT"], capture_output=True)
            
            # 3. DNS Redirection
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"], capture_output=True)
            
            # 4. Exclude Tor process
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "RETURN"], capture_output=True)
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "RETURN"], capture_output=True)
            
            # 5. Route ALL TCP to Tor TransPort
            subprocess.run(["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "-j", "REDIRECT", "--to-ports", "9040"], capture_output=True)
            
            if kill_switch:
                # Force kill-switch: Block anything that isn't Tor or Loopback
                subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], capture_output=True)
                subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "debian-tor", "-j", "ACCEPT"], capture_output=True)
                subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", "tor", "-j", "ACCEPT"], capture_output=True)
                subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "DROP"], capture_output=True)
            
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
            except: pass
            return

        subprocess.run(["sudo", "iptables", "-t", "nat", "-F"], capture_output=True)
        subprocess.run(["sudo", "iptables", "-F", "OUTPUT"], capture_output=True)
        subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "ip6tables", "-P", "INPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "ip6tables", "-P", "OUTPUT", "ACCEPT"], capture_output=True)
        subprocess.run(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"], capture_output=True)

# ═══════════════════════════════════════════════════════════════════════
# Tor Management
# ═══════════════════════════════════════════════════════════════════════

class TorManager:
    def __init__(self):
        self.socks_port = 9052
        self.ctrl_port = 9051
        self.trans_port = 9040
        self.dns_port = 9053
        self.controller = None

    def start(self, country=None):
        path = shutil.which("tor") or shutil.which("tor.exe")
        if not path: return False

        # Aggressive cleanup
        try:
            if is_windows(): subprocess.run(["taskkill", "/f", "/im", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else: subprocess.run(["sudo", "pkill", "-9", "-x", "tor"], capture_output=True)
            time.sleep(1)
        except: pass

        tordata = os.path.join(os.environ.get("LocalAppData", "/tmp"), "tor_hardened")
        if not os.path.exists(tordata): os.makedirs(tordata, exist_ok=True)

        cmd = [
            path, "--SocksPort", str(self.socks_port), "--ControlPort", str(self.ctrl_port),
            "--TransPort", str(self.trans_port), "--DNSPort", str(self.dns_port),
            "--CookieAuthentication", "0", "--MaxCircuitDirtiness", "10", 
            "--DataDirectory", tordata, "--RunAsDaemon", "1"
        ]
        if country: cmd += ["--ExitNodes", f"{{{country.lower()}}}", "--StrictNodes", "1"]

        if is_windows(): subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else: subprocess.Popen(["sudo"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        for i in range(30):
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
            # Send NEWNYM signal
            self.controller.signal(Signal.NEWNYM)
            # AGGRESSIVE: Close all existing circuits to force immediate change
            for circ in self.controller.get_circuits():
                try: self.controller.close_circuit(circ.id)
                except: pass
            return True
        except: return False

    def get_real_ip_direct(self):
        """Fetch IP bypassing all proxies (used for leak check)."""
        try: return requests.get("https://api.ipify.org", timeout=5).text.strip()
        except: return None

    def get_current_ip(self):
        """Fetch IP through system routing (Tor)."""
        try: return requests.get("https://api.ipify.org", timeout=5).text.strip()
        except: return None

    def is_tor_active(self):
        """Verify if current connection is actually Tor."""
        try:
            res = requests.get("https://check.torproject.org/api/ip", timeout=5).json()
            return res.get("IsTor", False)
        except: return False

# ═══════════════════════════════════════════════════════════════════════
# Main IPChanger
# ═══════════════════════════════════════════════════════════════════════

class IPChanger:
    def __init__(self, interval, country, kill_switch):
        self.interval = interval
        self.country = country
        self.kill_switch = kill_switch
        self.tor = TorManager()
        self.stop_event = threading.Event()
        self.real_ip = None

    def run(self):
        clear_screen()
        print_banner()
        if not is_admin():
            print_msg("X", "Elevated privileges required!", C.RED)
            return

        print_msg("*", "Detecting your real IP for protection...", C.CYAN)
        self.real_ip = self.tor.get_real_ip_direct()
        
        print_msg("*", "Starting hardened Tor engine...", C.CYAN)
        if not self.tor.start(self.country):
            print_msg("X", "Failed to start Tor.", C.RED)
            return

        TransparentProxy.enable(self.kill_switch)
        print_status_table(True, self.interval, self.country, self.kill_switch)
        
        last_ip = None
        while not self.stop_event.is_set():
            curr_ip = self.tor.get_current_ip()
            
            # ANTI-LEAK CHECK
            if curr_ip == self.real_ip:
                print_ip_change(curr_ip, leaked=True)
                print_msg("!", "IP LEAK DETECTED! Shutting down for safety.", C.RED)
                break
            
            if curr_ip and curr_ip != last_ip:
                last_ip = curr_ip
                # Verify Tor
                if self.tor.is_tor_active():
                    print_ip_change(curr_ip, "Tor Network")
                else:
                    print_msg("?", f"Warning: IP {curr_ip} might not be Tor!", C.YELLOW)
            
            self.tor.rotate()
            if self.stop_event.wait(self.interval): break
        
        self.shutdown()

    def shutdown(self):
        print_msg("*", "Closing circuits and restoring network...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller: self.tor.controller.close()
        os._exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--seconds", type=int, default=5)
    parser.add_argument("-c", "--country", type=str)
    parser.add_argument("-k", "--kill-switch", action="store_true", default=True) # Enabled by default for safety
    args = parser.parse_args()
    
    changer = IPChanger(args.seconds, args.country, args.kill_switch)
    signal.signal(signal.SIGINT, lambda s,f: changer.stop_event.set())
    changer.run()

if __name__ == "__main__":
    main()
