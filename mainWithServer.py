import os
import sys
import signal
import time
from dotenv import load_dotenv
from transcriptionPipeline import TranscriptionPipeline
from httpServer import TranscriptionHTTPServer
from logger import log
from config import Config

# Load environment variables from .env file
load_dotenv()

# Instantiate pipeline and server for global access
pipeline = TranscriptionPipeline()
http_server = None

def check_configuration():
    """Verifies that essential configurations are present."""
    api_endpoint = os.getenv('API_ENDPOINT')
    
    if not api_endpoint:
        log.warning("No API_ENDPOINT configured - API sending will be disabled")
        log.info("Set API_ENDPOINT in .env file to enable API functionality")
        # Disable API sending if no endpoint is configured
        pipeline.api_sending_enabled = False
    else:
        api_key = os.getenv('API_KEY')
        if not api_key:
            log.warning("No API_KEY configured - API requests may fail if authentication is required")
            log.info("Set API_KEY in .env file if your API requires authentication")

    model_path = Config.WHISPER["model_path"]
    if not os.path.exists(model_path):
        log.error(f"Whisper model not found: {model_path}")
        log.info("Run the setup script to download the model: python3 setup.py")
        return False
        
    return True

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info(f'Received signal {signal.Signals(sig).name}, shutting down...')
    
    # Stop HTTP server first
    if http_server:
        http_server.stop()
        
    # Stop pipeline
    if pipeline.is_running:
        pipeline.stop()

def handle_exception(exc_type, exc_value, exc_traceback):
    """Catches unhandled exceptions for logging and clean shutdown."""
    if issubclass(exc_type, KeyboardInterrupt):
        # KeyboardInterrupt is handled by the signal handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Unhandled exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Stop services
    if http_server:
        http_server.stop()
    if pipeline.is_running:
        pipeline.stop()
    sys.exit(1)

def main():
    """Main application function."""
    global http_server
    
    # Configure signal and exception handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.excepthook = handle_exception

    try:
        log.info('=== Real-Time Transcription System with HTTP API ===')
        log.info('Verifying configuration...')
        
        if not check_configuration():
            sys.exit(1)
        
        # Get HTTP server configuration
        http_host = os.getenv('HTTP_HOST', 'localhost')
        http_port = int(os.getenv('HTTP_PORT', 8080))
        
        # Start HTTP server
        log.info(f'Starting HTTP server on {http_host}:{http_port}...')
        http_server = TranscriptionHTTPServer(pipeline, http_host, http_port)
        http_server.start()
        
        log.info('Starting transcription pipeline...')
        pipeline.start()
        
        log.info('\n✅ System ready!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📝 Transcriptions will be stored locally and sent to API (if enabled)')
        log.info(f'🌐 HTTP API available at: {http_server.get_url()}')
        log.info('⏹️  Press Ctrl+C to stop\n')
        
        log.info('Available HTTP endpoints:')
        log.info(f'  Health Check: {http_server.get_url()}/health')
        log.info(f'  Transcriptions: {http_server.get_url()}/transcriptions')
        log.info(f'  API Documentation: {http_server.get_url()}/api-docs')
        log.info(f'  Control: {http_server.get_url()}/control/toggle-api-sending')
        log.info('')

        # Keep the main thread alive while services are running
        while pipeline.is_running:
            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info("Shutting down at user's request...")
    except Exception as e:
        log.error(f'Error starting application: {e}', exc_info=True)
    finally:
        # Ensure all services are stopped in any exit scenario
        if http_server:
            log.info("Stopping HTTP server...")
            http_server.stop()
            
        if pipeline.is_running:
            log.info("Finalizing transcription pipeline...")
            pipeline.stop()
            
        log.info("Application terminated.")
        sys.exit(0)

if __name__ == '__main__':
    main()