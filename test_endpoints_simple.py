#!/usr/bin/env python3
import os
import sys
import json
import requests
import threading
import time
from datetime import datetime

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'transcription'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'api'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from jsonTranscriber import JsonTranscriber

def test_endpoints():
    """Test all endpoints with curl commands"""
    base_url = "http://localhost:8081"
    
    endpoints_to_test = [
        "/health",
        "/health/detailed", 
        "/status",
        "/stats",
        "/transcriptions",
        "/transcriptions?limit=3",
        "/transcriptions/statistics",
        "/transcriptions/summary",
        "/transcriptions/summary?hours=1",
        "/transcriptions/search?q=test",
        "/transcriptions/search?q=Hello"
    ]
    
    print("🧪 Testing all endpoints...")
    print("=" * 60)
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        print(f"\n🔍 Testing: {endpoint}")
        print(f"URL: {url}")
        
        try:
            result = os.system(f'curl -s "{url}"')
            if result == 0:
                print("✅ SUCCESS")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 40)

def test_methods_directly():
    """Test the methods directly without HTTP"""
    print("\n🔬 Testing methods directly...")
    print("=" * 60)
    
    # Create transcriber with test data
    transcriber = JsonTranscriber("test_direct.json")
    
    # Add test data
    test_transcriptions = [
        {"id": 1, "timestamp": "2025-07-22T06:00:00", "text": "Hello world test", "confidence": 0.95, "engine": "google"},
        {"id": 2, "timestamp": "2025-07-22T06:05:00", "text": "Testing transcription system", "confidence": 0.88, "engine": "google"},
        {"id": 3, "timestamp": "2025-07-22T06:10:00", "text": "Aggregation endpoints", "confidence": 0.92, "engine": "google"},
    ]
    
    with transcriber.lock:
        transcriber.transcriptions = test_transcriptions
        transcriber.stats.update({
            "session_start": "2025-07-22T06:00:00",
            "total_transcriptions": len(test_transcriptions),
            "successful_transcriptions": len(test_transcriptions),
            "total_audio_chunks": len(test_transcriptions) + 1,
            "empty_transcriptions": 1,
            "errors": 0,
        })
    
    # Test methods
    print("\n📊 Testing get_statistics():")
    stats = transcriber.get_statistics()
    print(json.dumps(stats, indent=2))
    
    print("\n📈 Testing get_summary(1):")
    summary = transcriber.get_summary(1)
    print(json.dumps(summary, indent=2))
    
    print("\n🔍 Testing search_transcriptions('test'):")
    search_results = transcriber.search_transcriptions('test')
    print(f"Found {len(search_results)} results:")
    for result in search_results:
        print(f"  - {result.get('text', 'No text')}")
    
    print("\n🔍 Testing search_transcriptions('Hello'):")
    search_results2 = transcriber.search_transcriptions('Hello')
    print(f"Found {len(search_results2)} results:")
    for result in search_results2:
        print(f"  - {result.get('text', 'No text')}")

if __name__ == "__main__":
    print("🚀 Comprehensive Endpoint Testing")
    
    # Test methods directly first
    test_methods_directly()
    
    # Test HTTP endpoints if server is running
    print(f"\n\n🌐 HTTP Endpoint Testing")
    print("Note: Make sure server is running on localhost:8081")
    
    # Check if server is accessible
    try:
        result = os.system('curl -s http://localhost:8081/health > /dev/null 2>&1')
        if result == 0:
            print("✅ Server is accessible, testing HTTP endpoints...")
            test_endpoints()
        else:
            print("❌ Server is not accessible on localhost:8081")
            print("💡 Run the server manually and then test endpoints")
    except:
        print("❌ Cannot test HTTP endpoints")