
import requests
import json
import time
import os
import sys
from datetime import datetime

# Get the backend URL from the frontend .env file
def get_backend_url():
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.strip().split('=')[1].strip('"')
    return None

BACKEND_URL = get_backend_url()
if not BACKEND_URL:
    print("Error: Could not find REACT_APP_BACKEND_URL in frontend/.env")
    sys.exit(1)

API_BASE_URL = f"{BACKEND_URL}/api"
print(f"Using API base URL: {API_BASE_URL}")

def test_hello_world():
    """Test the Hello World endpoint"""
    print("\n=== Testing Hello World Endpoint ===")
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/")
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json() == {"message": "Hello World"}, f"Unexpected response: {response.json()}"
        
        print("✅ Hello World endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Hello World endpoint test failed: {str(e)}")
        return False

def test_create_status_check():
    """Test creating a status check"""
    print("\n=== Testing Create Status Check Endpoint ===")
    try:
        client_name = f"test_client_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {"client_name": client_name}
        
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/status", json=payload)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "id" in response.json(), "Response does not contain 'id' field"
        assert response.json()["client_name"] == client_name, f"Expected client_name {client_name}, got {response.json()['client_name']}"
        
        print("✅ Create Status Check endpoint test passed")
        return response.json()["id"]
    except Exception as e:
        print(f"❌ Create Status Check endpoint test failed: {str(e)}")
        return None

def test_get_status_checks(expected_id=None):
    """Test retrieving status checks"""
    print("\n=== Testing Get Status Checks Endpoint ===")
    try:
        start_time = time.time()
        response = requests.get(f"{API_BASE_URL}/status")
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        print(f"Number of status checks: {len(response.json())}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert isinstance(response.json(), list), "Response is not a list"
        
        if expected_id:
            found = False
            for status in response.json():
                if status["id"] == expected_id:
                    found = True
                    break
            assert found, f"Could not find status check with id {expected_id} in the response"
            print(f"✅ Found status check with id {expected_id}")
        
        print("✅ Get Status Checks endpoint test passed")
        return True
    except Exception as e:
        print(f"❌ Get Status Checks endpoint test failed: {str(e)}")
        return False

def test_concurrent_requests():
    """Test handling of concurrent requests"""
    print("\n=== Testing Concurrent Requests ===")
    try:
        import threading
        
        success_count = 0
        failure_count = 0
        num_requests = 10
        
        def make_request():
            nonlocal success_count, failure_count
            try:
                client_name = f"concurrent_test_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                payload = {"client_name": client_name}
                response = requests.post(f"{API_BASE_URL}/status", json=payload)
                if response.status_code == 200:
                    success_count += 1
                else:
                    failure_count += 1
            except Exception:
                failure_count += 1
        
        threads = []
        start_time = time.time()
        
        for _ in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        print(f"Concurrent requests completed in {(end_time - start_time) * 1000:.2f} ms")
        print(f"Success: {success_count}, Failures: {failure_count}")
        
        assert success_count == num_requests, f"Expected {num_requests} successful requests, got {success_count}"
        
        print("✅ Concurrent requests test passed")
        return True
    except Exception as e:
        print(f"❌ Concurrent requests test failed: {str(e)}")
        return False

def test_input_validation():
    """Test input validation"""
    print("\n=== Testing Input Validation ===")
    try:
        # Test with missing client_name
        payload = {}
        response = requests.post(f"{API_BASE_URL}/status", json=payload)
        print(f"Status code for missing client_name: {response.status_code}")
        assert response.status_code != 200, "Expected error for missing client_name"
        
        # Test with empty client_name
        payload = {"client_name": ""}
        response = requests.post(f"{API_BASE_URL}/status", json=payload)
        print(f"Status code for empty client_name: {response.status_code}")
        
        # Test with very long client_name
        payload = {"client_name": "a" * 1000}
        response = requests.post(f"{API_BASE_URL}/status", json=payload)
        print(f"Status code for very long client_name: {response.status_code}")
        assert response.status_code == 200, f"Expected status code 200 for long client_name, got {response.status_code}"
        
        print("✅ Input validation test passed")
        return True
    except Exception as e:
        print(f"❌ Input validation test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n=== Running All Backend API Tests ===")
    print(f"Testing against API: {API_BASE_URL}")
    
    results = {}
    
    # Test Hello World endpoint
    results["hello_world"] = test_hello_world()
    
    # Test Create Status Check endpoint
    status_id = test_create_status_check()
    results["create_status_check"] = status_id is not None
    
    # Test Get Status Checks endpoint
    results["get_status_checks"] = test_get_status_checks(status_id)
    
    # Test concurrent requests
    results["concurrent_requests"] = test_concurrent_requests()
    
    # Test input validation
    results["input_validation"] = test_input_validation()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    all_passed = all(results.values())
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
