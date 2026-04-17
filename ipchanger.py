#!/usr/bin/env python3
"""
IP Changer - Professional Tor-Based IP Rotation Tool
Optimized for stability and cross-platform compatibility.
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
    print(f"{colorize('|', C.CYAN)} Tor Status              {colorize('|', C.CYAN)} {status_text.ljust(39+9)} {colorize('|', C.CYAN)}") # +9 for ANSI escape codes
    
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
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Internet Settings", 0, winreg.KEY_WRITE)
                winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, "socks=127.0.0.1:9052")
                winreg.CloseKey(key)
                ctypes.windll.wininet.InternetSetOptionW(0, 39, 0, 0)
                ctypes.windll.wininet.InternetSetOptionW(0, 37, 0, 0)
                if kill_switch:
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KS", "dir=out", "action=block"])
                print_msg("V", "Windows Proxy enabled.", C.GREEN)
            except Exception as e: print_msg("X", f"Proxy fail: {e}", C.RED)
            return

        # Linux iptables logic
        tools = ["iptables", "ip6tables"]
        for t in tools:
            if shutil.which(t):
                TransparentProxy.run_cmd(["sudo", t, "-t", "nat", "-F"])
                TransparentProxy.run_cmd(["sudo", t, "-F", "OUTPUT"])
                TransparentProxy.run_cmd(["sudo", t, "-P", "OUTPUT", "ACCEPT"])

        if not shutil.which("iptables"): return

        # Route DNS and TCP to Tor
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
        
        print_msg("V", "Transparent proxy active.", C.GREEN)

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

    def start(self, country=None):
        if is_windows():
            path = shutil.which("tor") or "tor.exe"
            subprocess.Popen([path, "-SocksPort", str(self.socks_port), "-ControlPort", str(self.ctrl_port)], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux service management
            if shutil.which("systemctl"):
                subprocess.run(["sudo", "systemctl", "restart", "tor"], capture_output=True)
            elif shutil.which("service"):
                subprocess.run(["sudo", "service", "tor", "restart"], capture_output=True)
            else:
                bin_path = shutil.which("tor") or "/usr/bin/tor"
                subprocess.Popen(["sudo", bin_path, "--SocksPort", str(self.socks_port), "--ControlPort", str(self.ctrl_port), "--RunAsDaemon", "1"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for bootstrap
        for _ in range(20):
            if self.is_running(): return True
            time.sleep(1)
        return False

    def is_running(self):
        try:
            with socket.create_connection(("127.0.0.1", self.socks_port), timeout=1): return True
        except: return False

    def connect(self):
        if not HAS_STEM: return False
        try:
            self.controller = Controller.from_port(port=self.ctrl_port)
            self.controller.authenticate()
            return True
        except: return False

    def rotate(self):
        if not self.controller or not self.controller.is_alive():
            if not self.connect(): return False
        try:
            self.controller.signal(Signal.NEWNYM)
            return True
        except: return False

    def get_ip(self):
        for url in ["https://api.ipify.org", "https://icanhazip.com"]:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as res:
                    return res.read().decode().strip()
            except: continue
        return None

    def get_country(self, ip):
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country", timeout=3) as res:
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

    def run(self):
        clear_screen()
        print_banner()
        print_msg("*", "Initializing system...", C.CYAN)
        
        if not self.tor.start(self.country):
            print_msg("X", "Could not start Tor service.", C.RED)
            return
        
        TransparentProxy.enable(self.kill_switch)
        print_status_table(True, self.interval, self.country, self.kill_switch)
        
        while not self.stop_event.is_set():
            ip = self.tor.get_ip()
            if ip:
                country = self.tor.get_country(ip)
                print_ip_change(ip, country)
            
            if not self.tor.rotate():
                print_msg("!", "Rotation signal failed, reconnecting...", C.YELLOW)
                self.tor.connect()
            
            if self.stop_event.wait(self.interval): break
        
        self.shutdown()

    def shutdown(self):
        print_msg("*", "Cleaning up...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller: self.tor.controller.close()
        os._exit(0)

def main():
    if not is_admin():
        print(colorize("[X] ERROR: Must run as root/administrator.", C.RED, C.BOLD))
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--seconds", type=int, default=10)
    parser.add_argument("-c", "--country", type=str)
    parser.add_argument("-k", "--kill-switch", action="store_true")
    args = parser.parse_args()

    changer = IPChanger(args.seconds, args.country, args.kill_switch)
    signal.signal(signal.SIGINT, lambda s, f: changer.stop_event.set())
    changer.run()

if __name__ == "__main__":
    main()
