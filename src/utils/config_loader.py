#!/usr/bin/env python3
"""
IPCon v.1 - Configuration Loader
"""

import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RotationSettings:
    interval: int = 60
    strategy: str = "round_robin"
    pre_connect: bool = True
    pre_connect_time: float = 5.0
    max_retries: int = 3
    retry_delay: float = 2.0
    fail_threshold: int = 3
    health_check_interval: int = 30


@dataclass
class SecuritySettings:
    kill_switch: bool = True
    dns_leak_protection: bool = True
    ipv6_leak_protection: bool = True
    allowed_ports: List[int] = field(default_factory=lambda: [53, 67, 68])


@dataclass
class LoggingSettings:
    level: str = "INFO"
    file: str = "logs/ipcon.log"
    max_size: str = "10MB"
    backup_count: int = 5


@dataclass
class ProviderSettings:
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    config_file: Optional[str] = None
    interface: Optional[str] = None
    priority: int = 1
    enabled: bool = True


@dataclass
class NetworkSettings:
    dns_servers: List[str] = field(default_factory=lambda: ["1.1.1.1", "1.0.0.1"])
    vpn_interface: str = "tun+"
    mtu: int = 1400


@dataclass
class AppConfig:
    rotation: RotationSettings = field(default_factory=RotationSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    providers: List[ProviderSettings] = field(default_factory=list)


class ConfigLoader:
    """Loads and validates configuration from YAML files."""
    
    @staticmethod
    def load(path: str) -> AppConfig:
        """Load configuration from YAML file."""
        config_path = Path(path)
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return AppConfig()
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            return ConfigLoader._parse_config(data)
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return AppConfig()
    
    @staticmethod
    def _parse_config(data: dict) -> AppConfig:
        """Parse configuration data into AppConfig."""
        rotation_data = data.get("rotation", {})
        rotation = RotationSettings(
            interval=rotation_data.get("interval", 60),
            strategy=rotation_data.get("strategy", "round_robin"),
            pre_connect=rotation_data.get("pre_connect", True),
            pre_connect_time=rotation_data.get("pre_connect_time", 5.0),
            max_retries=rotation_data.get("max_retries", 3),
            retry_delay=rotation_data.get("retry_delay", 2.0),
            fail_threshold=rotation_data.get("fail_threshold", 3),
            health_check_interval=rotation_data.get("health_check_interval", 30)
        )
        
        security_data = data.get("security", {})
        security = SecuritySettings(
            kill_switch=security_data.get("kill_switch", True),
            dns_leak_protection=security_data.get("dns_leak_protection", True),
            ipv6_leak_protection=security_data.get("ipv6_leak_protection", True),
            allowed_ports=security_data.get("allowed_ports", [53, 67, 68])
        )
        
        logging_data = data.get("logging", {})
        logging_settings = LoggingSettings(
            level=logging_data.get("level", "INFO"),
            file=logging_data.get("file", "logs/ipcon.log"),
            max_size=logging_data.get("max_size", "10MB"),
            backup_count=logging_data.get("backup_count", 5)
        )
        
        network_data = data.get("network", {})
        network = NetworkSettings(
            dns_servers=network_data.get("dns_servers", ["1.1.1.1", "1.0.0.1"]),
            vpn_interface=network_data.get("vpn_interface", "tun+"),
            mtu=network_data.get("mtu", 1400)
        )
        
        providers = []
        for p_data in data.get("providers", []):
            provider = ProviderSettings(
                name=p_data.get("name", "unknown"),
                type=p_data.get("type", "unknown"),
                host=p_data.get("host"),
                port=p_data.get("port"),
                username=p_data.get("username"),
                password=p_data.get("password"),
                config_file=p_data.get("config_file"),
                interface=p_data.get("interface"),
                priority=p_data.get("priority", 1),
                enabled=p_data.get("enabled", True)
            )
            providers.append(provider)
        
        return AppConfig(
            rotation=rotation,
            security=security,
            logging=logging_settings,
            network=network,
            providers=providers
        )
