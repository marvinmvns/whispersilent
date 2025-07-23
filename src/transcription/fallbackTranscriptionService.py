import time
import threading
from typing import Optional, Dict, Any
from enum import Enum
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from config import Config
from logger import log
from connectivity import ConnectivityDetector, ConnectivityStatus

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'transcription'))
from speechRecognitionService import SpeechRecognitionService, TranscriptionEngine

class FallbackMode(Enum):
    """Fallback operation modes"""
    ONLINE_ONLY = "online_only"      # Use only online engines
    OFFLINE_ONLY = "offline_only"    # Use only offline engines  
    AUTO_FALLBACK = "auto_fallback"  # Automatically switch based on connectivity

class FallbackTranscriptionService:
    """
    Transcription service with automatic fallback support
    Switches between online/offline engines based on internet connectivity
    """
    
    def __init__(self):
        self.config = Config.SPEECH_RECOGNITION
        self.connectivity_detector = ConnectivityDetector(
            check_interval=self.config.get("connectivity_check_interval", 30)
        )
        
        # Fallback configuration
        self.enable_fallback = self.config.get("enable_fallback", True)
        self.offline_fallback_engine = self.config.get("offline_fallback_engine", "vosk")
        self.auto_switch = self.config.get("auto_switch_on_connection_loss", True)
        
        # Primary and fallback services
        self.primary_service = None
        self.fallback_service = None
        self.current_service = None
        
        # State tracking
        self.current_mode = FallbackMode.AUTO_FALLBACK
        self.last_connectivity_status = ConnectivityStatus.UNKNOWN
        self.fallback_count = 0
        self.service_lock = threading.Lock()
        
        # Initialize services
        self._initialize_services()
        
        # Setup connectivity monitoring
        if self.enable_fallback and self.auto_switch:
            self.connectivity_detector.add_status_callback(self._on_connectivity_change)
            self.connectivity_detector.start_monitoring()
        
        log.info(f"FallbackTranscriptionService initialized - Primary: {self.primary_service.engine.value if self.primary_service else 'None'}, Fallback: {self.offline_fallback_engine}")
    
    def _initialize_services(self):
        """Initialize primary and fallback transcription services"""
        try:
            # Initialize primary service (from config)
            self.primary_service = SpeechRecognitionService()
            
            # Initialize fallback service (offline engine)
            if self.enable_fallback:
                # Temporarily switch config to fallback engine
                original_engine = self.config["engine"]
                self.config["engine"] = self.offline_fallback_engine
                
                try:
                    self.fallback_service = SpeechRecognitionService()
                    log.info(f"Fallback service initialized with engine: {self.fallback_service.engine.value}")
                except Exception as e:
                    log.warning(f"Failed to initialize fallback service: {e}")
                    self.fallback_service = None
                finally:
                    # Restore original engine
                    self.config["engine"] = original_engine
            
            # Set current service based on connectivity
            self._select_current_service()
            
        except Exception as e:
            log.error(f"Failed to initialize fallback transcription service: {e}")
            raise
    
    def _select_current_service(self):
        """Select current service based on connectivity and configuration"""
        with self.service_lock:
            if not self.enable_fallback:
                self.current_service = self.primary_service
                log.debug("Fallback disabled, using primary service")
                return
            
            # Check connectivity
            connectivity_status = self.connectivity_detector.check_connectivity()
            
            if connectivity_status == ConnectivityStatus.ONLINE:
                # Online: use primary service
                if self.primary_service:
                    self.current_service = self.primary_service
                    log.debug(f"Online mode: using primary service ({self.primary_service.engine.value})")
                else:
                    self.current_service = self.fallback_service
                    log.warning("Primary service not available, using fallback")
            else:
                # Offline: use fallback service if available
                if self.fallback_service:
                    self.current_service = self.fallback_service
                    log.info(f"Offline mode: switched to fallback service ({self.fallback_service.engine.value})")
                    if connectivity_status != self.last_connectivity_status:
                        self.fallback_count += 1
                else:
                    self.current_service = self.primary_service
                    log.warning("Fallback service not available, using primary service offline")
            
            self.last_connectivity_status = connectivity_status
    
    def _on_connectivity_change(self, new_status: ConnectivityStatus):
        """Handle connectivity status changes"""
        if not self.auto_switch:
            return
        
        log.info(f"Connectivity changed to {new_status.value}, re-evaluating service selection")
        self._select_current_service()
    
    def transcribe(self, audio_chunk: np.ndarray) -> str:
        """
        Transcribe audio with automatic fallback support
        
        Args:
            audio_chunk: numpy array of audio samples
            
        Returns:
            str: Transcribed text or empty string if no speech detected
        """
        if not self.current_service:
            log.error("No transcription service available")
            return ""
        
        try:
            # Attempt transcription with current service
            result = self.current_service.transcribe(audio_chunk)
            return result
            
        except Exception as e:
            log.warning(f"Transcription failed with {self.current_service.engine.value}: {e}")
            
            # If fallback is enabled and we have a fallback service, try it
            if (self.enable_fallback and 
                self.fallback_service and 
                self.current_service != self.fallback_service):
                
                log.info(f"Attempting fallback transcription with {self.fallback_service.engine.value}")
                try:
                    result = self.fallback_service.transcribe(audio_chunk)
                    self.fallback_count += 1
                    
                    # If fallback succeeds, consider switching to it temporarily
                    if result.strip():
                        log.info("Fallback transcription successful, temporarily switching service")
                        with self.service_lock:
                            self.current_service = self.fallback_service
                    
                    return result
                    
                except Exception as fallback_error:
                    log.error(f"Fallback transcription also failed: {fallback_error}")
            
            return ""
    
    def force_online_mode(self):
        """Force the service to use only online engines"""
        with self.service_lock:
            self.current_mode = FallbackMode.ONLINE_ONLY
            if self.primary_service and not self.primary_service.is_offline_engine():
                self.current_service = self.primary_service
                log.info("Forced to online-only mode")
            else:
                log.warning("No online engine available for online-only mode")
    
    def force_offline_mode(self):
        """Force the service to use only offline engines"""
        with self.service_lock:
            self.current_mode = FallbackMode.OFFLINE_ONLY
            if self.fallback_service and self.fallback_service.is_offline_engine():
                self.current_service = self.fallback_service
                log.info("Forced to offline-only mode")
            elif self.primary_service and self.primary_service.is_offline_engine():
                self.current_service = self.primary_service
                log.info("Forced to offline-only mode with primary service")
            else:
                log.warning("No offline engine available for offline-only mode")
    
    def enable_auto_fallback(self):
        """Enable automatic fallback based on connectivity"""
        with self.service_lock:
            self.current_mode = FallbackMode.AUTO_FALLBACK
            self._select_current_service()
            log.info("Enabled automatic fallback mode")
    
    def get_current_engine(self) -> str:
        """Get the currently active engine name"""
        if self.current_service:
            return self.current_service.engine.value
        return "none"
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        connectivity_status = self.connectivity_detector.get_status()
        
        status = {
            "fallback_enabled": self.enable_fallback,
            "auto_switch_enabled": self.auto_switch,
            "current_mode": self.current_mode.value,
            "connectivity_status": connectivity_status.value,
            "fallback_count": self.fallback_count,
            "current_engine": self.get_current_engine(),
            "primary_engine": self.primary_service.engine.value if self.primary_service else None,
            "fallback_engine": self.fallback_service.engine.value if self.fallback_service else None,
            "services_available": {
                "primary": self.primary_service is not None,
                "fallback": self.fallback_service is not None
            }
        }
        
        return status
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the current engine"""
        if self.current_service:
            return self.current_service.get_engine_info()
        return {"engine": "none", "status": "unavailable"}
    
    def switch_engine(self, engine_name: str) -> bool:
        """
        Switch the primary engine (affects future service selection)
        
        Args:
            engine_name: Name of the engine to switch to
            
        Returns:
            bool: True if switch was successful
        """
        try:
            # Switch primary service
            if self.primary_service and self.primary_service.switch_engine(engine_name):
                # Re-evaluate current service selection
                self._select_current_service()
                log.info(f"Successfully switched primary engine to {engine_name}")
                return True
            return False
        except Exception as e:
            log.error(f"Failed to switch engine to {engine_name}: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        log.info("Cleaning up FallbackTranscriptionService")
        
        # Stop connectivity monitoring
        self.connectivity_detector.stop_monitoring()
        
        # Cleanup services
        if self.primary_service:
            self.primary_service.cleanup()
        if self.fallback_service:
            self.fallback_service.cleanup()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass


if __name__ == '__main__':
    # Test the fallback transcription service
    import numpy as np
    
    # Create sample audio data for testing
    sample_rate = 16000
    duration = 3  # 3 seconds
    t = np.linspace(0, duration, sample_rate * duration)
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)  # 440 Hz tone
    
    try:
        service = FallbackTranscriptionService()
        print(f"Service status: {service.get_status()}")
        print(f"Current engine: {service.get_current_engine()}")
        
        # Test transcription
        result = service.transcribe(audio_data)
        print(f"Transcription result: '{result}'")
        
        # Test mode switching
        print("\nTesting offline mode...")
        service.force_offline_mode()
        print(f"Current engine after offline mode: {service.get_current_engine()}")
        
        print("\nTesting online mode...")
        service.force_online_mode()
        print(f"Current engine after online mode: {service.get_current_engine()}")
        
        print("\nRe-enabling auto fallback...")
        service.enable_auto_fallback()
        print(f"Current engine with auto fallback: {service.get_current_engine()}")
        
        service.cleanup()
        
    except Exception as e:
        log.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()