#!/usr/bin/env python3
"""
IPCon v.1 - Scheduler
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class Scheduler:
    """Handles automatic rotation timing"""
    
    def __init__(self, rotation_engine):
        self.rotation_engine = rotation_engine
        self._interval: int = 60
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._paused: bool = False
    
    @property
    def interval(self) -> int:
        return self._interval
    
    async def start(self) -> bool:
        """Start the scheduler."""
        async with self._lock:
            if self._running:
                logger.warning("Scheduler already running")
                return True
            
            logger.info(f"Starting scheduler with interval: {self._interval}s")
            
            self._running = True
            self._paused = False
            self._task = asyncio.create_task(self._run())
            
            return True
    
    async def stop(self) -> bool:
        """Stop the scheduler."""
        async with self._lock:
            if not self._running:
                return True
            
            logger.info("Stopping scheduler...")
            
            self._running = False
            
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            
            return True
    
    async def pause(self) -> bool:
        """Pause the scheduler."""
        logger.info("Scheduler paused")
        self._paused = True
        return True
    
    async def resume(self) -> bool:
        """Resume the scheduler."""
        logger.info("Scheduler resumed")
        self._paused = False
        return True
    
    async def set_interval(self, seconds: int) -> bool:
        """Set rotation interval."""
        if seconds < 1:
            logger.error("Interval must be at least 1 second")
            return False
        
        old_interval = self._interval
        self._interval = seconds
        logger.info(f"Interval changed: {old_interval}s -> {self._interval}s")
        return True
    
    async def trigger_now(self) -> bool:
        """Trigger immediate rotation."""
        logger.info("Triggering immediate rotation")
        asyncio.create_task(self.rotation_engine.rotate(force=True))
        return True
    
    async def _run(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")
        
        while self._running:
            try:
                await asyncio.sleep(self._interval)
                
                if not self._running:
                    break
                
                if self._paused:
                    continue
                
                logger.debug(f"Scheduled rotation triggered (interval: {self._interval}s)")
                await self.rotation_engine.rotate()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
        
        logger.info("Scheduler loop stopped")
