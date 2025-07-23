#!/usr/bin/env python3
"""
WhisperSilent Advanced Mode - Complete Implementation
Uses full TranscriptionPipeline with all advanced features:
- HealthMonitor with system metrics
- TranscriptionStorage for advanced data management  
- API WebSocket real-time streaming
- Hourly aggregation system
- Speaker identification
- Complete HTTP API
"""

import os
import sys
import signal
import time
import asyncio
import threading
from datetime import datetime
from dotenv import load_dotenv

# Add module paths with higher priority
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

from transcription.transcriptionPipeline import TranscriptionPipeline
from api.httpServer import TranscriptionHTTPServer
from api.realtimeAPI import RealtimeTranscriptionAPI
from services.hourlyAggregator import HourlyAggregator
from services.speakerIdentification import SpeakerIdentificationService
from logger import log
from config import Config

# Load environment variables from .env file
load_dotenv()

# Global variables for graceful shutdown
pipeline = None
http_server = None
realtime_api = None
hourly_aggregator = None

def check_configuration():
    """Verify that all required configuration is in place"""
    engine = Config.SPEECH_RECOGNITION.get("engine", "").lower()
    
    if not engine or engine == "disabled":
        log.error("❌ No speech recognition engine configured")
        log.info("💡 Set SPEECH_RECOGNITION_ENGINE in .env file (google, vosk, etc.)")
        return False
    
    # Check model files for offline engines
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
            log.debug(f"💡 Falling back to 'google' engine if available")
        else:
            log.debug(f"✅ Engine credentials configured for {engine}")
    
    log.debug("✅ Configuration check completed")
    return True

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info("Received signal SIGTERM, shutting down...")
    
    global pipeline, http_server, realtime_api, hourly_aggregator
    
    # Stop real-time API first
    if realtime_api:
        log.info("🛑 Stopping real-time API...")
        realtime_api.stop()
    
    # Stop HTTP server
    if http_server:
        log.info("🛑 Stopping HTTP server...")
        http_server.stop()
    
    # Stop hourly aggregator
    if hourly_aggregator:
        log.info("🛑 Stopping hourly aggregator...")
        hourly_aggregator.stop()
    
    # Stop pipeline last
    if pipeline and pipeline.is_running:
        log.info("🛑 Stopping transcription pipeline...")
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
    global pipeline, http_server, realtime_api, hourly_aggregator
    if http_server:
        http_server.stop()
    if realtime_api:
        realtime_api.stop()
    if hourly_aggregator:
        hourly_aggregator.stop()
    if pipeline and pipeline.is_running:
        pipeline.stop()
    sys.exit(1)

# Function removed - WebSocket API is started directly in main()

def main():
    """Main application function with all advanced features."""
    global pipeline, http_server, realtime_api, hourly_aggregator
    
    # Configure signal and exception handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    sys.excepthook = handle_exception

    try:
        log.info('🚀 WHISPERSILENT ADVANCED MODE - COMPLETE IMPLEMENTATION')
        log.info('='*70)
        log.info('🔍 Verifying configuration...')
        
        if not check_configuration():
            log.error('❌ Configuration check failed')
            sys.exit(1)
        
        # Initialize complete transcription pipeline
        log.info('🏗️  Initializing advanced transcription pipeline...')
        pipeline = TranscriptionPipeline()
        
        # Initialize hourly aggregator
        log.info('📊 Initializing hourly aggregation system...')
        hourly_aggregator = HourlyAggregator(pipeline.transcription_storage)
        hourly_aggregator.start()
        
        # Get HTTP server configuration from Config
        http_host = Config.HTTP_SERVER["host"]
        http_port = Config.HTTP_SERVER["port"]
        
        log.info(f'🌐 Starting advanced HTTP server on {http_host}:{http_port}...')
        # Use the full HTTP server with all advanced features
        http_server = TranscriptionHTTPServer(pipeline, http_host, http_port)
        http_server.start()
        
        log.info(f'✅ Advanced HTTP server started on {http_host}:{http_port}')
        log.info(f'🎯 Engine: {pipeline.transcription_service.__class__.__name__}')
        
        # Start real-time WebSocket API if enabled
        if os.getenv("REALTIME_API_ENABLED", "false").lower() == "true":
            log.info('🔌 Starting real-time WebSocket API...')
            # Initialize and start real-time API directly
            port = int(os.getenv("REALTIME_WEBSOCKET_PORT", "8081"))
            realtime_api = RealtimeTranscriptionAPI(pipeline)
            realtime_api.start()
            log.info(f"✅ WebSocket API started on port {port}")
        
        log.info('🚀 Starting transcription pipeline...')
        pipeline.start()
        
        log.info('')
        log.info('='*70)
        log.info('✅ ADVANCED SYSTEM READY!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📊 System metrics and health monitoring active')
        log.info('🌐 Complete HTTP API available at: http://{}:{}'.format(http_host, http_port))
        if os.getenv("REALTIME_API_ENABLED", "false").lower() == "true":
            log.info('🔌 Real-time WebSocket API available at: ws://{}:{}'.format(http_host, int(os.getenv("REALTIME_WEBSOCKET_PORT", "8081"))))
        log.info('📋 API Documentation: http://{}:{}/api-docs'.format(http_host, http_port))
        log.info('⚠️  Use CTRL+C to stop')
        log.info('='*70)
        
        # Keep the main thread alive while pipeline runs
        try:
            while pipeline.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Keyboard interrupt received. Stopping...")
            pass
        
    except KeyboardInterrupt:
        log.info("🛑 Keyboard interrupt received. Stopping...")
    except Exception as e:
        log.error(f"❌ Critical error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if realtime_api:
            log.info("🛑 Stopping real-time API...")
            realtime_api.stop()
        
        if http_server:
            log.info("🛑 Stopping HTTP server...")
            http_server.stop()
        
        if hourly_aggregator:
            log.info("🛑 Stopping hourly aggregator...")
            hourly_aggregator.stop()
        
        if pipeline and pipeline.is_running:
            log.info("🛑 Stopping pipeline...")
            pipeline.stop()
        
        log.info("✅ Advanced application terminated successfully!")

if __name__ == "__main__":
    main()