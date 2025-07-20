import unittest
import os
import sys
from unittest.mock import patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Config after setting up path
import config

class TestConfig(unittest.TestCase):

    def setUp(self):
        # Reload config module to ensure fresh state for each test
        # This is crucial because module-level imports are cached
        from importlib import reload
        reload(config)
        from config import Config as ReloadedConfig
        self.Config = ReloadedConfig

        # Clear any existing environment variables that might interfere
        for key in ["SAMPLE_RATE", "CHANNELS", "WHISPER_MODEL_PATH", "API_ENDPOINT", "API_KEY", "CHUNK_DURATION_MS", "SILENCE_THRESHOLD", "SILENCE_DURATION_MS", "ENABLE_GPU"]:
            if key in os.environ:
                del os.environ[key]

    def test_default_audio_config(self):
        self.assertEqual(self.Config.AUDIO["sample_rate"], 16000)
        self.assertEqual(self.Config.AUDIO["channels"], 1)
        self.assertEqual(self.Config.AUDIO["device"], "plughw:2,0")

    def test_env_audio_config(self):
        os.environ["SAMPLE_RATE"] = "8000"
        os.environ["CHANNELS"] = "2"
        from importlib import reload
        reload(config)
        from config import Config as ReloadedConfig
        self.assertEqual(ReloadedConfig.AUDIO["sample_rate"], 8000)
        self.assertEqual(ReloadedConfig.AUDIO["channels"], 2)

    def test_default_whisper_config(self):
        # Ensure the dummy model path is used for default test
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        expected_model_path = os.path.join(project_root, 'models', 'ggml-base.bin')
        self.assertEqual(self.Config.WHISPER["model_path"], expected_model_path)
        self.assertEqual(self.Config.WHISPER["language"], "pt")
        self.assertFalse(self.Config.WHISPER["enable_gpu"])

    def test_env_whisper_config(self):
        os.environ["WHISPER_LANGUAGE"] = "en"
        os.environ["ENABLE_GPU"] = "true"
        from importlib import reload
        reload(config)
        from config import Config as ReloadedConfig
        self.assertEqual(ReloadedConfig.WHISPER["language"], "en")
        self.assertTrue(ReloadedConfig.WHISPER["enable_gpu"])

    def test_default_api_config(self):
        self.assertIsNone(self.Config.API["endpoint"])
        self.assertIsNone(self.Config.API["key"])
        self.assertEqual(self.Config.API["timeout"], 30000)

    def test_env_api_config(self):
        os.environ["API_ENDPOINT"] = "http://test.com"
        os.environ["API_KEY"] = "test_key"
        from importlib import reload
        reload(config)
        from config import Config as ReloadedConfig
        self.assertEqual(ReloadedConfig.API["endpoint"], "http://test.com")
        self.assertEqual(ReloadedConfig.API["key"], "test_key")

    def test_default_processing_config(self):
        self.assertEqual(self.Config.PROCESSING["chunk_duration_ms"], 3000)
        self.assertEqual(self.Config.PROCESSING["silence_threshold"], 500)
        self.assertEqual(self.Config.PROCESSING["silence_duration_ms"], 1500)

    def test_env_processing_config(self):
        os.environ["CHUNK_DURATION_MS"] = "1000"
        os.environ["SILENCE_THRESHOLD"] = "600"
        os.environ["SILENCE_DURATION_MS"] = "1000"
        from importlib import reload
        reload(config)
        from config import Config as ReloadedConfig
        self.assertEqual(ReloadedConfig.PROCESSING["chunk_duration_ms"], 1000)
        self.assertEqual(ReloadedConfig.PROCESSING["silence_threshold"], 600)
        self.assertEqual(ReloadedConfig.PROCESSING["silence_duration_ms"], 1000)

if __name__ == '__main__':
    unittest.main()