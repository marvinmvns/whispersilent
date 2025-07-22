#!/usr/bin/env python3
"""
Discovery script to find available endpoints on 192.168.31.54:8080
"""

import requests
import json
import time

def test_endpoint(url, method="GET", data=None):
    """Test a single endpoint and return detailed info"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        return {
            "status": response.status_code,
            "success": 200 <= response.status_code < 400,
            "data": response.text[:500],
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {
            "status": None,
            "success": False,
            "error": str(e)
        }

def main():
    base_url = "http://192.168.31.54:8080"
    
    print("🔍 DESCOBRINDO ENDPOINTS DISPONÍVEIS")
    print(f"🎯 Servidor: {base_url}")
    print("=" * 60)
    
    # Test known working endpoints
    working_endpoints = []
    
    print("\n✅ ENDPOINTS QUE FUNCIONAM:")
    
    # Test /health
    result = test_endpoint(f"{base_url}/health")
    if result["success"]:
        print(f"✅ GET /health - Status: {result['status']}")
        try:
            data = json.loads(result['data'])
            print(f"   📄 Response: {json.dumps(data, indent=2)}")
        except:
            print(f"   📄 Response: {result['data']}")
        working_endpoints.append("/health")
    
    # Test /transcriptions
    result = test_endpoint(f"{base_url}/transcriptions")
    if result["success"]:
        print(f"✅ GET /transcriptions - Status: {result['status']}")
        try:
            data = json.loads(result['data'])
            print(f"   📊 Total items: {len(data) if isinstance(data, list) else 'N/A'}")
        except:
            pass
        working_endpoints.append("/transcriptions")
    
    # Test common paths
    common_paths = [
        "/",
        "/api", 
        "/v1",
        "/docs",
        "/swagger",
        "/openapi.json",
        "/ping",
        "/version",
        "/info",
        "/transcribe",
        "/upload",
        "/file",
        "/audio",
        "/speech",
        "/recognize"
    ]
    
    print(f"\n🔍 TESTANDO ENDPOINTS COMUNS:")
    for path in common_paths:
        result = test_endpoint(f"{base_url}{path}")
        if result["success"]:
            print(f"✅ GET {path} - Status: {result['status']}")
            working_endpoints.append(path)
        elif result["status"] == 405:  # Method not allowed, try POST
            post_result = test_endpoint(f"{base_url}{path}", "POST", {})
            if post_result["success"]:
                print(f"✅ POST {path} - Status: {post_result['status']}")
                working_endpoints.append(f"POST {path}")
        time.sleep(0.1)
    
    # Test with audio data
    print(f"\n🎵 TESTANDO COM DADOS DE ÁUDIO:")
    audio_endpoints = ["/transcribe", "/upload", "/audio", "/speech", "/recognize"]
    
    # Sample audio data (mock)
    audio_data = {
        "audio": "mock_audio_data",
        "format": "wav",
        "sample_rate": 16000,
        "language": "pt-BR"
    }
    
    text_data = {
        "text": "Teste de transcrição",
        "timestamp": time.time(),
        "source": "test"
    }
    
    for endpoint in audio_endpoints:
        # Try with audio data
        result = test_endpoint(f"{base_url}{endpoint}", "POST", audio_data)
        if result["success"]:
            print(f"✅ POST {endpoint} (audio) - Status: {result['status']}")
            working_endpoints.append(f"POST {endpoint} (audio)")
            
        # Try with text data
        result = test_endpoint(f"{base_url}{endpoint}", "POST", text_data)
        if result["success"] or result["status"] != 404:
            print(f"📝 POST {endpoint} (text) - Status: {result['status']}")
            if result["success"]:
                working_endpoints.append(f"POST {endpoint} (text)")
        
        time.sleep(0.2)
    
    # Check what the server returns on root
    print(f"\n📋 INFORMAÇÕES DO SERVIDOR:")
    root_result = test_endpoint(f"{base_url}/")
    if root_result["success"]:
        print("✅ Root endpoint disponível:")
        print(f"   {root_result['data']}")
    
    # Check headers for clues
    health_result = test_endpoint(f"{base_url}/health")
    if health_result["success"] and "headers" in health_result:
        print(f"\n🔧 HEADERS DO SERVIDOR:")
        for key, value in health_result["headers"].items():
            if key.lower() in ['server', 'x-powered-by', 'x-api-version', 'content-type']:
                print(f"   {key}: {value}")
    
    print(f"\n📊 RESUMO:")
    print(f"   🎯 Endpoints funcionais encontrados: {len(working_endpoints)}")
    for endpoint in working_endpoints:
        print(f"   ✅ {endpoint}")
    
    # Test sending a real transcription
    print(f"\n🧪 TESTE FINAL - ENVIANDO TRANSCRIÇÃO REAL:")
    transcription_data = {
        "transcription": "Esta é uma transcrição de teste",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "sampleRate": 16000,
            "channels": 1,
            "language": "pt-BR",
            "model": "test",
            "device": "test-client"
        }
    }
    
    # Try different endpoints for sending transcription
    send_endpoints = ["/transcribe", "/transcriptions", "/upload", "/", "/api/transcribe"]
    
    for endpoint in send_endpoints:
        result = test_endpoint(f"{base_url}{endpoint}", "POST", transcription_data)
        print(f"📤 POST {endpoint}: Status {result['status']} - {'✅' if result['success'] else '❌'}")
        if result["success"]:
            print(f"   📄 Response: {result['data'][:200]}...")
        time.sleep(0.3)

if __name__ == "__main__":
    main()