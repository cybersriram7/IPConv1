#!/usr/bin/env python3
"""
IPCon v.1 - HTTP Proxy Provider
"""

import asyncio
import logging
import base64
from typing import Optional

from src.providers.base_provider import BaseProvider, ProviderConfig, ProviderStatus

logger = logging.getLogger(__name__)


class HTTPProxyProvider(BaseProvider):
    """HTTP/HTTPS proxy provider."""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.provider_type = "https" if config.type == "https" else "http"
        self._host = config.host
        self._port = config.port or (443 if self.provider_type == "https" else 8080)
        self._use_ssl = self.provider_type == "https"
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> bool:
        """Connect to HTTP/HTTPS proxy."""
        async with self._lock:
            if self._status == ProviderStatus.CONNECTED:
                logger.info(f"HTTP Proxy {self.name} already connected")
                return True
            
            self._status = ProviderStatus.CONNECTING
            
            try:
                if self._use_ssl:
                    import ssl
                    ctx = ssl.create_default_context()
                    self._reader, self._writer = await asyncio.wait_for(
                        asyncio.open_connection(self._host, self._port, ssl=ctx),
                        timeout=10
                    )
                else:
                    self._reader, self._writer = await asyncio.wait_for(
                        asyncio.open_connection(self._host, self._port),
                        timeout=10
                    )
                
                self._status = ProviderStatus.CONNECTED
                self._connection_start = asyncio.get_event_loop().time()
                
                logger.info(f"HTTP Proxy {self.name} connected ({self._host}:{self._port})")
                return True
                
            except asyncio.TimeoutError:
                logger.error("HTTP Proxy connection timeout")
                self._status = ProviderStatus.ERROR
                return False
            except Exception as e:
                logger.error(f"HTTP Proxy connection error: {e}")
                self._status = ProviderStatus.ERROR
                return False
    
    async def disconnect(self) -> bool:
        """Disconnect from HTTP proxy."""
        async with self._lock:
            if self._writer:
                try:
                    self._writer.close()
                    await self._writer.wait_closed()
                except:
                    pass
                self._writer = None
                self._reader = None
            
            self._status = ProviderStatus.DISCONNECTED
            self._connection_start = None
            logger.info(f"HTTP Proxy {self.name} disconnected")
            return True
    
    async def test_connection(self) -> bool:
        """Test HTTP proxy connection."""
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
