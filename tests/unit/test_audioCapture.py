import unittest
import sounddevice as sd
import numpy as np
import queue
import time
import os
import sys
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from audioCapture import AudioCapture
from config import Config
from logger import log

class TestAudioCapture(unittest.TestCase):

    def setUp(self):
        self.audio_capture = AudioCapture()
        # Reset Config values for consistent testing
        Config.AUDIO["sample_rate"] = 16000
        Config.AUDIO["channels"] = 1
        # Set a default device that can be found by name in the mock
        Config.AUDIO["device"] = "default_mic"

        # Clear log files before each test
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        for f in ['combined.log', 'error.log']:
            file_path = os.path.join(log_dir, f)
            if os.path.exists(file_path):
                os.remove(file_path)

    @patch('sounddevice.InputStream')
    @patch('sounddevice.query_devices')
    def test_start_success(self, mock_query_devices, mock_input_stream):
        # Mock query_devices to return a list of dictionaries when called without args
        # and a single dictionary when called with an integer (device_id)
        def query_devices_side_effect(device=None):
            if device is None:
                return [
                    {'name': 'default_mic', 'index': 0, 'max_input_channels': 1},
                    {'name': 'other_mic', 'index': 1, 'max_input_channels': 1}
                ]
            else:
                # Simulate finding the device by index
                if device == 0:
                    return {'name': 'default_mic', 'index': 0, 'max_input_channels': 1}
                raise sd.PortAudioError("Device not found")

        mock_query_devices.side_effect = query_devices_side_effect

        mock_input_stream_instance = MagicMock()
        mock_input_stream.return_value = mock_input_stream_instance

        with patch.dict('config.Config.AUDIO', {'device': 'default_mic'}):
            q = self.audio_capture.start()

        self.assertTrue(self.audio_capture.is_recording)
        mock_query_devices.assert_any_call() # Ensure query_devices was called without args
        mock_query_devices.assert_any_call(0) # Ensure query_devices was called with device_id
        mock_input_stream.assert_called_once_with(
            samplerate=Config.AUDIO["sample_rate"],
            channels=Config.AUDIO["channels"],
            device=0, # Should resolve to index 0 for 'default_mic'
            callback=self.audio_capture._callback,
            dtype='int16'
        )
        mock_input_stream_instance.start.assert_called_once()
        self.assertIsInstance(q, queue.Queue)
        # Check logs
        time.sleep(0.1) # Give time for logs to be written
        self.assertIn("Captura de áudio iniciada", self.read_log_file('combined.log'))

    @patch('sounddevice.InputStream')
    @patch('sounddevice.query_devices')
    def test_start_device_not_found(self, mock_query_devices, mock_input_stream):
        mock_query_devices.return_value = [] # Simulate no devices found

        with patch.dict('config.Config.AUDIO', {'device': 'non_existent_mic'}):
            with self.assertRaises(ValueError) as cm:
                self.audio_capture.start()
        
        self.assertFalse(self.audio_capture.is_recording)
        self.assertIn("Audio device 'non_existent_mic' not found.", str(cm.exception))
        self.assertIn("Audio device 'non_existent_mic' not found", self.read_log_file('error.log'))

    @patch('sounddevice.InputStream')
    @patch('sounddevice.query_devices')
    def test_stop(self, mock_query_devices, mock_input_stream):
        # Mock query_devices similar to test_start_success
        def query_devices_side_effect(device=None):
            if device is None:
                return [
                    {'name': 'default_mic', 'index': 0, 'max_input_channels': 1}
                ]
            else:
                if device == 0:
                    return {'name': 'default_mic', 'index': 0, 'max_input_channels': 1}
                raise sd.PortAudioError("Device not found")
        mock_query_devices.side_effect = query_devices_side_effect

        mock_input_stream_instance = MagicMock()
        mock_input_stream.return_value = mock_input_stream_instance

        with patch.dict('config.Config.AUDIO', {'device': 'default_mic'}):
            self.audio_capture.start()
            self.audio_capture.stop()

        self.assertFalse(self.audio_capture.is_recording)
        mock_input_stream_instance.stop.assert_called_once()
        mock_input_stream_instance.close.assert_called_once()
        self.assertIn("Captura de áudio parada", self.read_log_file('combined.log'))

    def test_callback_puts_data_in_queue(self):
        # Simulate data coming from sounddevice callback
        test_data = np.array([[1, 2], [3, 4]], dtype='int16')
        self.audio_capture._callback(test_data, 2, None, None)

        self.assertFalse(self.audio_capture.q.empty())
        retrieved_data = self.audio_capture.q.get()
        np.testing.assert_array_equal(retrieved_data, test_data)

    def test_get_audio_chunk_generator(self):
        self.audio_capture.is_recording = True # Manually set for generator test
        test_chunks = [np.array([1, 2]), np.array([3, 4])]
        for chunk in test_chunks:
            self.audio_capture.q.put(chunk)

        retrieved_chunks = []
        for i, chunk in enumerate(self.audio_capture.get_audio_chunk()):
            retrieved_chunks.append(chunk)
            if i == len(test_chunks) - 1:
                self.audio_capture.is_recording = False # Simulate end of recording

        self.assertEqual(len(retrieved_chunks), len(test_chunks))
        for i in range(len(test_chunks)):
            np.testing.assert_array_equal(retrieved_chunks[i], test_chunks[i])

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

if __name__ == '__main__':
    unittest.main()
