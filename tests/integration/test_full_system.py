#!/usr/bin/env python3
"""
Full system integration test for WhisperSilent
Tests all speech recognition engines and system components
"""

import sys
import os
import unittest
import numpy as np
import tempfile
from unittest.mock import patch, MagicMock

# Add project paths
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(os.path.join(project_root, 'src', 'core'))
sys.path.append(os.path.join(project_root, 'src', 'transcription'))
sys.path.append(os.path.join(project_root, 'src', 'api'))
sys.path.append(os.path.join(project_root, 'src', 'services'))

from config import Config
from speechRecognitionService import SpeechRecognitionService, TranscriptionEngine
from transcriptionPipeline import TranscriptionPipeline

class TestFullSystem(unittest.TestCase):
    """Test complete system functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Save original environment
        self.original_env = os.environ.copy()
        
        # Set test environment variables
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'
        os.environ['SPEECH_RECOGNITION_LANGUAGE'] = 'pt-BR'
        os.environ['API_ENDPOINT'] = 'https://test-endpoint.com'
        os.environ['API_KEY'] = 'test-key'
        
        # Reload config
        import importlib
        import config
        importlib.reload(config)
        
    def tearDown(self):
        """Clean up test environment"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Reload config again
        import importlib
        import config
        importlib.reload(config)
    
    def test_configuration_loading(self):
        """Test that configuration loads correctly"""
        from config import Config
        
        self.assertEqual(Config.SPEECH_RECOGNITION["engine"], "google")
        self.assertEqual(Config.SPEECH_RECOGNITION["language"], "pt-BR")
        self.assertEqual(Config.API["endpoint"], "https://test-endpoint.com")
        self.assertEqual(Config.API["key"], "test-key")
    
    def test_speech_recognition_service_initialization(self):
        """Test SpeechRecognitionService initializes correctly"""
        service = SpeechRecognitionService()
        
        self.assertEqual(service.engine, TranscriptionEngine.GOOGLE)
        self.assertEqual(service.language, "pt-BR")
        self.assertIsNotNone(service.recognizer)
    
    def test_engine_switching(self):
        """Test engine switching functionality"""
        service = SpeechRecognitionService()
        
        # Test valid engine switch
        result = service.switch_engine("sphinx")
        self.assertTrue(result)
        self.assertEqual(service.engine, TranscriptionEngine.SPHINX)
        
        # Test invalid engine switch
        result = service.switch_engine("invalid_engine")
        self.assertFalse(result)
        self.assertEqual(service.engine, TranscriptionEngine.SPHINX)  # Should remain unchanged
    
    def test_engine_info(self):
        """Test engine information retrieval"""
        service = SpeechRecognitionService()
        info = service.get_engine_info()
        
        self.assertIn("engine", info)
        self.assertIn("language", info)
        self.assertIn("offline", info)
        self.assertIn("requires_api_key", info)
        self.assertIn("status", info)
        
        self.assertEqual(info["engine"], "google")
        self.assertEqual(info["language"], "pt-BR")
        self.assertFalse(info["offline"])  # Google is online
        self.assertFalse(info["requires_api_key"])  # Free Google doesn't require key
    
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_audio_transcription(self, mock_recognize):
        """Test audio transcription with mocked Google service"""
        # Mock successful recognition
        mock_recognize.return_value = "Test transcription result"
        
        service = SpeechRecognitionService()
        
        # Create test audio data
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        
        # Test transcription
        result = service.transcribe(audio_data)
        
        self.assertEqual(result, "Test transcription result")
        self.assertTrue(mock_recognize.called)
    
    @patch('speech_recognition.Recognizer.recognize_google')
    def test_failed_transcription(self, mock_recognize):
        """Test handling of transcription failures"""
        # Mock recognition failure
        import speech_recognition as sr
        mock_recognize.side_effect = sr.UnknownValueError()
        
        service = SpeechRecognitionService()
        
        # Create test audio data
        audio_data = np.zeros(16000, dtype=np.int16)
        
        # Test failed transcription
        result = service.transcribe(audio_data)
        
        self.assertEqual(result, "")  # Should return empty string on failure
    
    def test_pipeline_initialization(self):
        """Test TranscriptionPipeline initializes correctly"""
        pipeline = TranscriptionPipeline()
        
        self.assertIsNotNone(pipeline.transcription_service)
        self.assertIsInstance(pipeline.transcription_service, SpeechRecognitionService)
        self.assertIsNotNone(pipeline.api_service)
        self.assertIsNotNone(pipeline.health_monitor)
        self.assertIsNotNone(pipeline.transcription_storage)
        self.assertIsNotNone(pipeline.file_manager)
        
        # Test initial state
        self.assertFalse(pipeline.is_running)
        self.assertTrue(pipeline.api_sending_enabled)
    
    def test_offline_engines_detection(self):
        """Test detection of offline engines"""
        # Test offline engine
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'sphinx'
        service = SpeechRecognitionService()
        self.assertTrue(service.is_offline_engine())
        
        # Test online engine
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'
        service = SpeechRecognitionService()
        self.assertFalse(service.is_offline_engine())
    
    def test_api_key_requirements(self):
        """Test API key requirement detection"""
        # Test engine that requires API key
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'wit'
        service = SpeechRecognitionService()
        self.assertTrue(service.requires_api_key())
        
        # Test engine that doesn't require API key
        os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'
        service = SpeechRecognitionService()
        self.assertFalse(service.requires_api_key())

class TestEngineAvailability(unittest.TestCase):
    """Test which engines are actually available"""
    
    def test_available_engines(self):
        """Test which speech recognition engines are available"""
        available_engines = []
        unavailable_engines = []
        
        # Test basic engines
        try:
            import speech_recognition
            available_engines.append("google")
        except ImportError:
            unavailable_engines.append("google")
        
        # Test optional engines
        optional_engines = {
            'sphinx': 'pocketsphinx',
            'vosk': 'vosk',
            'whisper_local': 'whisper',
            'faster_whisper': 'faster_whisper'
        }
        
        for engine, package in optional_engines.items():
            try:
                __import__(package)
                available_engines.append(engine)
            except ImportError:
                unavailable_engines.append(engine)
        
        print(f"\nAvailable engines: {available_engines}")
        print(f"Unavailable engines: {unavailable_engines}")
        
        # At minimum, Google should be available
        self.assertIn("google", available_engines)

def create_test_suite():
    """Create a comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTest(unittest.makeSuite(TestFullSystem))
    suite.addTest(unittest.makeSuite(TestEngineAvailability))
    
    return suite

def main():
    """Run the test suite"""
    print("WhisperSilent Full System Integration Test")
    print("=" * 50)
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())