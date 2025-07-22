#!/usr/bin/env python3
import os
import sys
import time
import threading
import json
from datetime import datetime

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jsonTranscriber import JsonTranscriber

# Import the classes directly from the mainWithServer module
import importlib.util
spec = importlib.util.spec_from_file_location("mainWithServer", os.path.join(os.path.dirname(__file__), 'src', 'mainWithServer.py'))
main_with_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_with_server)

SimpleTranscriptionHTTPServer = main_with_server.SimpleTranscriptionHTTPServer

def create_test_data(transcriber):
    """Create some test transcription data"""
    print("Creating test data...")
    
    # Simulate some transcriptions
    test_transcriptions = [
        {"id": 1, "timestamp": "2025-07-22T06:00:00", "text": "Hello world", "confidence": 0.95, "engine": "google"},
        {"id": 2, "timestamp": "2025-07-22T06:05:00", "text": "Testing transcription system", "confidence": 0.88, "engine": "google"},
        {"id": 3, "timestamp": "2025-07-22T06:10:00", "text": "Aggregation endpoints", "confidence": 0.92, "engine": "google"},
        {"id": 4, "timestamp": "2025-07-22T06:15:00", "text": "Search functionality test", "confidence": 0.87, "engine": "google"},
        {"id": 5, "timestamp": "2025-07-22T06:20:00", "text": "Statistics and summary", "confidence": 0.91, "engine": "google"},
    ]
    
    # Add test data to transcriber
    with transcriber.lock:
        transcriber.transcriptions = test_transcriptions
        transcriber.stats.update({
            "session_start": "2025-07-22T06:00:00",
            "total_transcriptions": len(test_transcriptions),
            "successful_transcriptions": len(test_transcriptions),
            "total_audio_chunks": len(test_transcriptions) + 2,
            "empty_transcriptions": 2,
            "errors": 0,
            "engine_used": "google",
            "last_update": datetime.now().isoformat()
        })
    
    print(f"Created {len(test_transcriptions)} test transcriptions")

def main():
    print("🚀 Starting local HTTP server test...")
    
    # Initialize transcriber with test file
    transcriber = JsonTranscriber("test_transcriptions_local.json")
    
    # Create test data
    create_test_data(transcriber)
    
    # Start HTTP server on port 8081
    server = SimpleTranscriptionHTTPServer(transcriber, host='localhost', port=8081)
    
    try:
        print("Starting HTTP server on http://localhost:8081")
        server.start()
        
        print("\n✅ Server started successfully!")
        print("Available endpoints:")
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
        print("\n🔍 Ready for testing! Server will run for 60 seconds...")
        
        # Keep server running for testing
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n⏹️ Stopping server...")
    finally:
        server.stop()
        print("Server stopped.")

if __name__ == "__main__":
    main()