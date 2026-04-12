#!/usr/bin/env python3
"""
IPCon v.1 - OpenVPN Provider
"""

import asyncio
import logging
import subprocess
from typing import Optional
from pathlib import Path

from src.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger(__name__)


class OpenVPNProvider(BaseProvider):
    """OpenVPN protocol provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.provider_type = "openvpn"
        self._process: Optional[subprocess.Process] = None
        self._interface = config.interface or "tun0"
    
    async def connect(self) -> bool:
        """Connect using OpenVPN."""
        async with self._lock:
            if self._status == ProviderStatus.CONNECTED:
                logger.info(f"OpenVPN {self.name} already connected")
                return True
            
            self._status = ProviderStatus.CONNECTING
            
            try:
                if not self.config.config_file:
                    logger.error("No config file specified")
                    self._status = ProviderStatus.ERROR
                    return False
                
                config_path = Path(self.config.config_file)
                if not config_path.exists():
                    logger.error(f"Config file not found: {self.config.config_file}")
                    self._status = ProviderStatus.ERROR
                    return False
                
                cmd = [
                    "openvpn", "--config", str(config_path),
                    "--dev", self._interface, "--persist-tun",
                    "--nobind", "--comp-lzo", "--ping", "10", "--ping-restart", "60"
                ]
                
                self._process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await asyncio.sleep(3)
                
                self._status = ProviderStatus.CONNECTED
                self._connection_start = asyncio.get_event_loop().time()
                
                logger.info(f"OpenVPN {self.name} connected")
                return True
                
            except FileNotFoundError:
                logger.error("OpenVPN not installed")
                self._status = ProviderStatus.ERROR
                return False
            except Exception as e:
                logger.error(f"OpenVPN connection error: {e}")
                self._status = ProviderStatus.ERROR
                return False
    
    async def disconnect(self) -> bool:
        """Disconnect from OpenVPN."""
        async with self._lock:
            try:
                if self._process:
                    self._process.terminate()
                    try:
                        await asyncio.wait_for(self._process.wait(), timeout=5)
                    except asyncio.TimeoutError:
                        self._process.kill()
                        await self._process.wait()
                    
                    self._process = None
                
                self._status = ProviderStatus.DISCONNECTED
                self._connection_start = None
                
                logger.info(f"OpenVPN {self.name} disconnected")
                return True
                
            except Exception as e:
                logger.error(f"OpenVPN disconnect error: {e}")
                return False
    
    async def test_connection(self) -> bool:
        """Test OpenVPN connection."""
        if self._status != ProviderStatus.CONNECTED:
            return False
        
        try:
            result = await asyncio.create_subprocess_exec(
                "ip", "link", "show", self._interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except:
            return False
