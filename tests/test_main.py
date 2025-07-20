import unittest
import os
import sys
import signal
from unittest.mock import patch, MagicMock

# Adjust path to import modules from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import check_configuration, main, pipeline
from config import Config
from logger import log

class TestMain(unittest.TestCase):

    def setUp(self):
        # Clear environment variables before each test
        for var in ['API_ENDPOINT', 'API_KEY']:
            if var in os.environ:
                del os.environ[var]

        # Create a dummy model file for testing existence checks
        self.test_models_dir = os.path.join(os.path.dirname(__file__), 'temp_models')
        os.makedirs(self.test_models_dir, exist_ok=True)
        self.dummy_model_path = os.path.join(self.test_models_dir, 'ggml-base.bin')
        with open(self.dummy_model_path, 'w') as f:
            f.write("dummy model content")
        Config.WHISPER["model_path"] = self.dummy_model_path

        # Mock logger to prevent actual logging during tests
        self.mock_logger_error = patch('logger.logger.error').start()
        self.mock_logger_info = patch('logger.logger.info').start()

        # Mock sys.exit to prevent actual exit during tests
        self.mock_sys_exit = patch('sys.exit').start()

        # Mock pipeline methods
        self.mock_pipeline_start = patch('main.pipeline.start').start()
        self.mock_pipeline_stop = patch('main.pipeline.stop').start()

    def tearDown(self):
        # Clean up dummy model file and directory
        if os.path.exists(self.dummy_model_path):
            os.remove(self.dummy_model_path)
        if os.path.exists(self.test_models_dir):
            os.rmdir(self.test_models_dir)

        # Stop all patches
        patch.stopall()

    def test_check_configuration_success(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        
        check_configuration()
        self.mock_sys_exit.assert_not_called()
        self.mock_logger_error.assert_not_called()

    def test_check_configuration_missing_api_endpoint(self):
        os.environ['API_KEY'] = 'test_key'
        
        check_configuration()
        self.mock_logger_error.assert_called_with("Variáveis de ambiente faltando: API_ENDPOINT")
        self.mock_sys_exit.assert_called_once_with(1)

    def test_check_configuration_missing_api_key(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        
        check_configuration()
        self.mock_logger_error.assert_called_with("Variáveis de ambiente faltando: API_KEY")
        self.mock_sys_exit.assert_called_once_with(1)

    def test_check_configuration_missing_model_path(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        os.remove(self.dummy_model_path) # Remove dummy model to simulate missing

        check_configuration()
        self.mock_logger_error.assert_called_with(f"Modelo Whisper não encontrado: {self.dummy_model_path}")
        self.mock_sys_exit.assert_called_once_with(1)

    @patch('time.sleep', MagicMock())
    def test_main_function_starts_pipeline(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'

        # To prevent infinite loop in main, we'll make pipeline.start() raise an exception after a short delay
        # or mock time.sleep to break the loop. Here, we mock time.sleep.
        # We also need to mock sys.exit for the normal exit path.
        self.mock_sys_exit.side_effect = SystemExit # Allow sys.exit to raise an exception for testing

        with self.assertRaises(SystemExit):
            main()

        self.mock_pipeline_start.assert_called_once()
        self.mock_logger_info.assert_any_call('✅ Sistema pronto!')

    @patch('time.sleep', MagicMock())
    def test_main_function_handles_exception(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        self.mock_pipeline_start.side_effect = Exception("Test Error")
        self.mock_sys_exit.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            main()

        self.mock_logger_error.assert_called_with('Erro ao iniciar aplicação: Test Error')
        self.mock_sys_exit.assert_called_once_with(1)

    @patch('time.sleep', MagicMock())
    def test_signal_handler_sigint(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        self.mock_sys_exit.side_effect = SystemExit

        # Simulate SIGINT
        with self.assertRaises(SystemExit):
            signal.getsignal(signal.SIGINT)(signal.SIGINT, None)

        self.mock_logger_info.assert_any_call('Recebido sinal 2, encerrando...') # SIGINT is usually 2
        self.mock_pipeline_stop.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(0)

    @patch('time.sleep', MagicMock())
    def test_signal_handler_sigterm(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        self.mock_sys_exit.side_effect = SystemExit

        # Simulate SIGTERM
        with self.assertRaises(SystemExit):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)

        self.mock_logger_info.assert_any_call('Recebido sinal 15, encerrando...') # SIGTERM is usually 15
        self.mock_pipeline_stop.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(0)

    @patch('time.sleep', MagicMock())
    def test_unhandled_exception_hook(self):
        os.environ['API_ENDPOINT'] = 'http://test.com'
        os.environ['API_KEY'] = 'test_key'
        self.mock_sys_exit.side_effect = SystemExit

        try:
            raise ValueError("Test Unhandled Exception")
        except ValueError:
            # Call the custom exception hook directly
            sys.excepthook(*sys.exc_info())

        self.mock_logger_error.assert_called_with("Erro não capturado:", exc_info=True)
        self.mock_pipeline_stop.assert_called_once()
        self.mock_sys_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main()
