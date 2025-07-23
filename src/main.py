#!/usr/bin/env python3
"""
WhisperSilent - Unified Real-Time Transcription System
=====================================================

A comprehensive real-time audio transcription system with multiple operation modes:

MODES:
- AUTO: Automatically detects best mode based on system capabilities
- ADVANCED: Full pipeline with all features (HealthMonitor, WebSocket, Aggregation)
- BASIC: Simple JSON transcriber with basic HTTP API
- SIMPLE: Command-line only transcription without HTTP API

FEATURES:
- 🎤 Real-time audio transcription with 12+ speech recognition engines
- 🌐 Complete REST API with Swagger documentation
- 🔌 WebSocket real-time streaming API
- 📊 System health monitoring with performance metrics
- 📈 Hourly aggregation system with silence gap detection
- 🔄 Automatic online/offline fallback
- 🎯 Speaker identification support
- 📱 Multiple output formats (JSON, files, API)

USAGE:
    python3 main.py [MODE] [OPTIONS]
    
    MODE:
        auto     - Auto-detect best mode (default)
        advanced - Full feature set with all components
        basic    - JSON transcriber with HTTP API
        simple   - Command-line only transcription
        
    OPTIONS:
        --interactive  - Show interactive mode selection
        --config      - Show current configuration
        --test        - Run system validation tests
        --help        - Show this help message

EXAMPLES:
    python3 main.py                    # Auto-detect best mode
    python3 main.py advanced           # Force advanced mode
    python3 main.py --interactive      # Choose mode interactively
    python3 main.py --config          # Show configuration
    python3 main.py --test            # Run validation tests
"""

import os
import sys
import signal
import time
import argparse
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add module paths with higher priority
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

from logger import log
from config import Config

# Load environment variables
load_dotenv()

# Global variables for graceful shutdown
current_app = None
current_mode = None

class WhisperSilentApp:
    """Unified WhisperSilent application with multiple operation modes"""
    
    def __init__(self):
        self.mode = None
        self.pipeline = None
        self.http_server = None
        self.realtime_api = None
        self.hourly_aggregator = None
        self.json_transcriber = None
        self.simple_transcriber = None
        
    def detect_optimal_mode(self) -> str:
        """Automatically detect the best mode based on system capabilities"""
        log.info("🔍 Auto-detecting optimal operation mode...")
        
        # Check system resources
        try:
            import psutil
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)
            log.debug(f"System: {cpu_count} CPUs, {memory_gb:.1f}GB RAM")
        except ImportError:
            cpu_count = 2
            memory_gb = 4.0
            log.debug("psutil not available, assuming minimal system")
        
        # Check if all dependencies are available
        try:
            # Test advanced mode dependencies
            from transcription.transcriptionPipeline import TranscriptionPipeline
            from api.httpServer import TranscriptionHTTPServer
            from api.realtimeAPI import RealtimeTranscriptionAPI
            from services.hourlyAggregator import HourlyAggregator
            advanced_available = True
            log.debug("✅ Advanced mode dependencies available")
        except Exception as e:
            advanced_available = False
            log.debug(f"❌ Advanced mode dependencies missing: {e}")
        
        try:
            # Test basic mode dependencies
            from transcription.jsonTranscriber import JsonTranscriber
            basic_available = True
            log.debug("✅ Basic mode dependencies available")
        except Exception as e:
            basic_available = False
            log.debug(f"❌ Basic mode dependencies missing: {e}")
        
        # Decision logic
        if advanced_available and memory_gb >= 4.0 and cpu_count >= 2:
            mode = "advanced"
            reason = f"System capable ({cpu_count} CPUs, {memory_gb:.1f}GB RAM) and all dependencies available"
        elif basic_available:
            mode = "basic"
            reason = "Basic dependencies available, using JSON transcriber mode"
        else:
            mode = "simple"
            reason = "Minimal dependencies, using simple command-line mode"
        
        log.info(f"🎯 Auto-selected mode: {mode.upper()}")
        log.info(f"📋 Reason: {reason}")
        
        return mode
    
    def show_interactive_selection(self) -> str:
        """Show interactive mode selection"""
        print("\n" + "="*60)
        print("🎤 WHISPERSILENT - MODE SELECTION")
        print("="*60)
        print("\nAvailable operation modes:")
        print("\n1. 🚀 ADVANCED - Complete feature set")
        print("   • Full TranscriptionPipeline with all components")
        print("   • Real-time WebSocket API (ws://localhost:8081)")
        print("   • System health monitoring with performance metrics")
        print("   • Hourly aggregation with silence gap detection")
        print("   • Advanced HTTP API (25+ endpoints)")
        print("   • Automatic online/offline fallback")
        print("   • Speaker identification support")
        
        print("\n2. 📝 BASIC - JSON transcriber with HTTP API")
        print("   • JsonTranscriber with real-time transcription")
        print("   • HTTP API server (http://localhost:8080)")
        print("   • JSON file output with session management")
        print("   • Basic health monitoring")
        print("   • 12 endpoints available")
        
        print("\n3. 💻 SIMPLE - Command-line only")
        print("   • Direct transcription to console")
        print("   • No HTTP API or WebSocket")
        print("   • Minimal resource usage")
        print("   • Basic file output")
        
        print("\n4. 🤖 AUTO - Automatic detection")
        print("   • System analyzes capabilities")
        print("   • Selects optimal mode automatically")
        print("   • Recommended for most users")
        
        while True:
            try:
                choice = input("\nSelect mode (1-4) or 'q' to quit: ").strip().lower()
                
                if choice == 'q':
                    print("👋 Goodbye!")
                    sys.exit(0)
                elif choice == '1':
                    return 'advanced'
                elif choice == '2':
                    return 'basic'
                elif choice == '3':
                    return 'simple'
                elif choice == '4':
                    return 'auto'
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, 4, or 'q'")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def validate_configuration(self) -> bool:
        """Validate system configuration for the selected mode"""
        log.info("🔍 Validating configuration...")
        
        # Check speech recognition engine
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
        
        # Check API keys for online engines
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
                log.debug(f"💡 Will fallback to 'google' engine if available")
            else:
                log.debug(f"✅ Engine credentials configured for {engine}")
        
        # Validate mode-specific requirements
        if self.mode == "advanced":
            # Check advanced mode dependencies
            required_features = [
                ("HealthMonitor", "services.healthMonitor"),
                ("TranscriptionStorage", "transcription.transcriptionStorage"),
                ("HourlyAggregator", "services.hourlyAggregator"),
                ("RealtimeAPI", "api.realtimeAPI")
            ]
            
            for feature_name, module_name in required_features:
                try:
                    __import__(module_name)
                    log.debug(f"✅ {feature_name} available")
                except ImportError as e:
                    log.error(f"❌ {feature_name} not available: {e}")
                    return False
        
        log.info("✅ Configuration validation completed")
        return True
    
    def start_advanced_mode(self):
        """Start advanced mode with full pipeline and all features"""
        log.info("🚀 Starting ADVANCED mode - Complete feature set")
        
        try:
            from transcription.transcriptionPipeline import TranscriptionPipeline
            from api.httpServer import TranscriptionHTTPServer
            from api.realtimeAPI import RealtimeTranscriptionAPI
            from services.hourlyAggregator import HourlyAggregator
        except ImportError as e:
            log.error(f"❌ Failed to import advanced components: {e}")
            log.info("💡 Falling back to basic mode...")
            return self.start_basic_mode()
        
        # Initialize complete transcription pipeline
        log.info("🏗️  Initializing advanced transcription pipeline...")
        self.pipeline = TranscriptionPipeline()
        
        # Initialize hourly aggregator
        if os.getenv("HOURLY_AGGREGATION_ENABLED", "true").lower() == "true":
            log.info("📊 Initializing hourly aggregation system...")
            self.hourly_aggregator = HourlyAggregator(self.pipeline.api_service)
            self.hourly_aggregator.start()
        
        # Start HTTP server with advanced features
        http_host = Config.HTTP_SERVER["host"]
        http_port = Config.HTTP_SERVER["port"]
        
        log.info(f"🌐 Starting advanced HTTP server on {http_host}:{http_port}...")
        self.http_server = TranscriptionHTTPServer(self.pipeline, http_host, http_port)
        self.http_server.start()
        
        # Start real-time WebSocket API if enabled
        if os.getenv("REALTIME_API_ENABLED", "false").lower() == "true":
            log.info("🔌 Starting real-time WebSocket API...")
            port = int(os.getenv("REALTIME_WEBSOCKET_PORT", "8081"))
            self.realtime_api = RealtimeTranscriptionAPI(self.pipeline)
            self.realtime_api.start()
            log.info(f"✅ WebSocket API started on port {port}")
        
        # Start transcription pipeline
        log.info("🚀 Starting transcription pipeline...")
        self.pipeline.start()
        
        # Show status
        log.info("")
        log.info("="*70)
        log.info("✅ ADVANCED MODE READY!")
        log.info("🎤 Speak into the microphone to transcribe")
        log.info("📊 System metrics and health monitoring active")
        log.info(f"🌐 Complete HTTP API: http://{http_host}:{http_port}")
        log.info(f"📋 API Documentation: http://{http_host}:{http_port}/api-docs")
        if os.getenv("REALTIME_API_ENABLED", "false").lower() == "true":
            realtime_port = int(os.getenv("REALTIME_WEBSOCKET_PORT", "8081"))
            log.info(f"🔌 Real-time WebSocket: ws://{http_host}:{realtime_port}")
        log.info("⚠️  Use CTRL+C to stop")
        log.info("="*70)
        
        # Keep running
        try:
            while self.pipeline.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Keyboard interrupt received. Stopping...")
    
    def start_basic_mode(self):
        """Start basic mode with JSON transcriber and HTTP API"""
        log.info("📝 Starting BASIC mode - JSON transcriber with HTTP API")
        
        try:
            from transcription.jsonTranscriber import JsonTranscriber
        except ImportError as e:
            log.error(f"❌ Failed to import JsonTranscriber: {e}")
            log.info("💡 Falling back to simple mode...")
            return self.start_simple_mode()
        
        # Import the simple HTTP server
        import mainWithServer
        
        # Initialize JSON transcriber
        output_file = "transcriptions_unified.json"
        log.info(f"📄 Output file: {output_file}")
        
        self.json_transcriber = JsonTranscriber(output_file)
        
        # Start HTTP server
        http_host = Config.HTTP_SERVER["host"]
        http_port = Config.HTTP_SERVER["port"]
        
        log.info(f"🌐 Starting basic HTTP server on {http_host}:{http_port}...")
        self.http_server = mainWithServer.SimpleTranscriptionHTTPServer(
            self.json_transcriber, http_host, http_port
        )
        self.http_server.start()
        
        # Start transcription
        log.info("🚀 Starting JSON transcriber...")
        self.json_transcriber.start()
        
        # Show status
        log.info("")
        log.info("="*60)
        log.info("✅ BASIC MODE READY!")
        log.info("🎤 Speak into the microphone to transcribe")
        log.info("📝 Transcriptions stored in JSON format")
        log.info(f"🌐 HTTP API: http://{http_host}:{http_port}")
        log.info(f"📋 API Documentation: http://{http_host}:{http_port}/api-docs")
        log.info("⚠️  Use CTRL+C to stop")
        log.info("="*60)
        
        # Keep running
        try:
            while self.json_transcriber.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("🛑 Keyboard interrupt received. Stopping...")
    
    def start_simple_mode(self):
        """Start simple mode with command-line only transcription"""
        log.info("💻 Starting SIMPLE mode - Command-line transcription")
        
        try:
            from core.audioCapture import AudioCapture
            from core.audioProcessor import AudioProcessor
            from transcription.speechRecognitionService import SpeechRecognitionService
        except ImportError as e:
            log.error(f"❌ Failed to import required components: {e}")
            log.error("❌ Cannot start any mode. Please check installation.")
            sys.exit(1)
        
        # Initialize components
        audio_capture = AudioCapture()
        audio_processor = AudioProcessor(audio_capture.q)
        speech_service = SpeechRecognitionService()
        
        log.info("🎤 Simple transcription started")
        log.info("💬 Transcriptions will be displayed in console")
        log.info("⚠️  Use CTRL+C to stop")
        log.info("-" * 50)
        
        # Start audio capture
        try:
            chunk_count = 0
            for audio_chunk in audio_processor.process_audio():
                if audio_chunk is not None and audio_chunk.size > 0:
                    chunk_count += 1
                    start_time = time.time()
                    
                    try:
                        transcription = speech_service.transcribe_audio(audio_chunk)
                        if transcription and transcription.strip():
                            processing_time = (time.time() - start_time) * 1000
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[{timestamp}] ({processing_time:.0f}ms): {transcription}")
                        else:
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] (silence)")
                    except Exception as e:
                        print(f"❌ Transcription error: {e}")
                        
        except KeyboardInterrupt:
            log.info("🛑 Stopping simple transcription...")
        finally:
            audio_capture.stop()
            log.info(f"✅ Simple mode stopped. Processed {chunk_count} audio chunks.")
    
    def run(self, mode: str = "auto"):
        """Run the application in the specified mode"""
        global current_app, current_mode
        current_app = self
        current_mode = mode
        
        try:
            # Detect mode if auto
            if mode == "auto":
                mode = self.detect_optimal_mode()
            
            self.mode = mode
            
            # Validate configuration
            if not self.validate_configuration():
                log.error("❌ Configuration validation failed")
                sys.exit(1)
            
            # Start in selected mode
            if mode == "advanced":
                self.start_advanced_mode()
            elif mode == "basic":
                self.start_basic_mode()
            elif mode == "simple":
                self.start_simple_mode()
            else:
                log.error(f"❌ Unknown mode: {mode}")
                sys.exit(1)
                
        except KeyboardInterrupt:
            log.info("🛑 Application interrupted by user")
        except Exception as e:
            log.error(f"❌ Critical error: {e}")
            sys.exit(1)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        log.info("🧹 Cleaning up resources...")
        
        try:
            if self.realtime_api:
                log.info("🛑 Stopping real-time API...")
                self.realtime_api.stop()
            
            if self.http_server:
                log.info("🛑 Stopping HTTP server...")
                self.http_server.stop()
            
            if self.hourly_aggregator:
                log.info("🛑 Stopping hourly aggregator...")
                self.hourly_aggregator.stop()
            
            if self.pipeline and hasattr(self.pipeline, 'is_running') and self.pipeline.is_running:
                log.info("🛑 Stopping transcription pipeline...")
                self.pipeline.stop()
            
            if self.json_transcriber and hasattr(self.json_transcriber, 'is_running') and self.json_transcriber.is_running:
                log.info("🛑 Stopping JSON transcriber...")
                self.json_transcriber.stop()
                
        except Exception as e:
            log.error(f"Error during cleanup: {e}")
        
        log.info("✅ Cleanup completed")

def signal_handler(sig, frame):
    """Handle system signals for graceful shutdown"""
    log.info("Received signal, shutting down...")
    if current_app:
        current_app.cleanup()
    sys.exit(0)

def show_configuration():
    """Display current configuration"""
    print("\n" + "="*60)
    print("⚙️  WHISPERSILENT CONFIGURATION")
    print("="*60)
    
    # Audio configuration
    print("\n🎤 AUDIO CONFIGURATION:")
    print(f"   Sample Rate: {Config.AUDIO['sample_rate']} Hz")
    print(f"   Channels: {Config.AUDIO['channels']}")
    print(f"   Device: {Config.AUDIO['device']}")
    
    # Speech recognition
    print("\n🗣️  SPEECH RECOGNITION:")
    engine = Config.SPEECH_RECOGNITION.get("engine", "not configured")
    print(f"   Engine: {engine}")
    print(f"   Language: {Config.SPEECH_RECOGNITION.get('language', 'not configured')}")
    print(f"   Fallback Enabled: {Config.SPEECH_RECOGNITION.get('enable_fallback', False)}")
    
    # HTTP server
    print("\n🌐 HTTP SERVER:")
    print(f"   Host: {Config.HTTP_SERVER['host']}")
    print(f"   Port: {Config.HTTP_SERVER['port']}")
    
    # Real-time API
    print("\n🔌 REAL-TIME API:")
    realtime_enabled = os.getenv("REALTIME_API_ENABLED", "false").lower() == "true"
    print(f"   Enabled: {realtime_enabled}")
    if realtime_enabled:
        print(f"   WebSocket Port: {os.getenv('REALTIME_WEBSOCKET_PORT', '8081')}")
        print(f"   Max Connections: {os.getenv('REALTIME_MAX_CONNECTIONS', '50')}")
    
    # Aggregation
    print("\n📊 HOURLY AGGREGATION:")
    aggregation_enabled = os.getenv("HOURLY_AGGREGATION_ENABLED", "true").lower() == "true"
    print(f"   Enabled: {aggregation_enabled}")
    if aggregation_enabled:
        print(f"   Min Silence Gap: {os.getenv('MIN_SILENCE_GAP_MINUTES', '5')} minutes")
    
    # API configuration
    print("\n📡 EXTERNAL API:")
    api_endpoint = Config.API.get("endpoint")
    if api_endpoint:
        print(f"   Endpoint: {api_endpoint}")
        print(f"   Key Configured: {'Yes' if Config.API.get('key') else 'No'}")
    else:
        print("   Not configured")
    
    print("\n" + "="*60)

def run_validation_tests():
    """Run system validation tests"""
    print("\n" + "="*60)
    print("🧪 WHISPERSILENT VALIDATION TESTS")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Configuration loading
    tests_total += 1
    try:
        from config import Config
        assert Config.AUDIO is not None
        assert Config.SPEECH_RECOGNITION is not None
        print("✅ Test 1: Configuration loading - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1: Configuration loading - FAILED: {e}")
    
    # Test 2: Audio capture
    tests_total += 1
    try:
        from core.audioCapture import AudioCapture
        audio = AudioCapture()
        print("✅ Test 2: Audio capture initialization - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: Audio capture initialization - FAILED: {e}")
    
    # Test 3: Speech recognition service
    tests_total += 1
    try:
        from transcription.speechRecognitionService import SpeechRecognitionService
        service = SpeechRecognitionService()
        print("✅ Test 3: Speech recognition service - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Speech recognition service - FAILED: {e}")
    
    # Test 4: Advanced components (optional)
    tests_total += 1
    try:
        from transcription.transcriptionPipeline import TranscriptionPipeline
        from api.httpServer import TranscriptionHTTPServer
        print("✅ Test 4: Advanced components - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"⚠️  Test 4: Advanced components - FAILED: {e} (Advanced mode not available)")
    
    # Test 5: Basic components
    tests_total += 1
    try:
        from transcription.jsonTranscriber import JsonTranscriber
        print("✅ Test 5: Basic components - PASSED")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5: Basic components - FAILED: {e}")
    
    # Summary
    print("\n" + "-"*60)
    print(f"📊 RESULTS: {tests_passed}/{tests_total} tests passed ({tests_passed/tests_total*100:.1f}%)")
    
    if tests_passed == tests_total:
        print("🎉 All tests passed! System is ready.")
        return True
    elif tests_passed >= 3:
        print("⚠️  Some tests failed, but basic functionality should work.")
        return True
    else:
        print("❌ Critical tests failed. Please check installation.")
        return False

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="WhisperSilent - Unified Real-Time Transcription System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'mode', 
        nargs='?', 
        default='auto',
        choices=['auto', 'advanced', 'basic', 'simple'],
        help='Operation mode (default: auto)'
    )
    
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Show interactive mode selection'
    )
    
    parser.add_argument(
        '--config', 
        action='store_true',
        help='Show current configuration'
    )
    
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Run system validation tests'
    )
    
    args = parser.parse_args()
    
    # Handle special options
    if args.config:
        show_configuration()
        return
    
    if args.test:
        success = run_validation_tests()
        sys.exit(0 if success else 1)
    
    # Initialize application
    app = WhisperSilentApp()
    
    # Determine mode
    if args.interactive:
        mode = app.show_interactive_selection()
    else:
        mode = args.mode
    
    # Show startup banner
    print("\n" + "="*70)
    print("🎤 WHISPERSILENT - UNIFIED TRANSCRIPTION SYSTEM")
    print("="*70)
    print(f"🚀 Starting in {mode.upper()} mode...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run application
    app.run(mode)

if __name__ == "__main__":
    main()