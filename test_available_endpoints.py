#!/usr/bin/env python3
"""
Test only the available endpoints on 192.168.31.54:8080
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint_detailed(url, description=""):
    """Test endpoint with detailed analysis"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time
        
        print(f"🔍 Testing: {url}")
        print(f"   📝 {description}")
        print(f"   📊 Status: {response.status_code}")
        print(f"   ⏱️  Time: {response_time:.3f}s")
        
        if response.status_code == 200:
            try:
                data = json.loads(response.text)
                print(f"   📄 Response (JSON):")
                print(f"      {json.dumps(data, indent=6)}")
                
                # Analyze response structure
                if isinstance(data, dict):
                    print(f"   🔧 Keys found: {list(data.keys())}")
                elif isinstance(data, list):
                    print(f"   📊 Array length: {len(data)}")
                    if len(data) > 0:
                        print(f"   🔍 First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
                        
            except json.JSONDecodeError:
                print(f"   📄 Response (Text): {response.text[:200]}...")
                
        else:
            print(f"   ❌ Error response: {response.text[:100]}...")
            
        print("   " + "-" * 50)
        return response.status_code == 200, response_time, response.text
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   " + "-" * 50)
        return False, 0, str(e)

def main():
    base_url = "http://192.168.31.54:8080"
    
    print("🎯 TESTE DETALHADO DOS ENDPOINTS DISPONÍVEIS")
    print(f"📡 Servidor: {base_url}")
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    results = []
    
    # Test main endpoints
    endpoints = [
        ("/health", "Health check - status do sistema"),
        ("/transcriptions", "Lista todas as transcrições disponíveis"),
        ("/transcriptions?limit=10", "Limite de 10 transcrições"),
        ("/transcriptions?limit=5", "Limite de 5 transcrições"),
        ("/transcriptions?limit=1", "Apenas 1 transcrição"),
        ("/transcriptions?recent_minutes=60", "Transcrições das últimas 60 minutos"),
        ("/transcriptions?recent_minutes=30", "Transcrições dos últimos 30 minutos"),
        ("/transcriptions?recent_minutes=5", "Transcrições dos últimos 5 minutos"),
    ]
    
    for path, description in endpoints:
        url = f"{base_url}{path}"
        success, response_time, response_data = test_endpoint_detailed(url, description)
        results.append({
            "endpoint": path,
            "success": success,
            "response_time": response_time,
            "response_data": response_data
        })
        time.sleep(0.5)  # Pause between requests
    
    # Summary
    print("\n📊 RESUMO DOS RESULTADOS")
    print("=" * 80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    print(f"✅ Endpoints funcionando: {len(successful)}/{len(results)}")
    print(f"❌ Endpoints com falha: {len(failed)}")
    
    if successful:
        avg_time = sum(r["response_time"] for r in successful) / len(successful)
        print(f"⏱️  Tempo médio de resposta: {avg_time:.3f}s")
        
        print(f"\n🎉 ENDPOINTS FUNCIONAIS:")
        for result in successful:
            print(f"   ✅ {result['endpoint']} ({result['response_time']:.3f}s)")
    
    if failed:
        print(f"\n❌ ENDPOINTS COM PROBLEMAS:")
        for result in failed:
            print(f"   🔴 {result['endpoint']}")
    
    # Test server capabilities
    print(f"\n🔧 ANÁLISE DE CAPACIDADES DO SERVIDOR")
    print("=" * 60)
    
    # Check if server has transcriptions
    transcriptions_result = next((r for r in results if r["endpoint"] == "/transcriptions"), None)
    if transcriptions_result and transcriptions_result["success"]:
        try:
            data = json.loads(transcriptions_result["response_data"])
            if isinstance(data, list):
                print(f"📊 Total de transcrições armazenadas: {len(data)}")
                if len(data) > 0:
                    # Analyze transcription structure
                    sample = data[0]
                    print(f"📝 Estrutura das transcrições:")
                    for key, value in sample.items():
                        print(f"   - {key}: {type(value).__name__}")
                    
                    # Check if recent transcriptions exist
                    recent = [t for t in data if isinstance(t.get('timestamp'), (int, float)) and 
                             time.time() - t['timestamp'] < 3600]  # Last hour
                    print(f"🕐 Transcrições da última hora: {len(recent)}")
                    
                else:
                    print("📭 Nenhuma transcrição armazenada no servidor")
            else:
                print(f"📄 Response não é uma lista: {type(data)}")
        except Exception as e:
            print(f"❌ Erro ao analisar transcrições: {e}")
    
    # Check health status details
    health_result = next((r for r in results if r["endpoint"] == "/health"), None)
    if health_result and health_result["success"]:
        try:
            health_data = json.loads(health_result["response_data"])
            print(f"\n💚 STATUS DE SAÚDE DO SERVIDOR:")
            for key, value in health_data.items():
                print(f"   {key}: {value}")
        except Exception as e:
            print(f"❌ Erro ao analisar health: {e}")
    
    print(f"\n🎯 CONCLUSÃO:")
    if len(successful) >= 2:
        print("✅ Servidor está operacional e respondendo corretamente")
        print("📊 Endpoints de consulta (GET) estão funcionando")
        print("📝 Servidor parece ser uma versão básica/read-only")
        print("💡 Para envio de dados, pode ser necessário usar uma API diferente")
    else:
        print("⚠️  Servidor tem funcionalidade limitada")
        print("🔧 Apenas alguns endpoints estão funcionando")
    
    return len(successful) > 0

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 Teste concluído com sucesso!' if success else '❌ Teste encontrou problemas'}")