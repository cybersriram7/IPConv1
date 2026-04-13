#!/usr/bin/env python3
"""
IPCon v.1 - Tor Provider
"""

import asyncio
import logging
import socket
import stem.process
import stem.control
from typing import Optional
import os
import time
import platform

from src.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger(__name__)


class TorProvider(BaseProvider):
    """Tor anonymity network provider."""
    
    DEFAULT_CONTROL_PORT = 9051
    DEFAULT_SOCKS_PORT = 9050
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.provider_type = "tor"
        self._control_port = getattr(config, 'port', None) or self.DEFAULT_CONTROL_PORT
        self._socks_port = getattr(config, 'socks_port', self.DEFAULT_SOCKS_PORT)
        self._tor_process = None
        self._controller = None
        self._tor_path = "tor" if platform.system() == "Windows" else "/usr/bin/tor"
    
    async def connect(self) -> bool:
        """Start Tor and establish connection."""
        async with self._lock:
            if self._status == ProviderStatus.CONNECTED:
                logger.info(f"Tor {self.name} already connected")
                return True
            
            self._status = ProviderStatus.CONNECTING
            
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._start_tor
                )
                
                for _ in range(30):
                    if await asyncio.get_event_loop().run_in_executor(
                        None, self._is_tor_connected
                    ):
                        break
                    await asyncio.sleep(1)
                
                self._status = ProviderStatus.CONNECTED
                self._connection_start = asyncio.get_event_loop().time()
                logger.info(f"Tor {self.name} connected")
                return True
                
            except Exception as e:
                logger.error(f"Tor connection error: {e}")
                self._status = ProviderStatus.ERROR
                return False
    
    def _start_tor(self):
        """Start Tor process."""
        try:
            self._tor_process = stem.process.launch_tor_with_config(
                config={
                    'ControlPort': str(self._control_port),
                    'SocksPort': str(self._socks_port),
                    'DataDirectory': 'tor_data' if platform.system() == "Windows" else '/tmp/ipcon_tor',
                    'CookieAuthentication': '1',
                    'StrictNodes': '1',
                },
                tor_cmd=self._tor_path,
                timeout=30,
                take_ownership=True
            )
        except Exception as e:
            logger.warning(f"Tor process start: {e}")
    
    def _is_tor_connected(self) -> bool:
        """Check if Tor is connected."""
        try:
            self._controller = stem.control.Controller.from_port(
                port=self._control_port
            )
            self._controller.close()
            return True
        except:
            return False
    
    async def disconnect(self) -> bool:
        """Stop Tor connection."""
        async with self._lock:
            try:
                if self._controller:
                    self._controller.close()
                    self._controller = None
                
                if self._tor_process:
                    self._tor_process.terminate()
                    self._tor_process = None
                
                self._status = ProviderStatus.DISCONNECTED
                self._connection_start = None
                logger.info(f"Tor {self.name} disconnected")
                return True
            except Exception as e:
                logger.error(f"Tor disconnect error: {e}")
                return False
    
    async def renew_connection(self) -> bool:
        """Request new Tor circuit (new IP)."""
        async with self._lock:
            try:
                if not self._controller:
                    self._controller = stem.control.Controller.from_port(
                        port=self._control_port
                    )
                
                self._controller.signal(stem.Signal.NEWNYM)
                logger.info(f"Tor {self.name}: New IP requested")
                await asyncio.sleep(2)
                return True
            except Exception as e:
                logger.error(f"Tor renew error: {e}")
                return False
    
    async def test_connection(self) -> bool:
        """Test Tor connection."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._is_tor_connected
        )
    
    def get_socks_url(self) -> str:
        """Get SOCKS proxy URL."""
        return f"socks5://127.0.0.1:{self._socks_port}"
