import unittest
from unittest.mock import patch, MagicMock
import requests
from apiService import ApiService
from config import Config

class TestApiService(unittest.TestCase):

    def setUp(self):
        """Set up a new ApiService instance and mock dependencies."""
        Config.API["endpoint"] = "http://fake-api.com/transcribe"
        Config.API["key"] = "fake_api_key"
        Config.API["retry_attempts"] = 2
        Config.API["retry_delay"] = 10 # ms
        self.service = ApiService()

    @patch('requests.post')
    def test_send_transcription_successful(self, mock_post):
        """Test successful sending of a transcription."""
        # Mock the requests.post call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_post.return_value = mock_response

        # Call the method
        result = self.service.send_transcription("hello world")

        # Assertions
        self.assertEqual(result, {"status": "success"})
        mock_post.assert_called_once()
        # Verify headers and data
        _, kwargs = mock_post.call_args
        self.assertIn('Authorization', kwargs['headers'])
        self.assertEqual(kwargs['headers']['Authorization'], f'Bearer {Config.API["key"]}')
        self.assertEqual(kwargs['json']['transcription'], "hello world")

    @patch('requests.post')
    def test_send_transcription_retry_and_fail(self, mock_post):
        """Test that the retry mechanism works and eventually fails."""
        # Mock the requests.post call to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")

        # Call the method and expect an exception
        with self.assertRaises(requests.exceptions.RequestException):
            self.service.send_transcription("this will fail")

        # Assert that the call was retried the correct number of times
        self.assertEqual(mock_post.call_count, Config.API["retry_attempts"])

if __name__ == '__main__':
    unittest.main()