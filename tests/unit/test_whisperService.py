import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import os
from whisperService import WhisperService
from config import Config

class TestWhisperService(unittest.TestCase):

    @patch('os.path.exists', return_value=True)
    def setUp(self, mock_exists):
        """Set up a new WhisperService instance and mock dependencies."""
        # Ensure the temp directory exists
        os.makedirs(Config.PROCESSING["temp_dir"], exist_ok=True)
        self.service = WhisperService()

    @patch('subprocess.run')
    def test_transcribe_successful(self, mock_subprocess_run):
        """Test successful transcription of an audio buffer."""
        # Mock the subprocess call to whisper.cpp
        mock_result = MagicMock()
        mock_result.stdout = "This is a test transcription."
        mock_result.stderr = ""
        mock_result.check_returncode.return_value = None
        mock_subprocess_run.return_value = mock_result

        # Create a dummy audio buffer
        audio_buffer = np.zeros(16000, dtype=np.int16)

        # Transcribe
        transcription = self.service.transcribe(audio_buffer)

        # Assertions
        self.assertEqual(transcription, "This is a test transcription.")
        mock_subprocess_run.assert_called_once()
        # Verify that the temp file was created and then cleaned up
        args, _ = mock_subprocess_run.call_args
        temp_file_path = args[0][args[0].index('-f') + 1]
        self.assertFalse(os.path.exists(temp_file_path))

    def test_save_as_wav(self):
        """Test that a WAV file is saved correctly."""
        audio_data = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
        file_path = os.path.join(Config.PROCESSING["temp_dir"], "test_output.wav")
        
        self.service.save_as_wav(audio_data, file_path)
        
        self.assertTrue(os.path.exists(file_path))
        # Optional: could also read the file back and verify its properties
        
        # Cleanup
        os.remove(file_path)

if __name__ == '__main__':
    unittest.main()