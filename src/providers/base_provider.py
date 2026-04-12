#!/usr/bin/env python3
"""
IPCon v.1 - Base Provider
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class ProviderConfig:
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config_file: Optional[str] = None
    interface: Optional[str] = None
    dns: Optional[str] = None
    mtu: int = 1400
    priority: int = 1
    enabled: bool = True
    socks_port: Optional[int] = None
    auto_renew: bool = False
    renew_interval: int = 30


class BaseProvider(ABC):
    """Abstract base class for all provider implementations."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._status = ProviderStatus.DISCONNECTED
        self._latency: float = 0.0
        self._connection_start: Optional[float] = None
        self._lock = asyncio.Lock()
        
        self.provider_type = config.type
        self.name = config.name
    
    @property
    def status(self) -> ProviderStatus:
        return self._status
    
    @property
    def latency(self) -> float:
        return self._latency
    
    @property
    def is_connected(self) -> bool:
        return self._status == ProviderStatus.CONNECTED
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the provider."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the provider."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider is reachable."""
        pass
    
    async def reconnect(self) -> bool:
        """Reconnect to the provider."""
        await self.disconnect()
        await asyncio.sleep(1)
        return await self.connect()
    
    async def measure_latency(self) -> float:
        """Measure connection latency to provider."""
        import time
        start = time.time()
        
        if await self.test_connection():
            return (time.time() - start) * 1000
        
        return 9999.0
    
    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": self.name,
            "type": self.provider_type,
            "status": self._status.value,
            "latency": self._latency,
            "connected": self.is_connected
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, status={self._status.value})>"
