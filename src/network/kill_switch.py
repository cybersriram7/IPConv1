#!/usr/bin/env python3
"""
IPCon v.1 - Kill Switch
"""

import asyncio
import logging
import subprocess
import platform
from typing import List

logger = logging.getLogger(__name__)


class KillSwitch:
    """iptables-based traffic blocking on VPN disconnect"""
    
    def __init__(self, vpn_interface: str = "tun+"):
        self.vpn_interface = vpn_interface
        self._enabled = False
        self._whitelisted_ips: List[str] = []
        self._lock = asyncio.Lock()
    
    async def enable(self) -> bool:
        """Enable the kill switch."""
        async with self._lock:
            if self._enabled:
                logger.info("Kill switch already enabled")
                return True
            
            try:
                if platform.system() == "Windows":
                    # For Windows, we'll use a different approach:
                    # 1. Block all outbound traffic
                    # 2. Allow localhost (for Tor control and SOCKS)
                    logger.info("Enabling Windows Kill Switch (via netsh)...")
                    
                    cmds = [
                        ["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Block_All", "dir=out", "action=block"],
                        ["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Allow_Local", "dir=out", "action=allow", "remoteip=127.0.0.1"]
                    ]
                    
                    for cmd in cmds:
                        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    self._enabled = True
                    logger.info("Windows Kill Switch enabled - Non-local traffic blocked")
                    return True

                logger.info("Enabling kill switch...")
                
                rules = [
                    ("iptables", "-F"), ("iptables", "-X"),
                    ("iptables", "-P", "INPUT", "DROP"),
                    ("iptables", "-P", "FORWARD", "DROP"),
                    ("iptables", "-P", "OUTPUT", "DROP"),
                ]
                
                for rule in rules:
                    await asyncio.create_subprocess_exec(
                        *rule, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                
                allow_rules = [
                    ("iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"),
                    ("iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"),
                    ("iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"),
                    ("iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"),
                    ("iptables", "-A", "INPUT", "-i", self.vpn_interface, "-j", "ACCEPT"),
                    ("iptables", "-A", "OUTPUT", "-o", self.vpn_interface, "-j", "ACCEPT"),
                ]
                
                for rule in allow_rules:
                    await asyncio.create_subprocess_exec(
                        *rule, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                
                self._enabled = True
                logger.info("Kill switch enabled - All non-VPN traffic blocked")
                return True
                
            except Exception as e:
                logger.error(f"Failed to enable kill switch: {e}")
                return False
    
    async def disable(self) -> bool:
        """Disable the kill switch."""
        async with self._lock:
            if not self._enabled:
                return True
            
            try:
                if platform.system() == "Windows":
                    logger.info("Disabling Windows Kill Switch...")
                    subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Block_All"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["netsh", "advfirewall", "firewall", "delete", "rule", "name=IPConv_Allow_Local"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self._enabled = False
                    return True

                logger.info("Disabling kill switch...")
                
                rules = [
                    ("iptables", "-F"), ("iptables", "-X"),
                    ("iptables", "-P", "INPUT", "ACCEPT"),
                    ("iptables", "-P", "FORWARD", "ACCEPT"),
                    ("iptables", "-P", "OUTPUT", "ACCEPT"),
                ]
                
                for rule in rules:
                    await asyncio.create_subprocess_exec(
                        *rule, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                
                self._enabled = False
                logger.info("Kill switch disabled - Normal traffic restored")
                return True
                
            except Exception as e:
                logger.error(f"Failed to disable kill switch: {e}")
                return False
    
    async def is_enabled(self) -> bool:
        """Check if kill switch is enabled."""
        return self._enabled
    
    async def emergency_kill(self) -> bool:
        """Emergency block of all traffic."""
        try:
            logger.critical("EMERGENCY KILL - Blocking all traffic!")
            
            if platform.system() == "Windows":
                subprocess.run(["netsh", "advfirewall", "firewall", "add", "rule", "name=IPConv_Emergency_Block", "dir=out", "action=block"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                rules = [
                    ("iptables", "-F"), ("iptables", "-X"),
                    ("iptables", "-P", "INPUT", "DROP"),
                    ("iptables", "-P", "FORWARD", "DROP"),
                    ("iptables", "-P", "OUTPUT", "DROP"),
                ]
                
                for rule in rules:
                    await asyncio.create_subprocess_exec(
                        *rule, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
            
            self._enabled = True
            logger.critical("All traffic blocked!")
            return True
            
        except Exception as e:
            logger.error(f"Emergency kill failed: {e}")
            return False
