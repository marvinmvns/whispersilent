#!/usr/bin/env python3
"""
Comprehensive test script for all HTTP endpoints in mainWithServer.py
Tests all endpoints to ensure they're functional
"""

import sys
import os
import time
import requests
import json
import subprocess
import signal
import threading
from typing import Dict, Any, List

# Add paths for imports
sys.path.insert(0, 'src')
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/transcription')
sys.path.insert(0, 'src/api')

class HTTPEndpointTester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.server_process = None
        
    def start_server(self):
        """Start the mainWithServer.py in background"""
        print("🚀 Starting mainWithServer.py...")
        
        # Set environment variables for testing
        env = os.environ.copy()
        env['SPEECH_RECOGNITION_ENGINE'] = 'google'
        env['HTTP_HOST'] = 'localhost'
        env['HTTP_PORT'] = '8080'
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, 'src/mainWithServer.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            # Wait for server to start
            print("⏳ Waiting for server to initialize...")
            time.sleep(8)
            
            # Check if server is responsive
            for attempt in range(5):
                try:
                    response = self.session.get(f"{self.base_url}/health", timeout=5)
                    if response.status_code == 200:
                        print("✅ Server is ready!")
                        return True
                except:
                    print(f"   Attempt {attempt + 1}/5 - waiting...")
                    time.sleep(2)
                    
            print("❌ Server failed to start properly")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server process"""
        if self.server_process:
            print("🛑 Stopping server...")
            try:
                # Send SIGTERM to the process group
                os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)
                self.server_process.wait(timeout=10)
            except:
                try:
                    # Force kill if needed
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGKILL)
                except:
                    pass
            
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
            
            # Check if status code matches expectation
            if response.status_code == expected_status:
                result["success"] = True
            else:
                result["error"] = f"Expected status {expected_status}, got {response.status_code}"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
            
        return result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all endpoint tests"""
        print(f"\n🧪 TESTING ALL HTTP ENDPOINTS")
        print("=" * 60)
        
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
            ("GET", "/transcriptions/nonexistent-id", 404, None, "Get non-existent transcription"),
            
            # Control endpoints
            ("POST", "/control/toggle-api-sending", 200, None, "Toggle API sending"),
            ("POST", "/control/start", 200, None, "Start pipeline"),
            ("POST", "/control/stop", 200, None, "Stop pipeline"),
            ("POST", "/control/start", 200, None, "Start pipeline again"),
            
            # Export endpoints
            ("POST", "/transcriptions/export", 200, None, "Export transcriptions"),
            ("POST", "/transcriptions/send-unsent", 200, None, "Send unsent transcriptions"),
            
            # API Documentation
            ("GET", "/api-docs", 200, None, "Swagger UI documentation"),
            ("GET", "/api-docs.json", 200, None, "OpenAPI specification"),
            
            # Non-existent endpoints
            ("GET", "/nonexistent", 404, None, "Non-existent GET endpoint"),
            ("POST", "/nonexistent", 404, None, "Non-existent POST endpoint"),
        ]
        
        results = []
        for i, (method, path, expected_status, data, description) in enumerate(tests, 1):
            print(f"\n🔍 Test {i:2d}/{len(tests)}: {method} {path}")
            print(f"    {description}")
            
            result = self.test_endpoint(method, path, expected_status, data, description)
            results.append(result)
            
            if result["success"]:
                print(f"    ✅ PASS - Status: {result['status_code']} - Time: {result['response_time']:.3f}s")
                if result["response_data"] and isinstance(result["response_data"], dict):
                    # Show some key information from response
                    if "message" in result["response_data"]:
                        print(f"       Message: {result['response_data']['message']}")
                    elif "total_count" in result["response_data"]:
                        print(f"       Count: {result['response_data']['total_count']}")
                    elif "pipeline_running" in result["response_data"]:
                        print(f"       Pipeline: {'Running' if result['response_data']['pipeline_running'] else 'Stopped'}")
            else:
                print(f"    ❌ FAIL - {result['error']}")
                if result["status_code"]:
                    print(f"       Status: {result['status_code']}")
                if result["response_data"]:
                    print(f"       Response: {str(result['response_data'])[:100]}...")
            
            # Small delay between tests
            time.sleep(0.5)
        
        return results
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """Generate a comprehensive test report"""
        print(f"\n📊 TEST REPORT")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = len([r for r in results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in results:
                if not result["success"]:
                    print(f"   {result['method']} {result['path']} - {result['error']}")
        
        # Performance summary
        response_times = [r["response_time"] for r in results if r["response_time"] is not None]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⏱️  PERFORMANCE:")
            print(f"   Average Response Time: {avg_time:.3f}s")
            print(f"   Max Response Time: {max_time:.3f}s")
        
        # Endpoint categories
        get_tests = [r for r in results if r["method"] == "GET"]
        post_tests = [r for r in results if r["method"] == "POST"]
        
        print(f"\n📋 BY METHOD:")
        print(f"   GET:  {len([r for r in get_tests if r['success']])}/{len(get_tests)} passed")
        print(f"   POST: {len([r for r in post_tests if r['success']])}/{len(post_tests)} passed")
        
        return passed_tests == total_tests

def main():
    """Main test function"""
    print("🧪 HTTP ENDPOINT COMPREHENSIVE TESTER")
    print("=" * 60)
    print("🎯 Testing all endpoints in mainWithServer.py")
    print("⚠️  This will start and stop the server automatically")
    print("=" * 60)
    
    tester = HTTPEndpointTester()
    
    try:
        # Start the server
        if not tester.start_server():
            print("❌ Failed to start server for testing")
            return False
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate report
        all_passed = tester.generate_report(results)
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED!")
            print("✅ All HTTP endpoints are functional")
        else:
            print(f"\n⚠️  SOME TESTS FAILED")
            print("❌ Check the failed endpoints above")
        
        return all_passed
        
    except KeyboardInterrupt:
        print(f"\n⚡ Testing interrupted by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        return False
        
    finally:
        # Always stop the server
        tester.stop_server()
        print("✅ Test completed!")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)