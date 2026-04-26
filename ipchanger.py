#!/usr/bin/env python3
"""
IP Changer - Professional Tor-Based IP Rotation Tool
ULTIMATE EDITION - Minimalist UI, Maximum Performance.
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

# Set global timeout for socket operations
socket.setdefaulttimeout(10)

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
 ██╗██████╗  ██████╗ ██████╗ ███╗   ██╗██╗   ██╗ ██╗
 ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║██║   ██║███║
 ██║██████╔╝██║     ██║   ██║██╔██╗ ██║██║   ██║╚██║
 ██║██╔═══╝ ██║     ██║   ██║██║╚██╗██║╚██╗ ██╔╝ ██║
 ██║██║     ╚██████╗╚██████╔╝██║ ╚████║ ╚████╔╝  ██║
 ╚═╝╚═╝      ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝  ╚═══╝   ╚═╝"""

def print_banner():
    print(colorize(BANNER, C.CYAN, C.BOLD))
    print(colorize("                                     [ DEVELOPED BY SRIRAM ]", C.MAGENTA, C.BOLD))
    print(colorize("-" * 65, C.GRAY))

def print_status_table(tor_status, interval, country=None, kill_switch=False):
    border = colorize("+-------------------------+----------------------------------------+", C.CYAN)
    print(border)
    print(colorize("|", C.CYAN) + colorize(" Service                 ", C.WHITE, C.BOLD) + colorize("|", C.CYAN) + colorize(" Information                            ", C.WHITE, C.BOLD) + colorize("|", C.CYAN))
    print(border)
    
    status_text = colorize("Tor engine active", C.GREEN) if tor_status else colorize("Tor engine failed", C.RED)
    print(f"{colorize('|', C.CYAN)} Engine Status           {colorize('|', C.CYAN)} {status_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    rot_text = colorize(f"Rotation: Every {interval}s", C.YELLOW)
    print(f"{colorize('|', C.CYAN)} IP Rotation             {colorize('|', C.CYAN)} {rot_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    region = f"Region: {country.upper()}" if country else "Region: All (Global)"
    reg_text = colorize(region, C.CYAN)
    print(f"{colorize('|', C.CYAN)} Target Region           {colorize('|', C.CYAN)} {reg_text.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    ks_val = colorize("ACTIVE (MAX FORCE)", C.GREEN, C.BOLD) if kill_switch else colorize("DISABLED", C.GRAY)
    print(f"{colorize('|', C.CYAN)} Kill Switch             {colorize('|', C.CYAN)} {ks_val.ljust(39+9)} {colorize('|', C.CYAN)}")
    
    print(f"{colorize('|', C.CYAN)} Control                 {colorize('|', C.CYAN)} {colorize('Press CTRL+C to Terminate', C.RED).ljust(39+9)} {colorize('|', C.CYAN)}")
    print(border)

def print_ip_change(ip, country=None, latency=None):
    now = datetime.now().strftime("%I:%M:%S %p")
    c_info = f" ({country})" if country else ""
    l_info = colorize(f" [{latency:.2f}s]", C.GRAY) if latency else ""
    print(f"{colorize(f'[{now}]', C.GRAY)} {colorize('Public IP -> ', C.WHITE)}{colorize(ip, C.GREEN, C.BOLD)}{colorize(c_info, C.YELLOW)}{l_info}")

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
                    tor_path = shutil.which("tor") or "tor.exe"
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Tor", "dir=out", "action=allow", f"program={tor_path}", "enable=yes"])
                    TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_KS", "dir=out", "action=block", "enable=yes"])
                TransparentProxy.run_cmd(["powershell", "-Command", "Disable-NetAdapterBinding -Name '*' -ComponentID ms_tcpip6"], silent=True)
            except: pass
            return

        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"])
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"])

        tor_users = ["debian-tor", "tor", "tor-socks", "tor-annex"]
        actual_tor_user = None
        for u in tor_users:
            try:
                import pwd
                pwd.getpwnam(u)
                actual_tor_user = u
                break
            except: continue
        
        if not actual_tor_user: actual_tor_user = "debian-tor"

        cmds = [
            ["sudo", "iptables", "-t", "nat", "-F"],
            ["sudo", "iptables", "-F", "OUTPUT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-o", "lo", "-j", "RETURN"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "192.168.0.0/16", "-j", "ACCEPT"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "192.168.0.0/16", "-j", "RETURN"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "10.0.0.0/8", "-j", "ACCEPT"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "10.0.0.0/8", "-j", "RETURN"],
            ["sudo", "iptables", "-A", "OUTPUT", "-d", "172.16.0.0/12", "-j", "ACCEPT"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-d", "172.16.0.0/12", "-j", "RETURN"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-m", "owner", "--uid-owner", actual_tor_user, "-j", "RETURN"],
            ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", actual_tor_user, "-j", "ACCEPT"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "REDIRECT", "--to-ports", "9053"],
            ["sudo", "iptables", "-t", "nat", "-A", "OUTPUT", "-p", "tcp", "-j", "REDIRECT", "--to-ports", "9040"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9040", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "9053", "-j", "ACCEPT"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "udp", "-j", "DROP"],
            ["sudo", "iptables", "-A", "OUTPUT", "-p", "icmp", "-j", "DROP"],
            ["sudo", "iptables", "-P", "OUTPUT", "DROP"]
        ]
        
        for cmd in cmds: TransparentProxy.run_cmd(cmd)
        if shutil.which("ip6tables"): TransparentProxy.run_cmd(["sudo", "ip6tables", "-P", "OUTPUT", "DROP"])

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
                TransparentProxy.run_cmd(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Tor"])
                TransparentProxy.run_cmd(["powershell", "-Command", "Enable-NetAdapterBinding -Name '*' -ComponentID ms_tcpip6"], silent=True)
                # Flush Windows DNS cache
                TransparentProxy.run_cmd(["ipconfig", "/flushdns"])
            except: pass
            return

        # Flush all iptables rules first
        for t in ["iptables", "ip6tables"]:
            if shutil.which(t):
                TransparentProxy.run_cmd(["sudo", t, "-t", "nat", "-F"])
                TransparentProxy.run_cmd(["sudo", t, "-F", "OUTPUT"])
                TransparentProxy.run_cmd(["sudo", t, "-P", "OUTPUT", "ACCEPT"])

        # Re-enable IPv6
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"])
        TransparentProxy.run_cmd(["sudo", "sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=0"])

        # Restart NetworkManager to restore original DNS and IP
        if shutil.which("systemctl"):
            TransparentProxy.run_cmd(["sudo", "systemctl", "restart", "NetworkManager"])
        elif shutil.which("service"):
            TransparentProxy.run_cmd(["sudo", "service", "network-manager", "restart"])

        # Flush DNS cache
        if shutil.which("resolvectl"):
            TransparentProxy.run_cmd(["sudo", "resolvectl", "flush-caches"])
        elif shutil.which("systemd-resolve"):
            TransparentProxy.run_cmd(["sudo", "systemd-resolve", "--flush-caches"])

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
                subprocess.run(["sudo", "systemctl", "restart", "tor@default"], capture_output=True)
            else:
                bin_path = shutil.which("tor") or "/usr/bin/tor"
                subprocess.Popen(["sudo", bin_path, "--SocksPort", str(self.socks_port), "--ControlPort", str(self.ctrl_port), "--RunAsDaemon", "1"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Completely Silent Bootstrap
        for i in range(120):
            if self.is_running():
                phase = self.get_bootstrap_phase()
                if "PROGRESS=100" in phase:
                    if country: self.apply_country_config(country)
                    return True
            time.sleep(1)
        return False

    def get_bootstrap_phase(self):
        if not self.connect(): return "PROGRESS=0"
        try:
            return self.controller.get_info("status/bootstrap-phase")
        except: return "PROGRESS=0"

    def apply_country_config(self, country):
        if not self.connect(): return False
        try:
            self.controller.set_conf("ExitNodes", f"{{{country}}}")
            self.controller.set_conf("StrictNodes", "1")
            return True
        except: return False

    def is_running(self):
        try:
            with socket.create_connection(("127.0.0.1", self.socks_port), timeout=2): return True
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
        urls = ["https://icanhazip.com", "https://api.ipify.org", "https://ifconfig.me/ip"]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as res:
                    return res.read().decode().strip()
            except: continue
        return None

    def get_country(self, ip):
        if not ip: return None
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country", timeout=3) as res:
                return json.loads(res.read().decode()).get('country')
        except: return None

# -----------------------------------------------------------------------
# IPChanger Core
# -----------------------------------------------------------------------

class IPChanger:
    def __init__(self, interval, country, kill_switch):
        self.interval = interval
        self.country = country
        self.kill_switch = kill_switch
        self.tor = TorManager()
        self.stop_event = threading.Event()

    def check_leaks(self):
        try:
            with urllib.request.urlopen("https://check.torproject.org/api/ip", timeout=10) as res:
                return json.loads(res.read().decode()).get("IsTor", False)
        except: return False

    def run(self):
        clear_screen()
        print_banner()
        
        # Silent Startup
        if not self.tor.start(self.country):
            print_msg("X", "Failed to connect to Tor.", C.RED)
            return
        
        TransparentProxy.enable(True)
        
        # Only verify and then print table immediately
        if not self.check_leaks():
            print_msg("X", "Leak detected! Connection aborted.", C.RED)
            self.shutdown()
            return

        print_status_table(True, self.interval, self.country, True)
        
        try:
            while not self.stop_event.is_set():
                start_time = time.time()
                
                if self.interval > 5:
                    threading.Timer(self.interval - 2, self.tor.rotate).start()
                else:
                    self.tor.rotate()

                ip = self.tor.get_ip()
                latency = time.time() - start_time
                
                if ip:
                    country = self.tor.get_country(ip)
                    print_ip_change(ip, country, latency)
                
                if self.stop_event.wait(self.interval): break
        except KeyboardInterrupt: pass
        finally: self.shutdown()

    def shutdown(self):
        print_msg("*", "Restoring original network...", C.MAGENTA)
        TransparentProxy.disable()
        if self.tor.controller: self.tor.controller.close()
        # Give NetworkManager a moment to reconnect
        time.sleep(2)
        # Show the restored real IP
        try:
            req = urllib.request.Request("https://icanhazip.com", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as res:
                real_ip = res.read().decode().strip()
                print_msg("V", f"Original IP restored -> {real_ip}", C.GREEN)
        except:
            print_msg("V", "Network restored to default.", C.GREEN)
        os._exit(0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="run")
    parser.add_argument("-s", "--seconds", type=int, default=10)
    parser.add_argument("-c", "--country", type=str)
    parser.add_argument("-k", "--kill-switch", action="store_true")
    args = parser.parse_args()

    if args.command == "stop":
        TransparentProxy.disable()
        if is_windows(): os.system("taskkill /IM tor.exe /F >nul 2>&1")
        else: os.system("sudo systemctl stop tor@default >/dev/null 2>&1; sudo pkill -9 tor >/dev/null 2>&1")
        time.sleep(2)
        try:
            req = urllib.request.Request("https://icanhazip.com", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as res:
                real_ip = res.read().decode().strip()
                print(colorize(f"[V] Original IP restored -> {real_ip}", C.GREEN))
        except:
            print(colorize("[V] Network restored to default.", C.GREEN))
        sys.exit(0)

    if not is_admin():
        print(colorize("[X] Error: Run as root/administrator.", C.RED))
        sys.exit(1)

    changer = IPChanger(args.seconds, args.country, args.kill_switch)
    signal.signal(signal.SIGINT, lambda s, f: changer.stop_event.set())
    changer.run()

if __name__ == "__main__":
    main()
