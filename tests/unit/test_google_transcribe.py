#!/usr/bin/env python3
"""
Test script for Google Transcribe Service
This script tests the integration without requiring a real external API
"""

import os
import sys
import numpy as np
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from googleTranscribeService import GoogleTranscribeService
from transcriptionPipeline import TranscriptionPipeline

class TestGoogleTranscribe(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Set environment variables for testing
        os.environ['GOOGLE_TRANSCRIBE_ENABLED'] = 'true'
        os.environ['GOOGLE_TRANSCRIBE_ENDPOINT'] = 'https://fake-endpoint.com/transcribe'
        os.environ['GOOGLE_TRANSCRIBE_KEY'] = 'fake-api-key'
        os.environ['GOOGLE_TRANSCRIBE_LANGUAGE'] = 'pt-BR'
        
        # Reload config to pick up new environment variables
        import config
        import importlib
        importlib.reload(config)
        
    def test_config_loads_google_settings(self):
        """Test that Google transcription configuration is loaded correctly"""
        from config import Config
        self.assertTrue(Config.GOOGLE_TRANSCRIBE["enabled"])
        self.assertEqual(Config.GOOGLE_TRANSCRIBE["endpoint"], 'https://fake-endpoint.com/transcribe')
        self.assertEqual(Config.GOOGLE_TRANSCRIBE["key"], 'fake-api-key')
        self.assertEqual(Config.GOOGLE_TRANSCRIBE["language"], 'pt-BR')
        
    def test_google_service_initialization(self):
        """Test that GoogleTranscribeService initializes correctly"""
        service = GoogleTranscribeService()
        self.assertEqual(service.endpoint, 'https://fake-endpoint.com/transcribe')
        self.assertEqual(service.api_key, 'fake-api-key')
        self.assertEqual(service.language, 'pt-BR')
        
    def test_audio_to_wav_conversion(self):
        """Test audio array to WAV file conversion"""
        service = GoogleTranscribeService()
        
        # Create test audio data (1 second of 440Hz sine wave)
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        
        # Test WAV conversion
        wav_path = service._audio_to_wav(audio_data)
        self.assertTrue(os.path.exists(wav_path))
        self.assertTrue(wav_path.endswith('.wav'))
        
        # Cleanup
        service._cleanup_temp_files(wav_path)
        self.assertFalse(os.path.exists(wav_path))
        
    def test_wav_to_mp3_conversion(self):
        """Test WAV to MP3 conversion using ffmpeg"""
        service = GoogleTranscribeService()
        
        # Create test audio data
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        
        # Convert to WAV first
        wav_path = service._audio_to_wav(audio_data)
        
        # Test MP3 conversion
        mp3_path = service._wav_to_mp3(wav_path)
        self.assertTrue(os.path.exists(mp3_path))
        self.assertTrue(mp3_path.endswith('.mp3'))
        
        # Cleanup
        service._cleanup_temp_files(wav_path, mp3_path)
        self.assertFalse(os.path.exists(wav_path))
        self.assertFalse(os.path.exists(mp3_path))
        
    @patch('requests.post')
    def test_transcription_api_call(self, mock_post):
        """Test API call to external transcription service"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'transcription': 'Test transcription result'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        service = GoogleTranscribeService()
        
        # Create test audio data
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        
        # Test transcription
        result = service.transcribe(audio_data)
        
        # Verify results
        self.assertEqual(result, 'Test transcription result')
        self.assertTrue(mock_post.called)
        
        # Verify API call parameters
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer fake-api-key')
        self.assertIn('audio', call_args[1]['files'])
        self.assertEqual(call_args[1]['data']['language'], 'pt-BR')
        
    def test_pipeline_uses_google_service(self):
        """Test that TranscriptionPipeline uses GoogleTranscribeService when enabled"""
        from transcriptionPipeline import TranscriptionPipeline
        
        # Create pipeline
        pipeline = TranscriptionPipeline()
        
        # Verify it's using GoogleTranscribeService
        self.assertIsInstance(pipeline.transcription_service, GoogleTranscribeService)
        
    def test_cleanup_method(self):
        """Test cleanup method compatibility"""
        service = GoogleTranscribeService()
        # Should not raise any exceptions
        service.cleanup()

def run_integration_test():
    """Run a simple integration test"""
    print("Running Google Transcribe Integration Test...")
    print("=" * 50)
    
    # Test configuration
    print("1. Testing Configuration...")
    os.environ['GOOGLE_TRANSCRIBE_ENABLED'] = 'true'
    os.environ['GOOGLE_TRANSCRIBE_ENDPOINT'] = 'https://fake-endpoint.com/transcribe'
    
    # Reload config
    import config
    import importlib
    importlib.reload(config)
    from config import Config
    
    print(f"   Google Transcribe Enabled: {Config.GOOGLE_TRANSCRIBE['enabled']}")
    print(f"   Endpoint: {Config.GOOGLE_TRANSCRIBE['endpoint']}")
    print(f"   Language: {Config.GOOGLE_TRANSCRIBE['language']}")
    
    # Test service initialization
    print("\n2. Testing Service Initialization...")
    try:
        service = GoogleTranscribeService()
        print("   ✓ GoogleTranscribeService initialized successfully")
    except Exception as e:
        print(f"   ✗ Service initialization failed: {e}")
        return False
    
    # Test audio conversion
    print("\n3. Testing Audio Conversion...")
    try:
        # Create test audio
        sample_rate = 16000
        duration = 1
        t = np.linspace(0, duration, sample_rate * duration)
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767 * 0.1).astype(np.int16)
        
        # Test WAV conversion
        wav_path = service._audio_to_wav(audio_data)
        print(f"   ✓ WAV conversion successful: {wav_path}")
        
        # Test MP3 conversion
        mp3_path = service._wav_to_mp3(wav_path)
        print(f"   ✓ MP3 conversion successful: {mp3_path}")
        
        # Cleanup
        service._cleanup_temp_files(wav_path, mp3_path)
        print("   ✓ Cleanup successful")
        
    except Exception as e:
        print(f"   ✗ Audio conversion failed: {e}")
        return False
    
    # Test pipeline integration
    print("\n4. Testing Pipeline Integration...")
    try:
        from transcriptionPipeline import TranscriptionPipeline
        pipeline = TranscriptionPipeline()
        print(f"   ✓ Pipeline created with service: {type(pipeline.transcription_service).__name__}")
        
        if isinstance(pipeline.transcription_service, GoogleTranscribeService):
            print("   ✓ Pipeline correctly using GoogleTranscribeService")
        else:
            print("   ✗ Pipeline not using GoogleTranscribeService")
            return False
            
    except Exception as e:
        print(f"   ✗ Pipeline integration failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All tests passed! Google Transcribe integration is working.")
    return True

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'integration':
        # Run integration test
        success = run_integration_test()
        sys.exit(0 if success else 1)
    else:
        # Run unit tests
        unittest.main()