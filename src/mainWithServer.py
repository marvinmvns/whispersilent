import os
import sys
import signal
import time
from datetime import datetime
from dotenv import load_dotenv

# Add module paths with higher priority
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services'))

from jsonTranscriber import JsonTranscriber
from httpServer import TranscriptionHTTPServer
from logger import log
from config import Config

# Load environment variables from .env file
load_dotenv()

# Forçar engine do Google antes de importar (testado e funcionando)
os.environ['SPEECH_RECOGNITION_ENGINE'] = 'google'

# Instantiate transcriber and server for global access
json_transcriber = JsonTranscriber("transcriptions_server.json")
http_server = None

def check_configuration():
    """Verifies that essential configurations are present."""
    log.debug("🔍 Checking configuration...")
    
    api_endpoint = os.getenv('API_ENDPOINT')
    if not api_endpoint:
        log.warning("⚠️  No API_ENDPOINT configured - API sending will be disabled")
        log.debug("💡 Set API_ENDPOINT in .env file to enable API functionality")
    else:
        log.debug(f"✅ API endpoint configured: {api_endpoint[:50]}...")
        api_key = os.getenv('API_KEY')
        if not api_key:
            log.warning("⚠️  No API_KEY configured - API requests may fail if authentication is required")
            log.debug("💡 Set API_KEY in .env file if your API requires authentication")
        else:
            log.debug("✅ API key configured")

    # Check speech recognition engine configuration
    engine = Config.SPEECH_RECOGNITION.get("engine", "google")
    log.debug(f"🎯 Speech recognition engine: {engine}")
    
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

# Servidor HTTP simplificado para JsonTranscriber
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

class SimpleTranscriptionHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, transcriber=None, **kwargs):
        self.transcriber = transcriber
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        # Silenciar logs do servidor HTTP
        pass
        
    def _send_json_response(self, data, status_code=200):
        """Send a JSON response"""
        response = json.dumps(data, indent=2, ensure_ascii=False)
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response.encode('utf-8'))))
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
        
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == '/health':
            self._send_json_response({
                "status": "healthy",
                "transcriber_running": self.transcriber.is_running,
                "engine": self.transcriber.speech_service.engine.value,
                "timestamp": time.time()
            })
        elif path == '/health/detailed':
            stats = self.transcriber.get_stats()
            self._send_json_response({
                "status": "healthy",
                "transcriber_running": self.transcriber.is_running,
                "engine": self.transcriber.speech_service.engine.value,
                "timestamp": time.time(),
                "stats": stats
            })
        elif path == '/stats':
            stats = self.transcriber.get_stats()
            self._send_json_response(stats)
        elif path == '/status':
            self._send_json_response({
                "pipeline_running": self.transcriber.is_running,
                "api_sending_enabled": False,  # JsonTranscriber doesn't send to API
                "transcription_service": "JsonTranscriber",
                "engine": self.transcriber.speech_service.engine.value,
                "uptime_seconds": time.time() - (datetime.fromisoformat(self.transcriber.stats['session_start']).timestamp() if self.transcriber.stats.get('session_start') else time.time()),
                "timestamp": time.time()
            })
        elif path == '/transcriptions':
            # Parse query parameters
            limit = None
            if 'limit' in query_params:
                try:
                    limit = int(query_params['limit'][0])
                except (ValueError, IndexError):
                    self._send_json_response({"error": "Invalid limit parameter"}, 400)
                    return
            
            if 'recent_minutes' in query_params:
                try:
                    minutes = int(query_params['recent_minutes'][0])
                    # Get transcriptions from last N minutes
                    import datetime as dt
                    cutoff_time = dt.datetime.now() - dt.timedelta(minutes=minutes)
                    recent_transcriptions = []
                    for t in self.transcriber.transcriptions:
                        if 'timestamp' in t:
                            try:
                                t_time = dt.datetime.fromisoformat(t['timestamp'].replace('Z', ''))
                                if t_time >= cutoff_time:
                                    recent_transcriptions.append(t)
                            except:
                                continue
                    transcriptions = recent_transcriptions[-limit:] if limit else recent_transcriptions
                except (ValueError, IndexError):
                    self._send_json_response({"error": "Invalid recent_minutes parameter"}, 400)
                    return
            else:
                transcriptions = self.transcriber.get_transcriptions(limit=limit)
            
            self._send_json_response({
                "transcriptions": transcriptions,
                "count": len(transcriptions),
                "total": len(self.transcriber.transcriptions)
            })
        elif path == '/transcriptions/search':
            if 'q' not in query_params:
                self._send_json_response({"error": "Missing search query parameter 'q'"}, 400)
                return
            
            query = query_params['q'][0]
            case_sensitive = query_params.get('case_sensitive', ['false'])[0].lower() == 'true'
            
            results = self.transcriber.search_transcriptions(query, case_sensitive)
            
            self._send_json_response({
                "query": query,
                "case_sensitive": case_sensitive,
                "results": results,
                "total_matches": len(results),
                "timestamp": time.time()
            })
        elif path == '/transcriptions/statistics':
            stats = self.transcriber.get_statistics()
            self._send_json_response(stats)
        elif path == '/transcriptions/summary':
            hours = 24  # default
            if 'hours' in query_params:
                try:
                    hours = int(query_params['hours'][0])
                except (ValueError, IndexError):
                    self._send_json_response({"error": "Invalid hours parameter"}, 400)
                    return
            
            summary = self.transcriber.get_summary(hours)
            self._send_json_response(summary)
        else:
            self._send_json_response({"error": "Not found"}, 404)

class SimpleTranscriptionHTTPServer:
    def __init__(self, transcriber, host='localhost', port=8080):
        self.transcriber = transcriber
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the HTTP server in a separate thread"""
        def handler(*args, **kwargs):
            return SimpleTranscriptionHandler(*args, transcriber=self.transcriber, **kwargs)
            
        self.server = HTTPServer((self.host, self.port), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        log.info(f"HTTP server started on {self.host}:{self.port}")
        
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=1)
            log.info("HTTP server stopped")

def signal_handler(sig, frame):
    """Handles graceful shutdown on system signals."""
    log.info(f'Received signal {signal.Signals(sig).name}, shutting down...')
    
    # Stop HTTP server first
    if 'http_server' in globals() and http_server:
        http_server.stop()
        
    # Stop transcriber
    if 'json_transcriber' in globals() and json_transcriber.is_running:
        json_transcriber.stop()
    
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
    if 'json_transcriber' in globals() and json_transcriber.is_running:
        json_transcriber.stop()
    sys.exit(1)

def main():
    """Main application function."""
    global http_server, json_transcriber
    
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
        
        # Get HTTP server configuration from Config
        http_host = Config.HTTP_SERVER["host"]
        http_port = Config.HTTP_SERVER["port"]
        
        log.info(f'🌐 Starting HTTP server on {http_host}:{http_port}...')
        # Create a simplified server that works with JsonTranscriber
        http_server = SimpleTranscriptionHTTPServer(json_transcriber, http_host, http_port)
        http_server.start()
        
        log.debug(f'✅ HTTP server initialized')
        log.debug(f'🎯 Engine: {json_transcriber.speech_service.engine.value}')
        log.debug(f'🌍 Language: {json_transcriber.speech_service.language}')
        
        log.info('🚀 Starting transcription system...')
        json_transcriber.start()
        
        log.info('\n' + '='*60)
        log.info('✅ SYSTEM READY!')
        log.info('🎤 Speak into the microphone to transcribe')
        log.info('📝 Transcriptions will be stored in JSON format')
        log.info(f'🌐 HTTP API available at: http://{http_host}:{http_port}')
        log.info('⚠️  Use CTRL+C to stop')
        log.info('='*60)
        
        log.debug('📋 Available HTTP endpoints:')
        log.debug(f'   Health Check: http://{http_host}:{http_port}/health')
        log.debug(f'   Transcriptions: http://{http_host}:{http_port}/transcriptions')
        log.debug(f'   Stats: http://{http_host}:{http_port}/stats')
        log.debug('')
        
        # Keep the main thread alive while services are running
        start_time = time.time()
        last_status = start_time
        
        while json_transcriber.is_running:
            current_time = time.time()
            
            # Show status periodically
            if current_time - last_status > 30:  # Every 30 seconds
                uptime = current_time - start_time
                stats = json_transcriber.get_stats()
                log.debug(f'📊 [{uptime:.0f}s] System running - Transcrições: {stats.get("successful_transcriptions", 0)}')
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
            
        if 'json_transcriber' in globals() and json_transcriber.is_running:
            log.info("🛑 Finalizing transcription system...")
            json_transcriber.stop()
            
            # Show final stats if available
            try:
                stats = json_transcriber.get_stats()
                log.info(f"\n📊 FINAL RESULTS:")
                log.info(f"   Total transcriptions: {stats.get('total_transcriptions', 0)}")
                log.info(f"   Successful: {stats.get('successful_transcriptions', 0)}")
                log.info(f"   Errors: {stats.get('errors', 0)}")
                log.info(f"   JSON file: {json_transcriber.output_file}")
            except Exception:
                pass
            
        log.info("✅ Application terminated successfully!")

if __name__ == '__main__':
    main()