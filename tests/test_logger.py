import unittest
import os
import sys
import logging
import time
from unittest.mock import patch, MagicMock
from importlib import reload
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import logger after setting up path
import logger

class TestLogger(unittest.TestCase):

    def setUp(self):
        # Ensure logs directory exists and is empty before each test
        self.log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
        for f in os.listdir(self.log_dir):
            os.remove(os.path.join(self.log_dir, f))

        # Reload the logger module to ensure a clean state for each test
        # Remove existing handlers to prevent duplicate logs
        for handler in logger.log.handlers[:]:
            logger.log.removeHandler(handler)
            handler.close()
        reload(logger)

        self.combined_log_path = os.path.join(self.log_dir, 'combined.log')
        self.error_log_path = os.path.join(self.log_dir, 'error.log')

        # Create the logs directory before each test
        os.makedirs(self.log_dir, exist_ok=True)

    def tearDown(self):
        # Clean up log files after each test
        for f in os.listdir(self.log_dir):
            os.remove(os.path.join(self.log_dir, f))
        if os.path.exists(self.log_dir):
            os.rmdir(self.log_dir)

    def read_log_file(self, filename):
        log_path = os.path.join(self.log_dir, filename)
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                return f.read()
        return ""

    def test_info_logging(self):
        logger.log.info("This is an info message.")
        combined_log = self.read_log_file('combined.log')
        self.assertIn("INFO - This is an info message.", combined_log)
        self.assertEqual(self.read_log_file('error.log'), "")

    def test_error_logging(self):
        logger.log.error("This is an error message.")
        combined_log = self.read_log_file('combined.log')
        error_log = self.read_log_file('error.log')
        self.assertIn("ERROR - This is an error message.", combined_log)
        self.assertIn("ERROR - This is an error message.", error_log)

    def test_debug_logging(self):
        # Temporarily set level to DEBUG for this test
        original_level = logger.log.level
        logger.log.setLevel(logging.DEBUG)
        logger.log.debug("This is a debug message.")
        combined_log = self.read_log_file('combined.log')
        self.assertIn("DEBUG - This is a debug message.", combined_log) # Should be in combined because level is DEBUG
        logger.log.setLevel(original_level) # Reset level

    @patch('sys.stdout', new_callable=MagicMock)
    def test_console_logging(self, mock_stdout):
        logger.log.info("Console info message.")
        # Check if the console handler was called with the correct message
        # The actual call will include the level and a newline
        # We will check that the write method was called, and we can inspect the call args if needed
        time.sleep(0.1) # Give time for logs to be written
        self.assertTrue(mock_stdout.write.called)
        # Example of a more specific check:
        # self.assertIn("Console info message", mock_stdout.write.call_args[0][0])

    def test_log_rotation(self):
        # Set maxBytes to a small value to force rotation
        for handler in logger.log.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                handler.maxBytes = 100 # Small size to force rotation
                handler.backupCount = 1

        # Write enough logs to trigger rotation
        for i in range(10):
            logger.log.info(f"Test message {i}." * 10) # Make message long enough

        # Check if backup files are created
        self.assertTrue(os.path.exists(self.combined_log_path))
        self.assertTrue(os.path.exists(self.combined_log_path + '.1'))

if __name__ == '__main__':
    unittest.main()
