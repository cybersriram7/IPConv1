#!/usr/bin/env python3
"""
IPCon v.1 - SOCKS5 Provider
"""

import asyncio
import logging
import socket
import struct
from typing import Optional

from src.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger(__name__)


class SOCKS5Provider(BaseProvider):
    """SOCKS5 proxy provider."""
    
    SOCKS_VERSION = 0x05
    AUTH_NO_AUTH = 0x00
    AUTH_PASSWORD = 0x02
    CMD_CONNECT = 0x01
    ATYP_DOMAIN = 0x03
    REP_SUCCESS = 0x00
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.provider_type = "socks5"
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._host = config.host
        self._port = config.port or 1080
    
    async def connect(self) -> bool:
        """Connect to SOCKS5 proxy."""
        async with self._lock:
            if self._status == ProviderStatus.CONNECTED:
                logger.info(f"SOCKS5 {self.name} already connected")
                return True
            
            self._status = ProviderStatus.CONNECTING
            
            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self._host, self._port),
                    timeout=10
                )
                
                greeting = bytes([self.SOCKS_VERSION, 0x02, self.AUTH_NO_AUTH, self.AUTH_PASSWORD])
                self._writer.write(greeting)
                await self._writer.drain()
                
                response = await self._reader.read(2)
                if len(response) < 2 or response[0] != self.SOCKS_VERSION:
                    logger.error("SOCKS5 greeting failed")
                    await self._cleanup()
                    self._status = ProviderStatus.ERROR
                    return False
                
                self._status = ProviderStatus.CONNECTED
                self._connection_start = asyncio.get_event_loop().time()
                
                logger.info(f"SOCKS5 {self.name} connected ({self._host}:{self._port})")
                return True
                
            except asyncio.TimeoutError:
                logger.error("SOCKS5 connection timeout")
                self._status = ProviderStatus.ERROR
                return False
            except Exception as e:
                logger.error(f"SOCKS5 connection error: {e}")
                self._status = ProviderStatus.ERROR
                return False
    
    async def disconnect(self) -> bool:
        """Disconnect from SOCKS5 proxy."""
        async with self._lock:
            await self._cleanup()
            self._status = ProviderStatus.DISCONNECTED
            self._connection_start = None
            logger.info(f"SOCKS5 {self.name} disconnected")
            return True
    
    async def _cleanup(self) -> None:
        """Clean up connection."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except:
                pass
            self._writer = None
            self._reader = None
    
    async def test_connection(self) -> bool:
        """Test SOCKS5 proxy connection."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=5
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
