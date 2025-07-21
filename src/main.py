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
from logger import log
from config import Config

# Load environment variables from .env file
load_dotenv()

# Instantiate pipeline for global access
pipeline = TranscriptionPipeline()

def check_configuration():
    """Verifies that essential configurations are present."""
    log.info("🔍 Checking configuration...")
    
    api_endpoint = os.getenv('API_ENDPOINT')
    if not api_endpoint:
        log.warning("⚠️  No API_ENDPOINT configured - API sending will be disabled")
        log.info("💡 Set API_ENDPOINT in .env file to enable API functionality")
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
            sys.exit(1)
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

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info(f'Received signal {signal.Signals(sig).name}, shutting down...')
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
    if 'pipeline' in globals() and pipeline.is_running:
        pipeline.stop()
    sys.exit(1)

def main():
    """Main application function."""
    global pipeline
    
    # Configure signal and exception handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.excepthook = handle_exception

    try:
        log.info('🎤 REAL-TIME TRANSCRIPTION SYSTEM')
        log.info('='*50)
        log.info('🔍 Verifying configuration...')
        check_configuration()
        
        log.info(f'✅ Configuration verified')
        log.info(f'🎯 Engine: {Config.SPEECH_RECOGNITION.get("engine", "google")}')
        log.info(f'🌍 Language: {Config.SPEECH_RECOGNITION.get("language", "pt-BR")}')
        
        log.info('🚀 Starting transcription pipeline...')
        pipeline.start()
        
        log.info('\n' + '='*50)
        log.info('✅ SYSTEM READY!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📝 Transcriptions will be sent to your API')
        log.info('⚠️  Use CTRL+C to stop')
        log.info('='*50)
        log.info('')

        # Keep the main thread alive while the pipeline is running
        start_time = time.time()
        last_status = start_time
        
        while pipeline.is_running:
            current_time = time.time()
            
            # Show status periodically
            if current_time - last_status > 30:  # Every 30 seconds
                uptime = current_time - start_time
                log.info(f'📊 [{uptime:.0f}s] System running - Pipeline active')
                last_status = current_time
            
            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info("\n⚡ Interrupted by user")
    except Exception as e:
        log.error(f'\n❌ Error starting application: {e}', exc_info=True)
    finally:
        # Ensure the pipeline is stopped in any exit scenario
        if 'pipeline' in globals() and pipeline.is_running:
            log.info("🛑 Finalizing pipeline...")
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