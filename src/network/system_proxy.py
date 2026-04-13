#!/usr/bin/env python3
"""
IPCon v.1 - Windows System Proxy Manager
Handles system-wide proxy settings via Windows Registry.
"""

import logging
import platform

logger = logging.getLogger(__name__)

class SystemProxy:
    """Manages Windows System Proxy settings."""
    
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
    
    @staticmethod
    def is_windows():
        return platform.system() == "Windows"
    
    def enable(self, host="127.0.0.1", port=9052):
        """Enable system-wide SOCKS proxy."""
        if not self.is_windows():
            return False
            
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_WRITE)
            
            # Enable proxy
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
            # Set proxy server (SOCKS)
            winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"socks={host}:{port}")
            # Optional: bypass local addresses
            winreg.SetValueEx(key, "ProxyOverride", 0, winreg.REG_SZ, "<local>")
            
            winreg.CloseKey(key)
            
            # Notify Windows of the change (optional but recommended)
            import ctypes
            internet_set_option = ctypes.windll.wininet.InternetSetOptionW
            internet_set_option(0, 39, 0, 0) # INTERNET_OPTION_SETTINGS_CHANGED
            internet_set_option(0, 37, 0, 0) # INTERNET_OPTION_REFRESH
            
            logger.info(f"Windows system-wide proxy enabled: {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to enable Windows system proxy: {e}")
            return False
            
    def disable(self):
        """Disable system-wide proxy."""
        if not self.is_windows():
            return False
            
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_WRITE)
            
            winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
            
            import ctypes
            internet_set_option = ctypes.windll.wininet.InternetSetOptionW
            internet_set_option(0, 39, 0, 0)
            internet_set_option(0, 37, 0, 0)
            
            logger.info("Windows system-wide proxy disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable Windows system proxy: {e}")
            return False

    def is_enabled(self):
        """Check if system proxy is enabled."""
        if not self.is_windows():
            return False
            
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.REG_PATH, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "ProxyEnable")
            winreg.CloseKey(key)
            return value == 1
        except:
            return False
