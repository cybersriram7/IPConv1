#!/usr/bin/env python3
"""
IPCon v.1 - Chain Manager
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from src.providers.base_provider import BaseProvider, ProviderStatus

logger = logging.getLogger(__name__)


class ChainState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SWITCHING = "switching"
    ERROR = "error"


class ChainManager:
    """Manages provider chains for multi-hop routing"""
    
    def __init__(self, config):
        self.config = config
        self._chains: Dict[str, List] = {}
        self._active_chain: Optional[str] = None
        self._active_provider_index: int = 0
        self._state = ChainState.DISCONNECTED
        self._lock = asyncio.Lock()
        self._providers: Dict[str, BaseProvider] = {}
        self._preconnected_provider: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize the chain manager."""
        try:
            logger.info("Initializing chain manager...")
            
            await self._load_providers()
            
            if self._providers:
                first_provider = list(self._providers.keys())[0]
                await self.connect_provider(first_provider)
            
            logger.info(f"Chain manager initialized with {len(self._providers)} providers")
            return True
            
        except Exception as e:
            logger.error(f"Chain manager initialization failed: {e}")
            return False
    
    async def _load_providers(self) -> None:
        """Load providers from configuration."""
        for provider_config in self.config.providers:
            try:
                provider = await self._create_provider(provider_config)
                if provider:
                    self._providers[provider_config.name] = provider
                    logger.info(f"Loaded provider: {provider_config.name}")
            except Exception as e:
                logger.error(f"Failed to load provider {provider_config.name}: {e}")
    
    async def _create_provider(self, config) -> Optional[BaseProvider]:
        """Create a provider instance based on config."""
        from src.providers.openvpn_provider import OpenVPNProvider
        from src.providers.wireguard_provider import WireGuardProvider
        from src.providers.socks5_provider import SOCKS5Provider
        from src.providers.http_proxy_provider import HTTPProxyProvider
        from src.providers.tor_provider import TorProvider
        
        provider_type = config.type.lower()
        
        if provider_type == "openvpn":
            return OpenVPNProvider(config)
        elif provider_type == "wireguard":
            return WireGuardProvider(config)
        elif provider_type == "socks5":
            return SOCKS5Provider(config)
        elif provider_type in ("http", "https"):
            return HTTPProxyProvider(config)
        elif provider_type == "tor":
            return TorProvider(config)
        else:
            logger.warning(f"Unknown provider type: {provider_type}")
            return None
    
    async def connect_provider(self, name: str) -> bool:
        """Connect to a specific provider."""
        async with self._lock:
            if name not in self._providers:
                logger.error(f"Provider not found: {name}")
                return False
            
            provider = self._providers[name]
            
            try:
                self._state = ChainState.CONNECTING
                logger.info(f"Connecting to provider: {name}")
                
                success = await provider.connect()
                
                if success:
                    self._active_chain = name
                    self._active_provider_index = 0
                    self._state = ChainState.CONNECTED
                    logger.info(f"Connected to {name}")
                    return True
                else:
                    self._state = ChainState.ERROR
                    logger.error(f"Failed to connect to {name}")
                    return False
                    
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self._state = ChainState.ERROR
                return False
    
    async def disconnect_provider(self, name: str) -> bool:
        """Disconnect from a provider."""
        if name not in self._providers:
            return False
        
        provider = self._providers[name]
        
        try:
            await provider.disconnect()
            
            if self._active_chain == name:
                self._active_chain = None
                self._state = ChainState.DISCONNECTED
            
            logger.info(f"Disconnected from {name}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    async def switch_to_provider(self, name: str) -> bool:
        """Switch to a different provider."""
        async with self._lock:
            if self._active_chain == name:
                logger.info(f"Already connected to {name}")
                return True
            
            self._state = ChainState.SWITCHING
            
            old_provider = self._active_chain
            
            if await self.connect_provider(name):
                if old_provider:
                    await self.disconnect_provider(old_provider)
                return True
            
            return False
    
    async def rotate_to_next(self) -> bool:
        """Rotate to the next available provider."""
        async with self._lock:
            if not self._providers:
                logger.error("No providers available")
                return False
            
            provider_names = list(self._providers.keys())
            
            if len(provider_names) == 1:
                logger.warning("Only one provider available, reconnecting")
                return await self.connect_provider(provider_names[0])
            
            current_index = provider_names.index(self._active_chain) if self._active_chain in provider_names else -1
            next_index = (current_index + 1) % len(provider_names)
            next_provider = provider_names[next_index]
            
            logger.info(f"Rotating from {self._active_chain} to {next_provider}")
            
            return await self.switch_to_provider(next_provider)
    
    async def pre_connect_next(self) -> bool:
        """Pre-connect to the next provider for seamless switching."""
        if not self.config.rotation.pre_connect:
            return True
        
        provider_names = list(self._providers.keys())
        if len(provider_names) <= 1:
            return True
        
        current_index = provider_names.index(self._active_chain) if self._active_chain in provider_names else -1
        next_index = (current_index + 1) % len(provider_names)
        next_provider = provider_names[next_index]
        
        logger.debug(f"Pre-connecting to {next_provider}")
        
        try:
            asyncio.create_task(self._providers[next_provider].connect())
            self._preconnected_provider = next_provider
            return True
        except Exception as e:
            logger.warning(f"Pre-connect failed: {e}")
            return False
    
    async def get_active_provider(self) -> Optional[str]:
        """Get the currently active provider name."""
        return self._active_chain
    
    async def get_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all providers."""
        result = {}
        
        for name, provider in self._providers.items():
            result[name] = {
                "type": provider.provider_type,
                "status": provider.status.value,
                "is_active": name == self._active_chain,
                "latency": provider.latency if hasattr(provider, 'latency') else None
            }
        
        return result
    
    async def disconnect_all(self) -> None:
        """Disconnect from all providers."""
        for name in list(self._providers.keys()):
            await self.disconnect_provider(name)
    
    async def set_active_provider(self, name: str) -> bool:
        """Set active provider."""
        return await self.connect_provider(name)
