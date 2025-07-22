#!/usr/bin/env python3
"""
Test script for all endpoints on 192.168.31.54:8080
"""

import sys
import os
import time
import requests
import json
from typing import Dict, Any, List

class RemoteEndpointTester:
    def __init__(self, base_url: str = "http://192.168.31.54:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.test_results = []
        
    def test_endpoint(self, method: str, path: str, expected_status: int = 200, 
                     data: Dict = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint"""
        url = f"{self.base_url}{path}"
        result = {
            "method": method,
            "path": path,
            "url": url,
            "description": description,
            "success": False,
            "status_code": None,
            "response_data": None,
            "error": None,
            "response_time": None
        }
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, timeout=10)
            elif method.upper() == "POST":
                if data:
                    response = self.session.post(url, json=data, timeout=10)
                else:
                    response = self.session.post(url, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            result["response_time"] = time.time() - start_time
            result["status_code"] = response.status_code
            
            # Try to parse JSON response
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
            # Check if status code matches expectation or is reasonable
            if response.status_code == expected_status or (200 <= response.status_code < 300):
                result["success"] = True
            else:
                result["error"] = f"Expected status {expected_status}, got {response.status_code}"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            
        return result
    
    def test_connectivity(self):
        """Test basic connectivity to the server"""
        print(f"🔗 Testing connectivity to {self.base_url}...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            print(f"✅ Server is reachable! Status: {response.status_code}")
            return True
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all endpoint tests"""
        print(f"\n🧪 TESTING ALL ENDPOINTS ON {self.base_url}")
        print("=" * 80)
        
        # Test basic connectivity first
        if not self.test_connectivity():
            print("❌ Stopping tests - server not reachable")
            return []
        
        # Define all endpoints to test
        tests = [
            # Health endpoints
            ("GET", "/health", 200, None, "Basic health check"),
            ("GET", "/health/detailed", 200, None, "Detailed health information"),
            
            # Status endpoint
            ("GET", "/status", 200, None, "Pipeline status and configuration"),
            
            # Transcription endpoints
            ("GET", "/transcriptions", 200, None, "Get all transcriptions"),
            ("GET", "/transcriptions?limit=5", 200, None, "Get limited transcriptions"),
            ("GET", "/transcriptions?recent_minutes=60", 200, None, "Get recent transcriptions"),
            ("GET", "/transcriptions/statistics", 200, None, "Get transcription statistics"),
            ("GET", "/transcriptions/summary", 200, None, "Get transcription summary"),
            ("GET", "/transcriptions/summary?hours=1", 200, None, "Get 1-hour summary"),
            ("GET", "/transcriptions/search?q=test", 200, None, "Search transcriptions"),
            ("GET", "/transcriptions/search?q=test&case_sensitive=true", 200, None, "Case-sensitive search"),
            
            # Control endpoints (testing availability)
            ("POST", "/control/toggle-api-sending", 200, None, "Toggle API sending"),
            ("POST", "/control/start", 200, None, "Start pipeline"),
            ("POST", "/control/stop", 200, None, "Stop pipeline"),
            
            # Export endpoints
            ("POST", "/transcriptions/export", 200, None, "Export transcriptions"),
            ("POST", "/transcriptions/send-unsent", 200, None, "Send unsent transcriptions"),
            
            # API Documentation
            ("GET", "/api-docs", 200, None, "Swagger UI documentation"),
            ("GET", "/api-docs.json", 200, None, "OpenAPI specification"),
            
            # Test with transcription data
            ("POST", "/transcribe", 200, {
                "transcription": "Test transcription",
                "metadata": {"test": True}
            }, "Send test transcription"),
            
            # Non-existent endpoints (should return 404)
            ("GET", "/nonexistent", 404, None, "Non-existent GET endpoint"),
            ("POST", "/nonexistent", 404, None, "Non-existent POST endpoint"),
        ]
        
        results = []
        for i, (method, path, expected_status, data, description) in enumerate(tests, 1):
            print(f"\n🔍 Test {i:2d}/{len(tests)}: {method} {path}")
            print(f"    📝 {description}")
            
            result = self.test_endpoint(method, path, expected_status, data, description)
            results.append(result)
            
            if result["success"]:
                print(f"    ✅ PASS - Status: {result['status_code']} - Time: {result['response_time']:.3f}s")
                if result["response_data"] and isinstance(result["response_data"], dict):
                    # Show some key information from response
                    if "message" in result["response_data"]:
                        print(f"       📄 Message: {result['response_data']['message']}")
                    elif "total_count" in result["response_data"]:
                        print(f"       📊 Count: {result['response_data']['total_count']}")
                    elif "pipeline_running" in result["response_data"]:
                        print(f"       🔧 Pipeline: {'Running' if result['response_data']['pipeline_running'] else 'Stopped'}")
                    elif "health" in result["response_data"]:
                        print(f"       💚 Health: {result['response_data']['health']}")
            else:
                print(f"    ❌ FAIL - {result['error']}")
                if result["status_code"]:
                    print(f"       📊 Status: {result['status_code']}")
                if result["response_data"] and len(str(result["response_data"])) < 100:
                    print(f"       📄 Response: {result['response_data']}")
            
            # Small delay between tests
            time.sleep(0.3)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """Generate a comprehensive test report"""
        print(f"\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        total_tests = len(results)
        passed_tests = len([r for r in results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"🎯 Target Server: {self.base_url}")
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in results:
                if not result["success"]:
                    print(f"   🔴 {result['method']} {result['path']}")
                    print(f"      📝 {result['description']}")
                    print(f"      ❌ {result['error']}")
                    print()
        
        # Performance summary
        response_times = [r["response_time"] for r in results if r["response_time"] is not None]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            print(f"\n⏱️  PERFORMANCE SUMMARY:")
            print(f"   📊 Average Response Time: {avg_time:.3f}s")
            print(f"   🏃 Fastest Response: {min_time:.3f}s")
            print(f"   🐌 Slowest Response: {max_time:.3f}s")
        
        # Endpoint categories
        get_tests = [r for r in results if r["method"] == "GET"]
        post_tests = [r for r in results if r["method"] == "POST"]
        
        print(f"\n📋 RESULTS BY METHOD:")
        print(f"   📥 GET:  {len([r for r in get_tests if r['success']])}/{len(get_tests)} passed")
        print(f"   📤 POST: {len([r for r in post_tests if r['success']])}/{len(post_tests)} passed")
        
        # Server capabilities summary
        successful_endpoints = [r for r in results if r["success"]]
        print(f"\n🚀 SERVER CAPABILITIES:")
        if any("health" in r["path"] for r in successful_endpoints):
            print("   💚 Health monitoring: Available")
        if any("transcription" in r["path"] for r in successful_endpoints):
            print("   📝 Transcription services: Available")
        if any("control" in r["path"] for r in successful_endpoints):
            print("   🎛️  Pipeline control: Available")
        if any("export" in r["path"] for r in successful_endpoints):
            print("   📤 Data export: Available")
        if any("api-docs" in r["path"] for r in successful_endpoints):
            print("   📚 API documentation: Available")
        
        return passed_tests == total_tests

def main():
    """Main test function"""
    print("🌐 REMOTE SERVER ENDPOINT TESTER")
    print("=" * 80)
    print("🎯 Testing all endpoints on 192.168.31.54:8080")
    print("🔍 Comprehensive endpoint functionality test")
    print("=" * 80)
    
    tester = RemoteEndpointTester("http://192.168.31.54:8080")
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        if not results:
            print("❌ No tests were executed")
            return False
        
        # Generate report
        all_passed = tester.generate_report(results)
        
        print(f"\n{'🎉 ALL TESTS PASSED!' if all_passed else '⚠️  SOME TESTS FAILED'}")
        print(f"{'✅ All endpoints are functional' if all_passed else '❌ Check failed endpoints above'}")
        
        return all_passed
        
    except KeyboardInterrupt:
        print(f"\n⚡ Testing interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)