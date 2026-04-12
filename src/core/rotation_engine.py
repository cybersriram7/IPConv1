#!/usr/bin/env python3
"""
IPCon v.1 - Rotation Engine
Core IP rotation logic with provider switching
"""

import asyncio
import logging
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class RotationState(Enum):
    IDLE = "idle"
    ROTATING = "rotating"
    SWITCHING = "switching"
    MONITORING = "monitoring"
    ERROR = "error"


@dataclass
class RotationStats:
    total_rotations: int = 0
    successful_rotations: int = 0
    failed_rotations: int = 0
    consecutive_failures: int = 0
    total_uptime: float = 0.0
    last_rotation: Optional[datetime] = None
    rotation_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def success_rate(self) -> float:
        if self.total_rotations == 0:
            return 100.0
        return (self.successful_rotations / self.total_rotations) * 100


@dataclass
class RotationConfig:
    interval: int = 60
    strategy: str = "round_robin"
    pre_connect: bool = True
    pre_connect_time: float = 5.0
    max_retries: int = 3
    retry_delay: float = 2.0
    fail_threshold: int = 3
    health_check_interval: int = 30


class RotationEngine:
    """Core rotation engine for IPCon v.1"""
    
    def __init__(self, chain_manager, ip_verifier, config, state_callback=None):
        self.chain_manager = chain_manager
        self.ip_verifier = ip_verifier
        self.config = config
        self.state_callback = state_callback
        
        self._state = RotationState.IDLE
        self._stats = RotationStats()
        self._current_provider: Optional[str] = None
        self._running = False
        self._lock = asyncio.Lock()
        self._start_time: Optional[float] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.info("Rotation engine initialized")
    
    @property
    def state(self) -> RotationState:
        return self._state
    
    @property
    def stats(self) -> RotationStats:
        return self._stats
    
    async def start(self) -> bool:
        """Start the rotation engine."""
        try:
            async with self._lock:
                if self._running:
                    logger.warning("Rotation engine already running")
                    return True
                
                logger.info("Starting rotation engine...")
                
                self._start_time = time.time()
                self._running = True
                self._state = RotationState.MONITORING
                
                initial_ip = await self.ip_verifier.get_current_ip()
                logger.info(f"Initial IP: {initial_ip}")
                
                self._health_check_task = asyncio.create_task(self._health_check_loop())
                
                logger.info("Rotation engine started")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start rotation engine: {e}")
            self._state = RotationState.ERROR
            return False
    
    async def stop(self) -> bool:
        """Stop the rotation engine."""
        try:
            async with self._lock:
                if not self._running:
                    return True
                
                logger.info("Stopping rotation engine...")
                
                self._running = False
                self._state = RotationState.IDLE
                
                if self._health_check_task:
                    self._health_check_task.cancel()
                    try:
                        await self._health_check_task
                    except asyncio.CancelledError:
                        pass
                
                if self._start_time:
                    self._stats.total_uptime += time.time() - self._start_time
                
                logger.info("Rotation engine stopped")
                return True
                
        except Exception as e:
            logger.error(f"Failed to stop rotation engine: {e}")
            return False
    
    async def rotate(self, force: bool = False) -> bool:
        """Perform IP rotation."""
        async with self._lock:
            if self._state == RotationState.ROTATING and not force:
                logger.warning("Rotation already in progress")
                return False
            
            if not self._running:
                logger.error("Rotation engine not running")
                return False
            
            self._state = RotationState.ROTATING
            rotation_start = time.time()
            
            try:
                logger.info("Starting IP rotation...")
                
                await self.chain_manager.pre_connect_next()
                
                await asyncio.sleep(self.config.pre_connect_time)
                
                success = await self.chain_manager.rotate_to_next()
                
                rotation_time = time.time() - rotation_start
                
                self._stats.total_rotations += 1
                self._stats.last_rotation = datetime.now()
                
                if success:
                    self._stats.successful_rotations += 1
                    self._stats.consecutive_failures = 0
                    
                    new_ip = await self.ip_verifier.get_current_ip()
                    logger.info(f"Rotation successful! New IP: {new_ip} (took {rotation_time:.2f}s)")
                    
                    self._state = RotationState.MONITORING
                else:
                    self._stats.failed_rotations += 1
                    self._stats.consecutive_failures += 1
                    logger.error(f"Rotation failed (took {rotation_time:.2f}s)")
                    
                    if self._stats.consecutive_failures >= self.config.fail_threshold:
                        logger.critical("Fail threshold reached, switching to error state")
                        self._state = RotationState.ERROR
                
                self._stats.rotation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "duration": rotation_time,
                    "state": self._state.value
                })
                
                return success
                
            except Exception as e:
                logger.error(f"Rotation error: {e}")
                self._stats.failed_rotations += 1
                self._state = RotationState.ERROR
                return False
    
    async def switch_provider(self, provider_name: str) -> bool:
        """Switch to a specific provider."""
        try:
            async with self._lock:
                logger.info(f"Switching to provider: {provider_name}")
                
                success = await self.chain_manager.switch_to_provider(provider_name)
                
                if success:
                    self._current_provider = provider_name
                    logger.info(f"Switched to {provider_name}")
                else:
                    logger.error(f"Failed to switch to {provider_name}")
                
                return success
                
        except Exception as e:
            logger.error(f"Provider switch error: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current engine status."""
        current_provider = await self.chain_manager.get_active_provider()
        
        return {
            "running": self._running,
            "state": self._state.value,
            "current_provider": current_provider,
            "stats": {
                "total_rotations": self._stats.total_rotations,
                "successful": self._stats.successful_rotations,
                "failed": self._stats.failed_rotations,
                "success_rate": f"{self._stats.success_rate:.1f}%",
                "consecutive_failures": self._stats.consecutive_failures,
                "last_rotation": self._stats.last_rotation.isoformat() if self._stats.last_rotation else None
            },
            "config": {
                "interval": self.config.interval,
                "strategy": self.config.strategy,
                "pre_connect": self.config.pre_connect
            }
        }
    
    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        logger.info("Starting health check loop")
        
        while self._running:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                if not self._running:
                    break
                
                is_healthy = await self._perform_health_check()
                
                if not is_healthy:
                    logger.warning("Health check failed, triggering rotation")
                    asyncio.create_task(self.rotate(force=True))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _perform_health_check(self) -> bool:
        """Perform health check on current connection."""
        try:
            ip = await self.ip_verifier.get_current_ip()
            
            if not ip:
                logger.warning("Health check: No IP detected")
                return False
            
            latency = await self.ip_verifier.measure_latency()
            
            if latency > 5000:
                logger.warning(f"Health check: High latency ({latency:.0f}ms)")
                return False
            
            logger.debug(f"Health check OK: IP={ip}, Latency={latency:.0f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
