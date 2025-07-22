import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any
import threading
from dataclasses import asdict
from logger import log
from swagger import get_swagger_spec, get_swagger_html
from config import Config

class TranscriptionHTTPHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, pipeline=None, **kwargs):
        self.pipeline = pipeline
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        # Override to use our logger instead of printing to stderr
        log.debug(f"HTTP: {format % args}")
        
    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
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
        
    def _send_error_response(self, message: str, status_code: int = 500):
        """Send an error response"""
        self._send_json_response({
            "error": message,
            "timestamp": time.time()
        }, status_code)
        
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            if path == '/health':
                self._handle_health_check()
            elif path == '/health/detailed':
                self._handle_detailed_health_check()
            elif path == '/transcriptions':
                self._handle_get_transcriptions(query_params)
            elif path == '/transcriptions/search':
                self._handle_search_transcriptions(query_params)
            elif path == '/transcriptions/statistics':
                self._handle_get_statistics()
            elif path == '/transcriptions/summary':
                self._handle_get_summary(query_params)
            elif path == '/status':
                self._handle_get_status()
            elif path == '/api-docs':
                self._handle_swagger_ui()
            elif path == '/api-docs.json':
                self._handle_swagger_spec()
            elif path.startswith('/transcriptions/'):
                # Handle individual transcription by ID
                record_id = path.split('/')[-1]
                self._handle_get_transcription_by_id(record_id)
            else:
                self._send_error_response("Endpoint not found", 404)
                
        except Exception as e:
            log.error(f"Error handling GET request: {e}")
            self._send_error_response(f"Internal server error: {str(e)}")
            
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            if path == '/transcriptions/export':
                self._handle_export_transcriptions()
            elif path == '/transcriptions/send-unsent':
                self._handle_send_unsent_transcriptions()
            elif path == '/control/toggle-api-sending':
                self._handle_toggle_api_sending()
            elif path == '/control/start':
                self._handle_start_pipeline()
            elif path == '/control/stop':
                self._handle_stop_pipeline()
            else:
                self._send_error_response("Endpoint not found", 404)
                
        except Exception as e:
            log.error(f"Error handling POST request: {e}")
            self._send_error_response(f"Internal server error: {str(e)}")
            
    def _handle_swagger_ui(self):
        """Serve Swagger UI"""
        html = get_swagger_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
        
    def _handle_swagger_spec(self):
        """Serve OpenAPI specification"""
        self._send_json_response(get_swagger_spec())
            
    def _handle_health_check(self):
        """Basic health check endpoint"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        health_summary = self.pipeline.health_monitor.get_health_summary()
        self._send_json_response(health_summary)
        
    def _handle_detailed_health_check(self):
        """Detailed health check endpoint"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        health_status = self.pipeline.health_monitor.get_health_status()
        self._send_json_response(asdict(health_status))
        
    def _handle_get_transcriptions(self, query_params):
        """Get transcriptions with optional filtering"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        limit = None
        if 'limit' in query_params:
            try:
                limit = int(query_params['limit'][0])
            except (ValueError, IndexError):
                self._send_error_response("Invalid limit parameter", 400)
                return
                
        start_time = None
        end_time = None
        if 'start_time' in query_params:
            try:
                start_time = float(query_params['start_time'][0])
            except (ValueError, IndexError):
                self._send_error_response("Invalid start_time parameter", 400)
                return
                
        if 'end_time' in query_params:
            try:
                end_time = float(query_params['end_time'][0])
            except (ValueError, IndexError):
                self._send_error_response("Invalid end_time parameter", 400)
                return
                
        if 'recent_minutes' in query_params:
            try:
                minutes = int(query_params['recent_minutes'][0])
                transcriptions = self.pipeline.transcription_storage.get_recent_transcriptions(minutes)
            except (ValueError, IndexError):
                self._send_error_response("Invalid recent_minutes parameter", 400)
                return
        elif start_time is not None and end_time is not None:
            transcriptions = self.pipeline.transcription_storage.get_transcriptions_by_timerange(start_time, end_time)
        else:
            transcriptions = self.pipeline.transcription_storage.get_all_transcriptions(limit)
            
        self._send_json_response({
            "transcriptions": transcriptions,
            "total_count": len(transcriptions),
            "timestamp": time.time()
        })
        
    def _handle_search_transcriptions(self, query_params):
        """Search transcriptions by text"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        if 'q' not in query_params:
            self._send_error_response("Missing search query parameter 'q'", 400)
            return
            
        query = query_params['q'][0]
        case_sensitive = query_params.get('case_sensitive', ['false'])[0].lower() == 'true'
        
        results = self.pipeline.transcription_storage.search_transcriptions(query, case_sensitive)
        
        self._send_json_response({
            "query": query,
            "case_sensitive": case_sensitive,
            "results": results,
            "total_matches": len(results),
            "timestamp": time.time()
        })
        
    def _handle_get_transcription_by_id(self, record_id):
        """Get a specific transcription by ID"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        transcription = self.pipeline.transcription_storage.get_transcription_by_id(record_id)
        
        if transcription:
            self._send_json_response(transcription)
        else:
            self._send_error_response("Transcription not found", 404)
            
    def _handle_get_statistics(self):
        """Get transcription statistics"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        stats = self.pipeline.transcription_storage.get_statistics()
        self._send_json_response(stats)
        
    def _handle_get_summary(self, query_params):
        """Get transcription summary for a time period"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        hours = 24  # default
        if 'hours' in query_params:
            try:
                hours = int(query_params['hours'][0])
            except (ValueError, IndexError):
                self._send_error_response("Invalid hours parameter", 400)
                return
                
        summary = self.pipeline.transcription_storage.get_summary(hours)
        self._send_json_response(summary)
        
    def _handle_get_status(self):
        """Get current pipeline status"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        status = {
            "pipeline_running": self.pipeline.is_running,
            "api_sending_enabled": getattr(self.pipeline, 'api_sending_enabled', True),
            "transcription_service": "google-transcribe" if Config.GOOGLE_TRANSCRIBE["enabled"] else "whisper.cpp",
            "google_transcribe_configured": bool(Config.GOOGLE_TRANSCRIBE["endpoint"]),
            "uptime_seconds": time.time() - self.pipeline.health_monitor.start_time,
            "timestamp": time.time()
        }
        
        self._send_json_response(status)
        
    def _handle_export_transcriptions(self):
        """Export transcriptions to JSON file"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        try:
            filename = self.pipeline.transcription_storage.export_to_json()
            self._send_json_response({
                "message": "Transcriptions exported successfully",
                "filename": filename,
                "timestamp": time.time()
            })
        except Exception as e:
            self._send_error_response(f"Export failed: {str(e)}")
            
    def _handle_send_unsent_transcriptions(self):
        """Send all unsent transcriptions to API"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        unsent = self.pipeline.transcription_storage.get_unsent_transcriptions()
        sent_count = 0
        failed_count = 0
        
        for transcription in unsent:
            try:
                self.pipeline.api_service.send_transcription(
                    transcription['text'],
                    {
                        "chunkSize": transcription['chunk_size'],
                        "processingTimeMs": transcription['processing_time_ms'],
                        "recordId": transcription['id']
                    }
                )
                self.pipeline.transcription_storage.mark_api_sent(transcription['id'])
                sent_count += 1
            except Exception as e:
                log.error(f"Failed to send transcription {transcription['id']}: {e}")
                failed_count += 1
                
        self._send_json_response({
            "message": f"Sent {sent_count} transcriptions, {failed_count} failed",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "timestamp": time.time()
        })
        
    def _handle_toggle_api_sending(self):
        """Toggle automatic API sending on/off"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        current_state = getattr(self.pipeline, 'api_sending_enabled', True)
        new_state = not current_state
        setattr(self.pipeline, 'api_sending_enabled', new_state)
        
        self._send_json_response({
            "message": f"API sending {'enabled' if new_state else 'disabled'}",
            "api_sending_enabled": new_state,
            "timestamp": time.time()
        })
        
    def _handle_start_pipeline(self):
        """Start the transcription pipeline"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        try:
            if self.pipeline.is_running:
                self._send_json_response({
                    "message": "Pipeline is already running",
                    "pipeline_running": True,
                    "timestamp": time.time()
                })
            else:
                self.pipeline.start()
                self._send_json_response({
                    "message": "Pipeline started successfully",
                    "pipeline_running": True,
                    "timestamp": time.time()
                })
        except Exception as e:
            self._send_error_response(f"Failed to start pipeline: {str(e)}")
            
    def _handle_stop_pipeline(self):
        """Stop the transcription pipeline"""
        if not self.pipeline:
            self._send_error_response("Pipeline not available", 503)
            return
            
        try:
            if not self.pipeline.is_running:
                self._send_json_response({
                    "message": "Pipeline is already stopped",
                    "pipeline_running": False,
                    "timestamp": time.time()
                })
            else:
                self.pipeline.stop()
                self._send_json_response({
                    "message": "Pipeline stopped successfully",
                    "pipeline_running": False,
                    "timestamp": time.time()
                })
        except Exception as e:
            self._send_error_response(f"Failed to stop pipeline: {str(e)}")

class TranscriptionHTTPServer:
    def __init__(self, pipeline, host='localhost', port=8080):
        self.pipeline = pipeline
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        
    def start(self):
        """Start the HTTP server"""
        def handler(*args, **kwargs):
            return TranscriptionHTTPHandler(*args, pipeline=self.pipeline, **kwargs)
            
        self.server = HTTPServer((self.host, self.port), handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        log.info(f"HTTP server started on http://{self.host}:{self.port}")
        log.debug("Available endpoints:")
        log.debug("  GET  /health - Basic health check")
        log.debug("  GET  /health/detailed - Detailed health information")
        log.debug("  GET  /transcriptions - Get all transcriptions")
        log.debug("  GET  /transcriptions?limit=N - Get last N transcriptions")
        log.debug("  GET  /transcriptions?recent_minutes=N - Get transcriptions from last N minutes")
        log.debug("  GET  /transcriptions/search?q=text - Search transcriptions")
        log.debug("  GET  /transcriptions/statistics - Get transcription statistics")
        log.debug("  GET  /transcriptions/summary?hours=N - Get summary for last N hours")
        log.debug("  GET  /transcriptions/{id} - Get specific transcription")
        log.debug("  GET  /status - Get pipeline status")
        log.debug("  GET  /api-docs - Swagger UI documentation")
        log.debug("  GET  /api-docs.json - OpenAPI specification")
        log.debug("  POST /transcriptions/export - Export transcriptions to JSON")
        log.debug("  POST /transcriptions/send-unsent - Send unsent transcriptions to API")
        log.debug("  POST /control/toggle-api-sending - Toggle automatic API sending")
        log.debug("  POST /control/start - Start pipeline")
        log.debug("  POST /control/stop - Stop pipeline")
        
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server_thread.join(timeout=5)
            log.info("HTTP server stopped")
            
    def get_url(self):
        """Get the server URL"""
        return f"http://{self.host}:{self.port}"