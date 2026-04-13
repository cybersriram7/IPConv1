import subprocess
import logging
import platform

logger = logging.getLogger(__name__)


class LeakPrevention:
    def __init__(self):
        self.enabled = False

    def enable(self):
        try:
            if platform.system() == "Windows":
                logger.warning("IPv6 leak prevention is not supported on Windows.")
                return False
            subprocess.run(['ip6tables', '-F'], check=False)
            subprocess.run(['ip6tables', '-P', 'INPUT', 'DROP'], check=False)
            subprocess.run(['ip6tables', '-P', 'FORWARD', 'DROP'], check=False)
            subprocess.run(['ip6tables', '-P', 'OUTPUT', 'DROP'], check=False)
            self.enabled = True
            logger.info("IPv6 leak prevention enabled")
            return True
        except Exception as e:
            logger.error(f"Failed to enable leak prevention: {e}")
            return False

    def disable(self):
        try:
            subprocess.run(['ip6tables', '-F'], check=False)
            subprocess.run(['ip6tables', '-P', 'INPUT', 'ACCEPT'], check=False)
            subprocess.run(['ip6tables', '-P', 'FORWARD', 'ACCEPT'], check=False)
            subprocess.run(['ip6tables', '-P', 'OUTPUT', 'ACCEPT'], check=False)
            self.enabled = False
            logger.info("IPv6 leak prevention disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable leak prevention: {e}")
            return False

    def is_enabled(self):
        return self.enabled

    async def enable_ipv6_block(self):
        """Async alias for enable() used by main app."""
        return self.enable()

    async def disable_ipv6_block(self):
        """Async alias for disable() used by main app."""
        return self.disable()
