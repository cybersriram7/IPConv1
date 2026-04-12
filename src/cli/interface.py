#!/usr/bin/env python3
"""
IPCon v.1 - CLI Interface
"""

import json
import sys
from typing import Dict, Any


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text: str, color: str) -> str:
    """Colorize text."""
    return f"{getattr(Colors, color.upper(), '')}{text}{Colors.ENDC}"


class CLI:
    """Command-line interface for IPCon v.1"""
    
    def __init__(self, app):
        self.app = app
    
    def print_status(self, status: Dict[str, Any], verbose: bool = False, json_output: bool = False) -> None:
        """Print system status."""
        if json_output:
            print(json.dumps(status, indent=2))
            return
        
        print()
        print(c("╔══════════════════════════════════════════════════════════╗", "CYAN"))
        print(c("║              IPCon v.1 - STATUS PANEL                  ║", "CYAN"))
        print(c("╚══════════════════════════════════════════════════════════╝", "CYAN"))
        print()
        
        running = status.get('running', False)
        state = status.get('state', 'unknown')
        provider = status.get('current_provider', 'None')
        ip = status.get('current_ip', 'Unknown')
        
        status_color = "GREEN" if running else "RED"
        
        print(c("┌─────────────────────────────────────────────────────────┐", "CYAN"))
        print(c("│", "CYAN") + f"  Status:     {c(state.upper(), status_color):<40}" + c("│", "CYAN"))
        print(c("│", "CYAN") + f"  Provider:   {c(provider or 'None', 'WHITE'):<40}" + c("│", "CYAN"))
        print(c("│", "CYAN") + f"  Current IP: {c(ip, 'GREEN'):<40}" + c("│", "CYAN"))
        print(c("└─────────────────────────────────────────────────────────┘", "CYAN"))
        print()
        
        print(c("┌─────────────────────────────────────────────────────────┐", "CYAN"))
        print(c("│                    SECURITY FEATURES                       │", "CYAN"))
        print(c("├─────────────────────────────────────────────────────────┤", "CYAN"))
        
        ks = "Enabled" if status.get('kill_switch_active') else "Disabled"
        dns = "Enabled" if status.get('dns_protection_active') else "Disabled"
        ks_color = "GREEN" if status.get('kill_switch_active') else "RED"
        dns_color = "GREEN" if status.get('dns_protection_active') else "RED"
        
        print(c("│", "CYAN") + f"  Kill Switch:  {c(ks, ks_color):<40}" + c("│", "CYAN"))
        print(c("│", "CYAN") + f"  DNS Protection: {c(dns, dns_color):<40}" + c("│", "CYAN"))
        print(c("└─────────────────────────────────────────────────────────┘", "CYAN"))
        
        if "stats" in status:
            print()
            print(c("┌─────────────────────────────────────────────────────────┐", "CYAN"))
            print(c("│                     STATISTICS                           │", "CYAN"))
            print(c("├─────────────────────────────────────────────────────────┤", "CYAN"))
            
            stats = status["stats"]
            total = stats.get('total_rotations', 0)
            success = stats.get('successful', 0)
            failed = stats.get('failed', 0)
            rate = stats.get('success_rate', '0%')
            
            print(c("│", "CYAN") + f"  Total Rotations: {total:<37}" + c("│", "CYAN"))
            print(c("│", "CYAN") + f"  Successful:     {c(str(success), 'GREEN'):<40}" + c("│", "CYAN"))
            print(c("│", "CYAN") + f"  Failed:          {c(str(failed), 'RED'):<40}" + c("│", "CYAN"))
            print(c("│", "CYAN") + f"  Success Rate:   {c(rate, 'GREEN'):<40}" + c("│", "CYAN"))
            print(c("└─────────────────────────────────────────────────────────┘", "CYAN"))
        
        print()
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        print(c(f"[✗] {message}", "RED"), file=sys.stderr)
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        print(c(f"[!] {message}", "YELLOW"))
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        print(c(f"[✓] {message}", "GREEN"))
    
    def print_info(self, message: str) -> None:
        """Print info message."""
        print(c(f"[*] {message}", "CYAN"))
