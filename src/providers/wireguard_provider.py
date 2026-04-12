#!/usr/bin/env python3
"""
IPCon v.1 - WireGuard Provider
"""

import asyncio
import logging
import subprocess
from typing import Optional
from pathlib import Path

from src.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger(__name__)


class WireGuardProvider(BaseProvider):
    """WireGuard protocol provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.provider_type = "wireguard"
        self._interface = config.interface or "wg0"
        self._config_file = config.config_file or f"/etc/wireguard/{self._interface}.conf"
    
    async def connect(self) -> bool:
        """Connect using WireGuard."""
        async with self._lock:
            if self._status == ProviderStatus.CONNECTED:
                logger.info(f"WireGuard {self.name} already connected")
                return True
            
            self._status = ProviderStatus.CONNECTING
            
            try:
                config_path = Path(self._config_file)
                if not config_path.exists():
                    logger.error(f"WireGuard config not found: {self._config_file}")
                    self._status = ProviderStatus.ERROR
                    return False
                
                result = await asyncio.create_subprocess_exec(
                    "wg-quick", "up", str(config_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                if result.returncode != 0:
                    stderr = await result.stderr.read()
                    logger.error(f"WireGuard error: {stderr.decode()}")
                    self._status = ProviderStatus.ERROR
                    return False
                
                self._status = ProviderStatus.CONNECTED
                self._connection_start = asyncio.get_event_loop().time()
                
                logger.info(f"WireGuard {self.name} connected")
                return True
                
            except FileNotFoundError:
                logger.error("WireGuard (wg-quick) not installed")
                self._status = ProviderStatus.ERROR
                return False
            except Exception as e:
                logger.error(f"WireGuard connection error: {e}")
                self._status = ProviderStatus.ERROR
                return False
    
    async def disconnect(self) -> bool:
        """Disconnect from WireGuard."""
        async with self._lock:
            try:
                result = await asyncio.create_subprocess_exec(
                    "wg-quick", "down", self._config_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                
                self._status = ProviderStatus.DISCONNECTED
                self._connection_start = None
                
                logger.info(f"WireGuard {self.name} disconnected")
                return True
                
            except Exception as e:
                logger.error(f"WireGuard disconnect error: {e}")
                return False
    
    async def test_connection(self) -> bool:
        """Test WireGuard connection."""
        if self._status != ProviderStatus.CONNECTED:
            return False
        
        try:
            result = await asyncio.create_subprocess_exec(
                "wg", "show", self._interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except:
            return False
