import os
import unittest
import time
import queue
import numpy as np
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from transcriptionPipeline import TranscriptionPipeline
from config import Config
from logger import log

class TestTranscriptionPipeline(unittest.TestCase):

    def setUp(self):
        # Mock dependencies
        self.mock_audio_capture = MagicMock()
        self.mock_audio_processor = MagicMock()
        self.mock_whisper_service = MagicMock()
        self.mock_api_service = MagicMock()

        # Patch the classes in the module where they are imported
        self.patcher_audio_capture = patch('transcriptionPipeline.AudioCapture', return_value=self.mock_audio_capture)
        self.patcher_audio_processor = patch('transcriptionPipeline.AudioProcessor', return_value=self.mock_audio_processor)
        self.patcher_whisper_service = patch('transcriptionPipeline.WhisperService', return_value=self.mock_whisper_service)
        self.patcher_api_service = patch('transcriptionPipeline.ApiService', return_value=self.mock_api_service)

        self.mock_audio_capture_cls = self.patcher_audio_capture.start()
        self.mock_audio_processor_cls = self.patcher_audio_processor.start()
        self.mock_whisper_service_cls = self.patcher_whisper_service.start()
        self.mock_api_service_cls = self.patcher_api_service.start()

        # Configure mock returns
        self.mock_audio_capture.start.return_value = queue.Queue() # Return a dummy queue
        self.mock_audio_processor.process_audio.return_value = iter([]) # Default to empty generator
        self.mock_whisper_service.transcribe.return_value = "Mocked Transcription"
        self.mock_api_service.send_transcription.return_value = None

        self.pipeline = TranscriptionPipeline()

    def tearDown(self):
        self.patcher_audio_capture.stop()
        self.patcher_audio_processor.stop()
        self.patcher_whisper_service.stop()
        self.patcher_api_service.stop()

    def test_start_pipeline_success(self):
        self.pipeline.start()

        self.assertTrue(self.pipeline.is_running)
        self.mock_audio_capture.start.assert_called_once()
        self.assertTrue(self.pipeline.processing_thread.is_alive())
        time.sleep(0.1) # Give time for logs to be written
        self.assertIn("Pipeline de transcrição iniciado com sucesso", self.read_log_file('combined.log'))

    def test_stop_pipeline(self):
        self.pipeline.start()
        self.pipeline.stop()

        self.assertFalse(self.pipeline.is_running)
        self.mock_audio_capture.stop.assert_called_once()
        self.mock_whisper_service.cleanup.assert_called_once()
        self.assertFalse(self.pipeline.processing_thread.is_alive())
        time.sleep(0.1) # Give time for logs to be written
        self.assertIn("Pipeline de transcrição parado", self.read_log_file('combined.log'))

    def test_process_audio_chunk_successful_transcription(self):
        # Simulate audio processor yielding a chunk
        mock_audio_chunk = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
        self.mock_audio_processor.process_audio.return_value = iter([mock_audio_chunk])

        # Start the pipeline and let the processing thread run briefly
        self.pipeline.start()
        time.sleep(0.1) # Give thread time to pick up the chunk
        self.pipeline.stop()

        self.mock_whisper_service.transcribe.assert_called_once_with(mock_audio_chunk)
        self.mock_api_service.send_transcription.assert_called_once()
        self.assertIn("Transcrição obtida em", self.read_log_file('combined.log'))

    def test_process_audio_chunk_no_transcription(self):
        self.mock_whisper_service.transcribe.return_value = "" # Simulate no transcription
        mock_audio_chunk = MagicMock()
        self.mock_audio_processor.process_audio.return_value = iter([mock_audio_chunk])

        self.pipeline.start()
        time.sleep(0.1)
        self.pipeline.stop()

        self.mock_whisper_service.transcribe.assert_called_once_with(mock_audio_chunk)
        self.mock_api_service.send_transcription.assert_not_called()
        self.assertIn("Nenhuma fala detectada no chunk", self.read_log_file('combined.log'))

    def test_process_audio_chunk_transcription_error(self):
        self.mock_whisper_service.transcribe.side_effect = Exception("Whisper Error")
        mock_audio_chunk = MagicMock()
        self.mock_audio_processor.process_audio.return_value = iter([mock_audio_chunk])

        self.pipeline.start()
        time.sleep(0.1)
        self.pipeline.stop()

        self.mock_whisper_service.transcribe.assert_called_once_with(mock_audio_chunk)
        self.mock_api_service.send_transcription.assert_not_called()
        self.assertIn("Erro ao processar chunk: Whisper Error", self.read_log_file('error.log'))

    def read_log_file(self, filename):
        log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', filename)
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                return f.read()
        return ""

    def tearDown(self):
        # Clean up log files after each test
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        for f in ['combined.log', 'error.log']:
            file_path = os.path.join(log_dir, f)
            if os.path.exists(file_path):
                os.remove(file_path)
        # Ensure the pipeline is stopped if it was started
        if self.pipeline.is_running:
            self.pipeline.stop()

if __name__ == '__main__':
    unittest.main()
