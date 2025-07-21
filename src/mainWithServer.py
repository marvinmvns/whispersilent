import os
import sys
import signal
import time
from dotenv import load_dotenv

# Add module paths with higher priority
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

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
    log.info("🔍 Checking configuration...")
    
    api_endpoint = os.getenv('API_ENDPOINT')
    if not api_endpoint:
        log.warning("⚠️  No API_ENDPOINT configured - API sending will be disabled")
        log.info("💡 Set API_ENDPOINT in .env file to enable API functionality")
        # Disable API sending if no endpoint is configured
        pipeline.api_sending_enabled = False
    else:
        log.info(f"✅ API endpoint configured: {api_endpoint[:50]}...")
        api_key = os.getenv('API_KEY')
        if not api_key:
            log.warning("⚠️  No API_KEY configured - API requests may fail if authentication is required")
            log.info("💡 Set API_KEY in .env file if your API requires authentication")
        else:
            log.info("✅ API key configured")

    # Check speech recognition engine configuration
    engine = Config.SPEECH_RECOGNITION.get("engine", "google")
    log.info(f"🎯 Speech recognition engine: {engine}")
    
    if engine == "vosk":
        model_path = Config.SPEECH_RECOGNITION.get("vosk_model_path")
        if not model_path or not os.path.exists(model_path):
            log.error(f"❌ Vosk model not found: {model_path}")
            log.info("💡 Download a Vosk model and set VOSK_MODEL_PATH in .env file")
            return False
        log.info(f"✅ Vosk model found: {model_path}")
    
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
            log.warning(f"⚠️  Engine '{engine}' requires {required_var} to be set in .env file")
            log.info(f"💡 Falling back to 'google' engine if available")
        else:
            log.info(f"✅ Engine credentials configured for {engine}")
    
    log.info("✅ Configuration check completed")
    return True

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info(f'Received signal {signal.Signals(sig).name}, shutting down...')
    
    # Stop HTTP server first
    if 'http_server' in globals() and http_server:
        http_server.stop()
        
    # Stop pipeline
    if 'pipeline' in globals() and pipeline.is_running:
        pipeline.stop()
    
    sys.exit(0)

def handle_exception(exc_type, exc_value, exc_traceback):
    """Catches unhandled exceptions for logging and clean shutdown."""
    if issubclass(exc_type, KeyboardInterrupt):
        # KeyboardInterrupt is handled by the signal handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    log.error("Unhandled exception:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Stop services
    if 'http_server' in globals() and http_server:
        http_server.stop()
    if 'pipeline' in globals() and pipeline.is_running:
        pipeline.stop()
    sys.exit(1)

def main():
    """Main application function."""
    global http_server, pipeline
    
    # Configure signal and exception handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.excepthook = handle_exception

    try:
        log.info('🎤 REAL-TIME TRANSCRIPTION SYSTEM WITH HTTP API')
        log.info('='*60)
        log.info('🔍 Verifying configuration...')
        
        if not check_configuration():
            log.error('❌ Configuration check failed')
            sys.exit(1)
        
        # Get HTTP server configuration
        http_host = os.getenv('HTTP_HOST', 'localhost')
        http_port = int(os.getenv('HTTP_PORT', 8080))
        
        log.info(f'🌐 Starting HTTP server on {http_host}:{http_port}...')
        http_server = TranscriptionHTTPServer(pipeline, http_host, http_port)
        http_server.start()
        
        log.info(f'✅ HTTP server initialized')
        log.info(f'🎯 Engine: {Config.SPEECH_RECOGNITION.get("engine", "google")}')
        log.info(f'🌍 Language: {Config.SPEECH_RECOGNITION.get("language", "pt-BR")}')
        
        log.info('🚀 Starting transcription pipeline...')
        pipeline.start()
        
        log.info('\n' + '='*60)
        log.info('✅ SYSTEM READY!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📝 Transcriptions will be stored locally and sent to API (if enabled)')
        log.info(f'🌐 HTTP API available at: {http_server.get_url()}')
        log.info('⚠️  Use CTRL+C to stop')
        log.info('='*60)
        
        log.info('📋 Available HTTP endpoints:')
        log.info(f'   Health Check: {http_server.get_url()}/health')
        log.info(f'   Transcriptions: {http_server.get_url()}/transcriptions')
        log.info(f'   API Documentation: {http_server.get_url()}/api-docs')
        log.info(f'   Control: {http_server.get_url()}/control/toggle-api-sending')
        log.info('')
        
        # Keep the main thread alive while services are running
        start_time = time.time()
        last_status = start_time
        
        while pipeline.is_running:
            current_time = time.time()
            
            # Show status periodically
            if current_time - last_status > 30:  # Every 30 seconds
                uptime = current_time - start_time
                log.info(f'📊 [{uptime:.0f}s] System running - HTTP API active at {http_server.get_url()}')
                last_status = current_time
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info("\n⚡ Interrupted by user")
    except Exception as e:
        log.error(f'\n❌ Error starting application: {e}', exc_info=True)
    finally:
        # Ensure all services are stopped in any exit scenario
        if 'http_server' in globals() and http_server:
            log.info("🛑 Stopping HTTP server...")
            http_server.stop()
            
        if 'pipeline' in globals() and pipeline.is_running:
            log.info("🛑 Finalizing transcription pipeline...")
            pipeline.stop()
            
            # Show final stats if available
            if hasattr(pipeline, 'transcription_storage'):
                try:
                    stats = pipeline.transcription_storage.get_statistics()
                    log.info(f"\n📊 FINAL RESULTS:")
                    log.info(f"   Total transcriptions: {stats.get('total_transcriptions', 0)}")
                    log.info(f"   Successful: {stats.get('successful_transcriptions', 0)}")
                    log.info(f"   Errors: {stats.get('failed_transcriptions', 0)}")
                except Exception:
                    pass
            
        log.info("✅ Application terminated successfully!")

if __name__ == '__main__':
    main()