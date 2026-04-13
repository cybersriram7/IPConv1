#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║   ███████╗██╗   ██╗███████╗████████╗███████╗██╗      ██████╗ ██╲    ██╗███████╗  ║
║   ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║██╔════╝  ║
║   ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║█████╗    ║
║   ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║██╔══╝    ║
║   ███████║   ██║   ███████║   ██║   ███████╗███████╗╚██████╔╝╚███╔███╔╝███████╗  ║
║   ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝  ║
║                                                                                      ║
║                          Professional IP Rotation System                               ║
║                                    VERSION 1.0                                       ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

    [AUTOMATIC IP ROTATION]    [MULTI-PROVIDER SUPPORT]    [KILL SWITCH PROTECTION]
    [MULTI-HOP CHAINS]        [DNS LEAK PROTECTION]       [REAL-TIME MONITORING]
"""

import sys
import argparse
import asyncio
import signal
import logging
import time
import os
from pathlib import Path
import platform
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.core.rotation_engine import RotationEngine, RotationState, RotationStats, RotationConfig
from src.core.scheduler import Scheduler
from src.core.chain_manager import ChainManager
from src.providers.base_provider import BaseProvider, ProviderStatus
from src.providers.openvpn_provider import OpenVPNProvider
from src.providers.wireguard_provider import WireGuardProvider
from src.providers.socks5_provider import SOCKS5Provider
from src.providers.http_proxy_provider import HTTPProxyProvider
from src.network.kill_switch import KillSwitch
from src.network.dns_protection import DNSProtection
from src.network.ip_verifier import IPVerifier
from src.network.leak_prevention import LeakPrevention
from src.utils.config_loader import ConfigLoader, AppConfig
from src.utils.logger import setup_logging
from src.cli.interface import CLI


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def c(text, color):
    return f"{getattr(Colors, color.upper(), '')}{text}{Colors.ENDC}"


def is_windows():
    return platform.system() == "Windows"


def clear_screen():
    os.system('cls' if is_windows() else 'clear')


BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║   ███████╗██╗   ██╗███████╗████████╗███████╗██╗      ██████╗ ██╲    ██╗███████╗  ║
║   ██╔════╝╚██╗ ██╔╝██╔════╝╚══██╔══╝██╔════╝██║     ██╔═══██╗██║    ██║██╔════╝  ║
║   ███████╗ ╚████╔╝ ███████╗   ██║   █████╗  ██║     ██║   ██║██║ █╗ ██║█████╗    ║
║   ╚════██║  ╚██╔╝  ╚════██║   ██║   ██╔══╝  ██║     ██║   ██║██║███╗██║██╔══╝    ║
║   ███████║   ██║   ███████║   ██║   ███████╗███████╗╚██████╔╝╚███╔███╔╝███████╗  ║
║   ╚══════╝   ╚═╝   ╚══════╝   ╚═╝   ╚══════╝╚══════╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝  ║
║                                                                                      ║
║                          Professional IP Rotation System                               ║
║                                    VERSION 1.0                                       ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""


def print_banner():
    print(c(BANNER, "CYAN"))
    print(c("═" * 75, "CYAN"))
    print(c(f"{'⚡ AUTOMATIC IP ROTATION':^75}", "GREEN"))
    print(c(f"{'🔒 KILL SWITCH • 🌐 MULTI-PROVIDER • 📊 REAL-TIME MONITORING':^75}", "YELLOW"))
    print(c("═" * 75, "CYAN"))
    print()


class IPConApp:
    """Main application class for IPCon v.1"""
    
    def __init__(self, config_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = config_path or os.path.join(base_dir, "config/config.yaml")
        self.config: Optional[AppConfig] = None
        self.rotation_engine: Optional[RotationEngine] = None
        self.scheduler: Optional[Scheduler] = None
        self.chain_manager: Optional[ChainManager] = None
        self.kill_switch: Optional[KillSwitch] = None
        self.dns_protection: Optional[DNSProtection] = None
        self.leak_prevention: Optional[LeakPrevention] = None
        self.ip_verifier: Optional[IPVerifier] = None
        self.cli: Optional[CLI] = None
        self._running = False
        self._start_time: Optional[float] = None
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            setup_logging()
            logger = logging.getLogger(__name__)
            
            print_banner()
            
            logger.info("Loading configuration...")
            self.config = ConfigLoader.load(self.config_path)
            
            logger.info("Initializing components...")
            
            self.ip_verifier = IPVerifier()
            self.kill_switch = KillSwitch()
            self.dns_protection = DNSProtection()
            self.leak_prevention = LeakPrevention()
            
            self.chain_manager = ChainManager(self.config)
            await self.chain_manager.initialize()
            
            rotation_config = RotationConfig(
                interval=self.config.rotation.interval,
                strategy=self.config.rotation.strategy,
                pre_connect=self.config.rotation.pre_connect,
                pre_connect_time=self.config.rotation.pre_connect_time,
                max_retries=self.config.rotation.max_retries,
                retry_delay=self.config.rotation.retry_delay,
                fail_threshold=self.config.rotation.fail_threshold,
                health_check_interval=self.config.rotation.health_check_interval
            )
            
            self.rotation_engine = RotationEngine(
                chain_manager=self.chain_manager,
                ip_verifier=self.ip_verifier,
                config=rotation_config
            )
            
            self.scheduler = Scheduler(self.rotation_engine)
            self.cli = CLI(self)
            
            logger.info("Initialization complete!")
            return True
            
        except Exception as e:
            logging.error(f"Initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def start(self, interval: Optional[int] = None, provider: Optional[str] = None) -> bool:
        """Start IPCon v.1"""
        try:
            if interval:
                self.config.rotation.interval = interval
            
            if provider:
                await self.chain_manager.set_active_provider(provider)
            
            if not is_windows():
                if self.config.security.kill_switch:
                    logger = logging.getLogger(__name__)
                    logger.info("Enabling kill switch...")
                    await self.kill_switch.enable()
                
                if self.config.security.dns_leak_protection:
                    logger = logging.getLogger(__name__)
                    logger.info("Enabling DNS leak protection...")
                    await self.dns_protection.enable()
                
                if self.config.security.ipv6_leak_protection:
                    logger = logging.getLogger(__name__)
                    logger.info("Enabling IPv6 leak prevention...")
                    await self.leak_prevention.enable_ipv6_block()
            else:
                logger = logging.getLogger(__name__)
                logger.info("Skipping Linux-only security features (Kill Switch, DNS Protection, IPv6 Block) on Windows.")
            
            await self.rotation_engine.start()
            await self.scheduler.start()
            
            self._running = True
            self._start_time = time.time()
            
            logger = logging.getLogger(__name__)
            logger.info(f"IPCon v.1 started - Rotating every {self.config.rotation.interval}s")
            
            return True
            
        except Exception as e:
            logging.error(f"Start failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def stop(self, graceful: bool = True) -> bool:
        """Stop IPCon v.1"""
        try:
            logger = logging.getLogger(__name__)
            logger.info("Stopping IPCon v.1...")
            
            self._running = False
            
            if self.scheduler:
                await self.scheduler.stop()
            
            if self.rotation_engine:
                await self.rotation_engine.stop()
            
            if self.kill_switch:
                await self.kill_switch.disable()
            
            if self.dns_protection:
                await self.dns_protection.disable()
            
            if self.leak_prevention:
                await self.leak_prevention.disable_ipv6_block()
            
            if self.chain_manager:
                await self.chain_manager.disconnect_all()
            
            logger.info("IPCon v.1 stopped successfully")
            return True
            
        except Exception as e:
            logging.error(f"Stop failed: {e}")
            return False
    
    async def get_status(self) -> dict:
        """Get current status."""
        status = {
            "running": self._running,
            "uptime": time.time() - self._start_time if self._start_time else 0,
            "current_ip": await self.ip_verifier.get_current_ip() if self.ip_verifier else None,
            "kill_switch_active": await self.kill_switch.is_enabled() if self.kill_switch else False,
            "dns_protection_active": await self.dns_protection.is_enabled() if self.dns_protection else False
        }
        
        if self.rotation_engine:
            engine_status = await self.rotation_engine.get_status()
            status.update(engine_status)
        
        if self.chain_manager:
            status["providers"] = await self.chain_manager.get_providers()
            status["active_provider"] = await self.chain_manager.get_active_provider()
        
        return status
    
    async def set_interval(self, seconds: int) -> bool:
        """Set rotation interval."""
        if self.scheduler:
            await self.scheduler.set_interval(seconds)
            self.config.rotation.interval = seconds
            return True
        return False
    
    async def set_provider(self, name: str) -> bool:
        """Set active provider."""
        return await self.chain_manager.set_active_provider(name)
    
    async def emergency_kill(self) -> bool:
        """Emergency kill - block all traffic."""
        if self.kill_switch:
            return await self.kill_switch.emergency_kill()
        return False


async def async_main(args) -> int:
    """Async main function."""
    app = IPConApp(args.config)
    
    if not await app.initialize():
        return 1
    
    if args.command == "start":
        success = await app.start(
            interval=args.interval,
            provider=args.provider
        )
        if success and not args.daemon:
            try:
                while app._running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
        return 0 if success else 1
    
    elif args.command == "stop":
        success = await app.stop(graceful=args.graceful)
        return 0 if success else 1
    
    elif args.command == "status":
        status = await app.get_status()
        app.cli.print_status(status, verbose=args.verbose, json_output=args.json)
        return 0
    
    elif args.command == "restart":
        await app.stop()
        await asyncio.sleep(1)
        success = await app.start()
        return 0 if success else 1
    
    elif args.command == "set-interval":
        success = await app.set_interval(args.seconds)
        if success:
            print(f"Rotation interval set to {args.seconds} seconds")
        return 0 if success else 1
    
    elif args.command == "set-provider":
        success = await app.set_provider(args.provider)
        if success:
            print(f"Provider set to {args.provider}")
        return 0 if success else 1
    
    elif args.command == "test":
        verifier = IPVerifier()
        ip = await verifier.get_current_ip()
        latency = await verifier.measure_latency()
        print(f"Current IP: {ip}")
        print(f"Latency: {latency:.0f}ms")
        return 0
    
    elif args.command == "emergency-kill":
        success = await app.emergency_kill()
        if success:
            print("EMERGENCY: All traffic blocked!")
        return 0 if success else 1
    
    elif args.command == "monitor":
        print_banner()
        print(c("Real-time Monitoring Mode", "GREEN"))
        print(c("Press Ctrl+C to exit", "YELLOW"))
        print()
        
        while True:
            try:
                status = await app.get_status()
                clear_screen()
                print_banner()
                app.cli.print_status(status, verbose=True)
                await asyncio.sleep(2)
            except KeyboardInterrupt:
                break
        
        return 0
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="IPCon v.1 - Professional IP Rotation System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-c", "--config", help="Configuration file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    start_parser = subparsers.add_parser("start", help="Start IPCon v.1")
    start_parser.add_argument("--interval", type=int, help="Rotation interval in seconds")
    start_parser.add_argument("--provider", help="Provider name")
    start_parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    stop_parser = subparsers.add_parser("stop", help="Stop IPCon v.1")
    stop_parser.add_argument("--graceful", action="store_true", help="Graceful shutdown")
    
    status_parser = subparsers.add_parser("status", help="Show status")
    status_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose")
    status_parser.add_argument("--json", action="store_true", help="JSON output")
    
    subparsers.add_parser("restart", help="Restart IPCon v.1")
    
    set_interval_parser = subparsers.add_parser("set-interval", help="Set interval")
    set_interval_parser.add_argument("seconds", type=int, help="Seconds")
    
    set_provider_parser = subparsers.add_parser("set-provider", help="Set provider")
    set_provider_parser.add_argument("provider", help="Provider name")
    
    subparsers.add_parser("test", help="Test connection")
    
    subparsers.add_parser("emergency-kill", help="Emergency kill switch")
    
    monitor_parser = subparsers.add_parser("monitor", help="Real-time monitoring")
    
    args = parser.parse_args()
    
    if not args.command:
        print_banner()
        parser.print_help()
        return 1
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
    
    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
