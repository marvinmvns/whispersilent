import os
import sys
import signal
import time
from dotenv import load_dotenv

# Add module paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'transcription'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from transcriptionPipeline import TranscriptionPipeline
from logger import log
from config import Config

# Load environment variables from .env file
load_dotenv()

# Instantiate pipeline for global access
pipeline = TranscriptionPipeline()

def check_configuration():
    """Verifies that essential configurations are present."""
    api_endpoint = os.getenv('API_ENDPOINT')
    
    if not api_endpoint:
        log.warning("No API_ENDPOINT configured - API sending will be disabled")
        log.info("Set API_ENDPOINT in .env file to enable API functionality")
    else:
        api_key = os.getenv('API_KEY')
        if not api_key:
            log.warning("No API_KEY configured - API requests may fail if authentication is required")
            log.info("Set API_KEY in .env file if your API requires authentication")

    # Check speech recognition engine configuration
    engine = Config.SPEECH_RECOGNITION.get("engine", "google")
    log.info(f"Configured speech recognition engine: {engine}")
    
    if engine == "vosk":
        model_path = Config.SPEECH_RECOGNITION.get("vosk_model_path")
        if not model_path or not os.path.exists(model_path):
            log.error(f"Vosk model not found: {model_path}")
            log.info("Download a Vosk model and set VOSK_MODEL_PATH in .env file")
            sys.exit(1)
    
    # Check for API keys if using online services
    online_engines = {
        "google_cloud": "GOOGLE_CLOUD_CREDENTIALS_JSON",
        "wit": "WIT_AI_KEY", 
        "azure": "AZURE_SPEECH_KEY",
        "houndify": "HOUNDIFY_CLIENT_ID",
        "ibm": "IBM_SPEECH_USERNAME",
        "whisper_api": "OPENAI_API_KEY",
        "groq": "GROQ_API_KEY",
        "custom_endpoint": "CUSTOM_SPEECH_ENDPOINT"
    }
    
    if engine in online_engines:
        required_var = online_engines[engine]
        if not os.getenv(required_var):
            log.warning(f"Engine '{engine}' requires {required_var} to be set in .env file")
            log.info(f"Falling back to 'google' engine if available")

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info(f'Received signal {signal.Signals(sig).name}, shutting down...')
    if pipeline.is_running:
        pipeline.stop()

def handle_exception(exc_type, exc_value, exc_traceback):
    """Catches unhandled exceptions for logging and clean shutdown."""
    if issubclass(exc_type, KeyboardInterrupt):
        # KeyboardInterrupt is handled by the signal handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Unhandled exception:", exc_info=(exc_type, exc_value, exc_traceback))
    if pipeline.is_running:
        pipeline.stop()
    sys.exit(1)

def main():
    """Main application function."""
    # Configure signal and exception handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.excepthook = handle_exception

    try:
        log.info('=== Real-Time Transcription System ===')
        log.info('Verifying configuration...')
        check_configuration()
        
        log.info('Starting application...')
        pipeline.start()
        
        log.info('\n✅ System ready!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📝 Transcriptions will be sent to your API')
        log.info('⏹️  Press Ctrl+C to stop\n')

        # Keep the main thread alive while the pipeline is running
        while pipeline.is_running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info("Shutting down at user's request...")
    except Exception as e:
        log.error(f'Error starting application: {e}', exc_info=True)
    finally:
        # Ensure the pipeline is stopped in any exit scenario
        if pipeline.is_running:
            log.info("Finalizing pipeline...")
            pipeline.stop()
        log.info("Application terminated.")
        sys.exit(0)

if __name__ == '__main__':
    main()