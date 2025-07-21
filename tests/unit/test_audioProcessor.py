import unittest
import numpy as np
import queue
import time
from audioProcessor import AudioProcessor
from config import Config

class TestAudioProcessor(unittest.TestCase):

    def setUp(self):
        """Set up a new AudioProcessor instance before each test."""
        self.audio_queue = queue.Queue()
        self.processor = AudioProcessor(self.audio_queue)
        # Configure for testing
        Config.PROCESSING["silence_threshold"] = 100
        Config.PROCESSING["silence_duration_ms"] = 50
        Config.PROCESSING["buffer_size"] = 128
        Config.AUDIO["sample_rate"] = 16000

    def test_detect_silence(self):
        """Test that silence detection is accurate."""
        silent_frame = np.zeros(100, dtype=np.int16)
        non_silent_frame = np.full(100, 200, dtype=np.int16)
        self.assertTrue(self.processor.detect_silence(silent_frame))
        self.assertFalse(self.processor.detect_silence(non_silent_frame))

    def test_process_audio_yields_speech_chunk(self):
        """Test that the processor correctly yields a speech chunk after silence."""
        # Simulate non-silent audio followed by silence
        non_silent_data = np.full(Config.PROCESSING["buffer_size"], 300, dtype=np.int16)
        silent_data = np.zeros(Config.PROCESSING["buffer_size"], dtype=np.int16)

        self.audio_queue.put(non_silent_data)
        self.audio_queue.put(silent_data)
        self.audio_queue.put(silent_data) # Extra silence to trigger timeout

        processor_generator = self.processor.process_audio()

        # Allow time for silence detection
        time.sleep(Config.PROCESSING["silence_duration_ms"] / 1000 + 0.1)

        # The generator should yield one chunk
        try:
            chunk = next(processor_generator)
            self.assertIsInstance(chunk, np.ndarray)
            self.assertGreater(chunk.size, 0)
        except StopIteration:
            self.fail("Audio processor did not yield a chunk as expected.")

if __name__ == '__main__':
    unittest.main()