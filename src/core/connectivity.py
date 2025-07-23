import socket
import time
import threading
from typing import Optional, Callable
from enum import Enum

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from logger import log

class ConnectivityStatus(Enum):
    """Network connectivity status"""
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

class ConnectivityDetector:
    """
    Network connectivity detector with automatic monitoring and callbacks
    """
    
    def __init__(self, 
                 check_interval: int = 30,
                 timeout: int = 5,
                 test_hosts: Optional[list] = None):
        """
        Initialize connectivity detector
        
        Args:
            check_interval: Seconds between connectivity checks
            timeout: Socket timeout in seconds
            test_hosts: List of (host, port) tuples to test connectivity
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.test_hosts = test_hosts or [
            ("8.8.8.8", 53),      # Google DNS
            ("1.1.1.1", 53),      # Cloudflare DNS
            ("208.67.222.222", 53) # OpenDNS
        ]
        
        self._status = ConnectivityStatus.UNKNOWN
        self._last_check = 0
        self._monitor_thread = None
        self._monitoring = False
        self._status_callbacks = []
        self._lock = threading.Lock()
        
        log.info(f"ConnectivityDetector initialized with {len(self.test_hosts)} test hosts")
    
    def add_status_callback(self, callback: Callable[[ConnectivityStatus], None]):
        """Add callback function to be called when connectivity status changes"""
        with self._lock:
            self._status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[ConnectivityStatus], None]):
        """Remove status change callback"""
        with self._lock:
            if callback in self._status_callbacks:
                self._status_callbacks.remove(callback)
    
    def _notify_callbacks(self, new_status: ConnectivityStatus):
        """Notify all registered callbacks of status change"""
        with self._lock:
            callbacks = self._status_callbacks.copy()
        
        for callback in callbacks:
            try:
                callback(new_status)
            except Exception as e:
                log.error(f"Error in connectivity status callback: {e}")
    
    def _test_single_host(self, host: str, port: int) -> bool:
        """Test connectivity to a single host"""
        try:
            with socket.create_connection((host, port), timeout=self.timeout):
                return True
        except (socket.error, OSError):
            return False
    
    def check_connectivity(self, force_check: bool = False) -> ConnectivityStatus:
        """
        Check network connectivity
        
        Args:
            force_check: Force a new check even if recently checked
            
        Returns:
            ConnectivityStatus: Current connectivity status
        """
        current_time = time.time()
        
        # Use cached result if recent and not forced
        if not force_check and (current_time - self._last_check) < 10:
            return self._status
        
        log.debug("Checking network connectivity...")
        
        # Test connectivity to multiple hosts
        successful_tests = 0
        for host, port in self.test_hosts:
            if self._test_single_host(host, port):
                successful_tests += 1
                # If at least one host is reachable, consider online
                break
        
        # Determine new status
        new_status = ConnectivityStatus.ONLINE if successful_tests > 0 else ConnectivityStatus.OFFLINE
        
        # Update status and notify callbacks if changed
        old_status = self._status
        self._status = new_status
        self._last_check = current_time
        
        if old_status != new_status:
            log.info(f"Connectivity status changed: {old_status.value} -> {new_status.value}")
            self._notify_callbacks(new_status)
        else:
            log.debug(f"Connectivity status: {new_status.value}")
        
        return new_status
    
    def is_online(self, force_check: bool = False) -> bool:
        """Check if currently online"""
        return self.check_connectivity(force_check) == ConnectivityStatus.ONLINE
    
    def is_offline(self, force_check: bool = False) -> bool:
        """Check if currently offline"""
        return self.check_connectivity(force_check) == ConnectivityStatus.OFFLINE
    
    def get_status(self) -> ConnectivityStatus:
        """Get current cached status without checking"""
        return self._status
    
    def start_monitoring(self):
        """Start continuous connectivity monitoring in background thread"""
        if self._monitoring:
            log.warning("Connectivity monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        log.info(f"Started connectivity monitoring (check interval: {self.check_interval}s)")
    
    def stop_monitoring(self):
        """Stop connectivity monitoring"""
        if not self._monitoring:
            return
        
        self._monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        log.info("Stopped connectivity monitoring")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring:
            try:
                self.check_connectivity(force_check=True)
                time.sleep(self.check_interval)
            except Exception as e:
                log.error(f"Error in connectivity monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def get_info(self) -> dict:
        """Get connectivity detector information"""
        return {
            "status": self._status.value,
            "last_check": self._last_check,
            "check_interval": self.check_interval,
            "timeout": self.timeout,
            "test_hosts": self.test_hosts,
            "monitoring": self._monitoring,
            "callbacks_count": len(self._status_callbacks)
        }


# Global connectivity detector instance
_connectivity_detector = None

def get_connectivity_detector() -> ConnectivityDetector:
    """Get the global connectivity detector instance"""
    global _connectivity_detector
    if _connectivity_detector is None:
        _connectivity_detector = ConnectivityDetector()
    return _connectivity_detector

def is_online(force_check: bool = False) -> bool:
    """Quick function to check if online"""
    return get_connectivity_detector().is_online(force_check)

def is_offline(force_check: bool = False) -> bool:
    """Quick function to check if offline"""
    return get_connectivity_detector().is_offline(force_check)

def get_connectivity_status(force_check: bool = False) -> ConnectivityStatus:
    """Quick function to get connectivity status"""
    return get_connectivity_detector().check_connectivity(force_check)


if __name__ == '__main__':
    # Test the connectivity detector
    detector = ConnectivityDetector()
    
    # Add a test callback
    def on_status_change(status):
        print(f"🌐 Connectivity changed to: {status.value}")
    
    detector.add_status_callback(on_status_change)
    
    # Test connectivity
    print("Testing connectivity...")
    status = detector.check_connectivity(force_check=True)
    print(f"Current status: {status.value}")
    
    # Test monitoring
    print("Starting monitoring for 30 seconds...")
    detector.start_monitoring()
    time.sleep(30)
    detector.stop_monitoring()
    
    print("Connectivity test completed")