#!/usr/bin/env python3
"""
IPCon v.1 - IP Verifier
"""

import asyncio
import logging
import time
import urllib.request
import json
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class IPVerifier:
    """Public IP detection and verification"""
    
    IP_SERVICES = [
        "https://api.ipify.org",
    ]
    
    def __init__(self):
        self._current_ip: Optional[str] = None
        self._ip_history: list = []
        self._last_check: Optional[float] = None
    
    async def get_current_ip(self) -> Optional[str]:
        """Get current public IP address."""
        try:
            for url in self.IP_SERVICES:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
                    response = urllib.request.urlopen(req, timeout=5)
                    content = response.read().decode().strip()
                    try:
                        data = json.loads(content)
                        ip = data.get('ip') or data.get('address') or str(data)
                    except json.JSONDecodeError:
                        ip = content
                    
                    if ip and self._is_valid_ip(ip):
                        if ip != self._current_ip:
                            self._current_ip = ip
                            self._ip_history.append({
                                "ip": ip,
                                "timestamp": time.time()
                            })
                            logger.info(f"IP changed: {ip}")
                        
                        self._last_check = time.time()
                        return ip
                        
                except Exception:
                    continue
            
            return self._current_ip
            
        except Exception as e:
            logger.error(f"Failed to get IP: {e}")
            return self._current_ip
    
    async def measure_latency(self) -> float:
        """Measure latency to IP verification services."""
        start = time.time()
        
        try:
            req = urllib.request.Request(
                "https://api.ipify.org",
                headers={"User-Agent": "IPCon/1.0"}
            )
            urllib.request.urlopen(req, timeout=5)
            return (time.time() - start) * 1000
        except:
            return 9999.0
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def get_history(self) -> list:
        """Get IP change history."""
        return self._ip_history.copy()
