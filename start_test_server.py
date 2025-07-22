#!/usr/bin/env python3
import os
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jsonTranscriber import JsonTranscriber

# Import the handler directly from mainWithServer
import importlib.util
spec = importlib.util.spec_from_file_location("mainWithServer", os.path.join(os.path.dirname(__file__), 'src', 'mainWithServer.py'))
main_with_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_with_server)

def create_test_transcriber():
    """Create a transcriber with test data"""
    transcriber = JsonTranscriber("test_server_data.json")
    
    # Add comprehensive test data
    test_transcriptions = [
        {"id": 1, "timestamp": "2025-07-22T06:00:00", "text": "Hello world testing", "confidence": 0.95, "engine": "google"},
        {"id": 2, "timestamp": "2025-07-22T06:05:00", "text": "Testing transcription system endpoints", "confidence": 0.88, "engine": "google"},
        {"id": 3, "timestamp": "2025-07-22T06:10:00", "text": "Aggregation and statistics functionality", "confidence": 0.92, "engine": "google"},
        {"id": 4, "timestamp": "2025-07-22T06:15:00", "text": "Search functionality test case", "confidence": 0.87, "engine": "google"},
        {"id": 5, "timestamp": "2025-07-22T06:20:00", "text": "Summary and analytics endpoint", "confidence": 0.91, "engine": "google"},
        {"id": 6, "timestamp": "2025-07-22T06:25:00", "text": "Local server validation process", "confidence": 0.89, "engine": "google"},
    ]
    
    with transcriber.lock:
        transcriber.transcriptions = test_transcriptions
        transcriber.stats.update({
            "session_start": "2025-07-22T06:00:00",
            "total_transcriptions": len(test_transcriptions),
            "successful_transcriptions": len(test_transcriptions),
            "total_audio_chunks": len(test_transcriptions) + 3,
            "empty_transcriptions": 3,
            "errors": 0,
            "engine_used": "google",
            "last_update": datetime.now().isoformat()
        })
    
    return transcriber

def main():
    print("🚀 Starting Local Test Server...")
    
    # Create transcriber with test data
    transcriber = create_test_transcriber()
    print(f"✅ Created transcriber with {len(transcriber.transcriptions)} test transcriptions")
    
    # Create handler factory
    def handler_factory(*args, **kwargs):
        return main_with_server.SimpleTranscriptionHandler(*args, transcriber=transcriber, **kwargs)
    
    # Create and start server
    server = HTTPServer(('localhost', 8081), handler_factory)
    
    print("🌐 HTTP server starting on http://localhost:8081")
    print("\nAvailable endpoints for testing:")
    print("  GET http://localhost:8081/health")
    print("  GET http://localhost:8081/health/detailed")  
    print("  GET http://localhost:8081/status")
    print("  GET http://localhost:8081/stats")
    print("  GET http://localhost:8081/transcriptions")
    print("  GET http://localhost:8081/transcriptions?limit=3")
    print("  GET http://localhost:8081/transcriptions?recent_minutes=60")
    print("  GET http://localhost:8081/transcriptions/statistics")
    print("  GET http://localhost:8081/transcriptions/summary")
    print("  GET http://localhost:8081/transcriptions/summary?hours=1")
    print("  GET http://localhost:8081/transcriptions/search?q=test")
    print("  GET http://localhost:8081/transcriptions/search?q=endpoint")
    print("\n🔥 Server is running! Press Ctrl+C to stop...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️ Stopping server...")
        server.shutdown()
        print("✅ Server stopped.")

if __name__ == "__main__":
    main()