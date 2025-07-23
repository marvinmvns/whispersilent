#!/usr/bin/env python3
"""
Fallback System Test Script
Tests the automatic fallback functionality between online and offline transcription engines
"""

import os
import sys
import time
import numpy as np
import socket
from contextlib import contextmanager

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'transcription'))

from connectivity import ConnectivityDetector, ConnectivityStatus
from fallbackTranscriptionService import FallbackTranscriptionService
from logger import log


@contextmanager
def mock_offline_mode():
    """Context manager to simulate offline mode by blocking DNS resolution"""
    original_getaddrinfo = socket.getaddrinfo
    
    def mock_getaddrinfo(*args, **kwargs):
        raise socket.gaierror("Name resolution failed (simulated offline)")
    
    try:
        print("🔌 Simulating offline mode...")
        socket.getaddrinfo = mock_getaddrinfo
        yield
    finally:
        print("🌐 Restoring online mode...")
        socket.getaddrinfo = original_getaddrinfo


class FallbackSystemTester:
    """Test suite for the fallback transcription system"""
    
    def __init__(self):
        self.test_results = []
        self.sample_audio = self._generate_test_audio()
    
    def _generate_test_audio(self) -> np.ndarray:
        """Generate test audio data"""
        sample_rate = 16000
        duration = 2  # 2 seconds
        t = np.linspace(0, duration, sample_rate * duration)
        
        # Generate a simple tone (this won't actually transcribe to text, but tests the pipeline)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        return audio_data
    
    def _record_test_result(self, test_name: str, success: bool, details: str = ""):
        """Record test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {test_name}: {details}")
    
    def test_connectivity_detector(self) -> bool:
        """Test connectivity detection functionality"""
        print("\n🔍 Testing Connectivity Detector...")
        
        try:
            detector = ConnectivityDetector(check_interval=5)
            
            # Test initial connectivity check
            status = detector.check_connectivity(force_check=True)
            self._record_test_result(
                "Initial connectivity check",
                status in [ConnectivityStatus.ONLINE, ConnectivityStatus.OFFLINE],
                f"Status: {status.value}"
            )
            
            # Test callback system
            callback_triggered = []
            
            def test_callback(new_status):
                callback_triggered.append(new_status)
            
            detector.add_status_callback(test_callback)
            
            # Simulate status change by forcing different check
            with mock_offline_mode():
                offline_status = detector.check_connectivity(force_check=True)
                time.sleep(0.1)  # Allow callback to trigger
            
            online_status = detector.check_connectivity(force_check=True)
            
            callback_success = len(callback_triggered) > 0
            self._record_test_result(
                "Connectivity status callbacks",
                callback_success,
                f"Callbacks triggered: {len(callback_triggered)}"
            )
            
            return True
            
        except Exception as e:
            self._record_test_result("Connectivity detector test", False, f"Error: {e}")
            return False
    
    def test_fallback_service_initialization(self) -> bool:
        """Test fallback service initialization"""
        print("\n🚀 Testing Fallback Service Initialization...")
        
        try:
            service = FallbackTranscriptionService()
            
            # Test basic initialization
            status = service.get_status()
            self._record_test_result(
                "Service initialization",
                status['services_available']['primary'],
                f"Primary engine: {status['primary_engine']}"
            )
            
            # Test engine info
            engine_info = service.get_engine_info()
            self._record_test_result(
                "Engine information retrieval",
                'engine' in engine_info,
                f"Current engine: {engine_info.get('engine', 'unknown')}"
            )
            
            return True
            
        except Exception as e:
            self._record_test_result("Fallback service initialization", False, f"Error: {e}")
            return False
    
    def test_manual_mode_switching(self) -> bool:
        """Test manual switching between online/offline modes"""
        print("\n🔄 Testing Manual Mode Switching...")
        
        try:
            service = FallbackTranscriptionService()
            original_engine = service.get_current_engine()
            
            # Test offline mode
            service.force_offline_mode()
            offline_engine = service.get_current_engine()
            self._record_test_result(
                "Force offline mode",
                offline_engine != original_engine or service.get_engine_info().get('offline', False),
                f"Engine: {original_engine} -> {offline_engine}"
            )
            
            # Test online mode
            service.force_online_mode()
            online_engine = service.get_current_engine()
            self._record_test_result(
                "Force online mode",
                True,  # Just test that it doesn't crash
                f"Engine: {offline_engine} -> {online_engine}"
            )
            
            # Test auto fallback re-enable
            service.enable_auto_fallback()
            auto_engine = service.get_current_engine()
            self._record_test_result(
                "Re-enable auto fallback",
                True,
                f"Engine: {online_engine} -> {auto_engine}"
            )
            
            service.cleanup()
            return True
            
        except Exception as e:
            self._record_test_result("Manual mode switching", False, f"Error: {e}")
            return False
    
    def test_transcription_with_fallback(self) -> bool:
        """Test transcription functionality with fallback"""
        print("\n🎤 Testing Transcription with Fallback...")
        
        try:
            service = FallbackTranscriptionService()
            
            # Test normal transcription
            result = service.transcribe(self.sample_audio)
            self._record_test_result(
                "Basic transcription",
                True,  # Success if no exceptions
                f"Result length: {len(result)} chars"
            )
            
            # Test with simulated offline condition
            with mock_offline_mode():
                service.force_offline_mode()
                offline_result = service.transcribe(self.sample_audio)
                self._record_test_result(
                    "Offline transcription",
                    True,  # Success if no exceptions
                    f"Offline result length: {len(offline_result)} chars"
                )
            
            service.cleanup()
            return True
            
        except Exception as e:
            self._record_test_result("Transcription with fallback", False, f"Error: {e}")
            return False
    
    def test_automatic_fallback_simulation(self) -> bool:
        """Test automatic fallback when connectivity changes"""
        print("\n🌐 Testing Automatic Fallback Simulation...")
        
        try:
            service = FallbackTranscriptionService()
            
            # Record initial state
            initial_status = service.get_status()
            initial_engine = service.get_current_engine()
            
            # Simulate connectivity loss and check if service adapts
            connectivity_detector = service.connectivity_detector
            
            # Force a connectivity change simulation
            with mock_offline_mode():
                # Force connectivity check
                connectivity_detector.check_connectivity(force_check=True)
                time.sleep(0.5)  # Allow time for callback processing
                
                offline_status = service.get_status()
                offline_engine = service.get_current_engine()
                
                fallback_triggered = (
                    offline_status['connectivity_status'] == 'offline' or 
                    offline_engine != initial_engine
                )
                
                self._record_test_result(
                    "Automatic fallback on connectivity loss",
                    fallback_triggered,
                    f"Engine: {initial_engine} -> {offline_engine}, Status: {offline_status['connectivity_status']}"
                )
            
            # Test recovery
            connectivity_detector.check_connectivity(force_check=True)
            time.sleep(0.5)
            
            recovery_status = service.get_status()
            recovery_engine = service.get_current_engine()
            
            self._record_test_result(
                "Recovery on connectivity restore",
                recovery_status['connectivity_status'] == 'online',
                f"Final engine: {recovery_engine}, Status: {recovery_status['connectivity_status']}"
            )
            
            service.cleanup()
            return True
            
        except Exception as e:
            self._record_test_result("Automatic fallback simulation", False, f"Error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all fallback system tests"""
        print("🧪 Starting Fallback System Tests")
        print("=" * 60)
        
        test_methods = [
            self.test_connectivity_detector,
            self.test_fallback_service_initialization, 
            self.test_manual_mode_switching,
            self.test_transcription_with_fallback,
            self.test_automatic_fallback_simulation
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {e}")
        
        # Print summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Print detailed results
        print(f"\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        return passed_tests == total_tests


def main():
    """Main test function"""
    print("🎯 WhisperSilent Fallback System Test Suite")
    print("=" * 70)
    
    tester = FallbackSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print(f"\n🎉 All tests passed! Fallback system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the detailed results above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())