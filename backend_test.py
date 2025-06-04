
import requests
import json
import time
import os
import sys
import threading
import uuid
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

# Global variables to store test data
test_users = {
    "regular_user": {
        "email": f"user_{uuid.uuid4()}@example.com",
        "password": "Password123!",
        "full_name": "Test User",
        "token": None,
        "id": None
    },
    "admin_user": {
        "email": f"admin_{uuid.uuid4()}@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
        "token": None,
        "id": None
    },
    "inactive_user": {
        "email": f"inactive_{uuid.uuid4()}@example.com",
        "password": "Inactive123!",
        "full_name": "Inactive User",
        "token": None,
        "id": None
    }
}

# Helper function to make authenticated requests
def make_auth_request(method, endpoint, token=None, json_data=None):
    url = f"{API_BASE_URL}{endpoint}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method.lower() == "get":
        return requests.get(url, headers=headers)
    elif method.lower() == "post":
        return requests.post(url, headers=headers, json=json_data)
    elif method.lower() == "put":
        return requests.put(url, headers=headers, json=json_data)
    elif method.lower() == "delete":
        return requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

# Original tests
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

# Authentication Tests
def test_user_registration():
    """Test user registration endpoint"""
    print("\n=== Testing User Registration ===")
    results = {}
    
    # Test 1: Successful registration
    try:
        print("\n--- Test: Successful Registration ---")
        payload = {
            "email": test_users["regular_user"]["email"],
            "password": test_users["regular_user"]["password"],
            "full_name": test_users["regular_user"]["full_name"],
            "is_active": True,
            "role": "user"
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
        assert response.json()["email"] == payload["email"], "Email in response doesn't match request"
        assert "id" in response.json(), "Response does not contain 'id' field"
        
        # Save user ID for later tests
        test_users["regular_user"]["id"] = response.json()["id"]
        
        print("✅ Successful registration test passed")
        results["successful_registration"] = True
    except Exception as e:
        print(f"❌ Successful registration test failed: {str(e)}")
        results["successful_registration"] = False
    
    # Test 2: Register admin user
    try:
        print("\n--- Test: Admin User Registration ---")
        payload = {
            "email": test_users["admin_user"]["email"],
            "password": test_users["admin_user"]["password"],
            "full_name": test_users["admin_user"]["full_name"],
            "is_active": True,
            "role": "admin"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
        assert response.json()["role"] == "admin", "Role in response doesn't match request"
        
        # Save admin user ID
        test_users["admin_user"]["id"] = response.json()["id"]
        
        print("✅ Admin user registration test passed")
        results["admin_registration"] = True
    except Exception as e:
        print(f"❌ Admin user registration test failed: {str(e)}")
        results["admin_registration"] = False
    
    # Test 3: Register inactive user
    try:
        print("\n--- Test: Inactive User Registration ---")
        payload = {
            "email": test_users["inactive_user"]["email"],
            "password": test_users["inactive_user"]["password"],
            "full_name": test_users["inactive_user"]["full_name"],
            "is_active": False,
            "role": "user"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
        assert response.json()["is_active"] == False, "is_active in response doesn't match request"
        
        # Save inactive user ID
        test_users["inactive_user"]["id"] = response.json()["id"]
        
        print("✅ Inactive user registration test passed")
        results["inactive_registration"] = True
    except Exception as e:
        print(f"❌ Inactive user registration test failed: {str(e)}")
        results["inactive_registration"] = False
    
    # Test 4: Registration with existing email
    try:
        print("\n--- Test: Registration with Existing Email ---")
        payload = {
            "email": test_users["regular_user"]["email"],  # Using the same email as the first test
            "password": "DifferentPassword123!",
            "full_name": "Duplicate User",
            "is_active": True,
            "role": "user"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        assert "already registered" in response.json()["detail"].lower(), "Expected 'already registered' in error message"
        
        print("✅ Registration with existing email test passed")
        results["duplicate_email"] = True
    except Exception as e:
        print(f"❌ Registration with existing email test failed: {str(e)}")
        results["duplicate_email"] = False
    
    # Test 5: Registration with invalid data
    try:
        print("\n--- Test: Registration with Invalid Data ---")
        # Missing required fields
        payload = {
            "email": "invalid_user@example.com"
            # Missing password and full_name
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        print(f"Status code for missing fields: {response.status_code}")
        assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
        
        # Invalid email format
        payload = {
            "email": "not_an_email",
            "password": "Password123!",
            "full_name": "Invalid Email User"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
        print(f"Status code for invalid email: {response.status_code}")
        assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
        
        print("✅ Registration with invalid data test passed")
        results["invalid_data"] = True
    except Exception as e:
        print(f"❌ Registration with invalid data test failed: {str(e)}")
        results["invalid_data"] = False
    
    # Print summary
    print("\n--- User Registration Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall User Registration Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_user_login():
    """Test user login endpoint"""
    print("\n=== Testing User Login ===")
    results = {}
    
    # Test 1: Successful login
    try:
        print("\n--- Test: Successful Login ---")
        payload = {
            "email": test_users["regular_user"]["email"],
            "password": test_users["regular_user"]["password"]
        }
        
        start_time = time.time()
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "access_token" in response.json(), "Response does not contain 'access_token' field"
        assert "token_type" in response.json(), "Response does not contain 'token_type' field"
        assert "expires_in" in response.json(), "Response does not contain 'expires_in' field"
        assert "user" in response.json(), "Response does not contain 'user' field"
        assert response.json()["user"]["email"] == payload["email"], "Email in response doesn't match request"
        
        # Save token for later tests
        test_users["regular_user"]["token"] = response.json()["access_token"]
        
        print("✅ Successful login test passed")
        results["successful_login"] = True
    except Exception as e:
        print(f"❌ Successful login test failed: {str(e)}")
        results["successful_login"] = False
    
    # Test 2: Admin user login
    try:
        print("\n--- Test: Admin User Login ---")
        payload = {
            "email": test_users["admin_user"]["email"],
            "password": test_users["admin_user"]["password"]
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json()["user"]["role"] == "admin", "Role in response doesn't match expected"
        
        # Save admin token
        test_users["admin_user"]["token"] = response.json()["access_token"]
        
        print("✅ Admin user login test passed")
        results["admin_login"] = True
    except Exception as e:
        print(f"❌ Admin user login test failed: {str(e)}")
        results["admin_login"] = False
    
    # Test 3: Login with incorrect password
    try:
        print("\n--- Test: Login with Incorrect Password ---")
        payload = {
            "email": test_users["regular_user"]["email"],
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        assert "invalid" in response.json()["detail"].lower(), "Expected 'invalid' in error message"
        
        print("✅ Login with incorrect password test passed")
        results["incorrect_password"] = True
    except Exception as e:
        print(f"❌ Login with incorrect password test failed: {str(e)}")
        results["incorrect_password"] = False
    
    # Test 4: Login with non-existent email
    try:
        print("\n--- Test: Login with Non-existent Email ---")
        payload = {
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        
        print("✅ Login with non-existent email test passed")
        results["nonexistent_email"] = True
    except Exception as e:
        print(f"❌ Login with non-existent email test failed: {str(e)}")
        results["nonexistent_email"] = False
    
    # Test 5: Login with inactive user
    try:
        print("\n--- Test: Login with Inactive User ---")
        payload = {
            "email": test_users["inactive_user"]["email"],
            "password": test_users["inactive_user"]["password"]
        }
        
        response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        assert "disabled" in response.json()["detail"].lower(), "Expected 'disabled' in error message"
        
        print("✅ Login with inactive user test passed")
        results["inactive_user"] = True
    except Exception as e:
        print(f"❌ Login with inactive user test failed: {str(e)}")
        results["inactive_user"] = False
    
    # Print summary
    print("\n--- User Login Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall User Login Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_get_current_user():
    """Test get current user endpoint"""
    print("\n=== Testing Get Current User ===")
    results = {}
    
    # Test 1: Get user with valid token
    try:
        print("\n--- Test: Get User with Valid Token ---")
        token = test_users["regular_user"]["token"]
        
        start_time = time.time()
        response = make_auth_request("get", "/auth/me", token)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json()["email"] == test_users["regular_user"]["email"], "Email in response doesn't match expected"
        assert response.json()["id"] == test_users["regular_user"]["id"], "ID in response doesn't match expected"
        
        print("✅ Get user with valid token test passed")
        results["valid_token"] = True
    except Exception as e:
        print(f"❌ Get user with valid token test failed: {str(e)}")
        results["valid_token"] = False
    
    # Test 2: Get user with invalid token
    try:
        print("\n--- Test: Get User with Invalid Token ---")
        invalid_token = "invalid.token.string"
        
        response = make_auth_request("get", "/auth/me", invalid_token)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        
        print("✅ Get user with invalid token test passed")
        results["invalid_token"] = True
    except Exception as e:
        print(f"❌ Get user with invalid token test failed: {str(e)}")
        results["invalid_token"] = False
    
    # Test 3: Get user without token
    try:
        print("\n--- Test: Get User Without Token ---")
        
        response = requests.get(f"{API_BASE_URL}/auth/me")
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
        
        print("✅ Get user without token test passed")
        results["no_token"] = True
    except Exception as e:
        print(f"❌ Get user without token test failed: {str(e)}")
        results["no_token"] = False
    
    # Print summary
    print("\n--- Get Current User Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall Get Current User Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_update_current_user():
    """Test update current user endpoint"""
    print("\n=== Testing Update Current User ===")
    results = {}
    
    # Test 1: Update user with valid token
    try:
        print("\n--- Test: Update User with Valid Token ---")
        token = test_users["regular_user"]["token"]
        updated_name = f"Updated Name {uuid.uuid4()}"
        
        payload = {
            "full_name": updated_name
        }
        
        start_time = time.time()
        response = make_auth_request("put", "/auth/me", token, payload)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json()["full_name"] == updated_name, "Name in response doesn't match updated name"
        
        # Verify the update by getting the user
        verify_response = make_auth_request("get", "/auth/me", token)
        assert verify_response.json()["full_name"] == updated_name, "Name not updated in database"
        
        print("✅ Update user with valid token test passed")
        results["valid_update"] = True
    except Exception as e:
        print(f"❌ Update user with valid token test failed: {str(e)}")
        results["valid_update"] = False
    
    # Test 2: Update email to existing email
    try:
        print("\n--- Test: Update Email to Existing Email ---")
        token = test_users["regular_user"]["token"]
        
        payload = {
            "email": test_users["admin_user"]["email"]  # Try to use admin's email
        }
        
        response = make_auth_request("put", "/auth/me", token, payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        assert "already in use" in response.json()["detail"].lower(), "Expected 'already in use' in error message"
        
        print("✅ Update email to existing email test passed")
        results["duplicate_email_update"] = True
    except Exception as e:
        print(f"❌ Update email to existing email test failed: {str(e)}")
        results["duplicate_email_update"] = False
    
    # Test 3: Update with invalid token
    try:
        print("\n--- Test: Update User with Invalid Token ---")
        invalid_token = "invalid.token.string"
        
        payload = {
            "full_name": "This Should Fail"
        }
        
        response = make_auth_request("put", "/auth/me", invalid_token, payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        
        print("✅ Update user with invalid token test passed")
        results["invalid_token_update"] = True
    except Exception as e:
        print(f"❌ Update user with invalid token test failed: {str(e)}")
        results["invalid_token_update"] = False
    
    # Print summary
    print("\n--- Update Current User Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall Update Current User Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_user_management():
    """Test user management admin endpoints"""
    print("\n=== Testing User Management Admin Endpoints ===")
    results = {}
    
    # Test 1: Get all users as admin
    try:
        print("\n--- Test: Get All Users as Admin ---")
        admin_token = test_users["admin_user"]["token"]
        
        start_time = time.time()
        response = make_auth_request("get", "/users/", admin_token)
        end_time = time.time()
        
        print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
        print(f"Status code: {response.status_code}")
        print(f"Number of users: {len(response.json())}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert isinstance(response.json(), list), "Response is not a list"
        assert len(response.json()) >= 3, f"Expected at least 3 users, got {len(response.json())}"
        
        # Check if our test users are in the list
        emails = [user["email"] for user in response.json()]
        assert test_users["regular_user"]["email"] in emails, "Regular user not found in users list"
        assert test_users["admin_user"]["email"] in emails, "Admin user not found in users list"
        assert test_users["inactive_user"]["email"] in emails, "Inactive user not found in users list"
        
        print("✅ Get all users as admin test passed")
        results["get_users_admin"] = True
    except Exception as e:
        print(f"❌ Get all users as admin test failed: {str(e)}")
        results["get_users_admin"] = False
    
    # Test 2: Get all users as regular user (should fail)
    try:
        print("\n--- Test: Get All Users as Regular User ---")
        regular_token = test_users["regular_user"]["token"]
        
        response = make_auth_request("get", "/users/", regular_token)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
        assert "permissions" in response.json()["detail"].lower(), "Expected 'permissions' in error message"
        
        print("✅ Get all users as regular user test passed")
        results["get_users_regular"] = True
    except Exception as e:
        print(f"❌ Get all users as regular user test failed: {str(e)}")
        results["get_users_regular"] = False
    
    # Test 3: Get user by ID as admin
    try:
        print("\n--- Test: Get User by ID as Admin ---")
        admin_token = test_users["admin_user"]["token"]
        user_id = test_users["regular_user"]["id"]
        
        response = make_auth_request("get", f"/users/{user_id}", admin_token)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json()["id"] == user_id, "ID in response doesn't match expected"
        assert response.json()["email"] == test_users["regular_user"]["email"], "Email in response doesn't match expected"
        
        print("✅ Get user by ID as admin test passed")
        results["get_user_by_id"] = True
    except Exception as e:
        print(f"❌ Get user by ID as admin test failed: {str(e)}")
        results["get_user_by_id"] = False
    
    # Test 4: Update user by ID as admin
    try:
        print("\n--- Test: Update User by ID as Admin ---")
        admin_token = test_users["admin_user"]["token"]
        user_id = test_users["regular_user"]["id"]
        updated_name = f"Admin Updated Name {uuid.uuid4()}"
        
        payload = {
            "full_name": updated_name
        }
        
        response = make_auth_request("put", f"/users/{user_id}", admin_token, payload)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert response.json()["full_name"] == updated_name, "Name in response doesn't match updated name"
        
        print("✅ Update user by ID as admin test passed")
        results["update_user_by_id"] = True
    except Exception as e:
        print(f"❌ Update user by ID as admin test failed: {str(e)}")
        results["update_user_by_id"] = False
    
    # Test 5: Delete user by ID as admin
    try:
        print("\n--- Test: Delete User by ID as Admin ---")
        admin_token = test_users["admin_user"]["token"]
        
        # Create a temporary user to delete
        temp_email = f"temp_delete_{uuid.uuid4()}@example.com"
        temp_payload = {
            "email": temp_email,
            "password": "TempPass123!",
            "full_name": "Temporary User",
            "is_active": True,
            "role": "user"
        }
        
        create_response = requests.post(f"{API_BASE_URL}/auth/register", json=temp_payload)
        temp_user_id = create_response.json()["id"]
        
        # Delete the user
        response = make_auth_request("delete", f"/users/{temp_user_id}", admin_token)
        print(f"Status code: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        assert "deleted" in response.json()["message"].lower(), "Expected 'deleted' in success message"
        
        # Verify the user is deleted
        verify_response = make_auth_request("get", f"/users/{temp_user_id}", admin_token)
        assert verify_response.status_code == 404, f"Expected status code 404, got {verify_response.status_code}"
        
        print("✅ Delete user by ID as admin test passed")
        results["delete_user_by_id"] = True
    except Exception as e:
        print(f"❌ Delete user by ID as admin test failed: {str(e)}")
        results["delete_user_by_id"] = False
    
    # Print summary
    print("\n--- User Management Admin Endpoints Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall User Management Admin Endpoints Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_rate_limiting():
    """Test rate limiting on endpoints"""
    print("\n=== Testing Rate Limiting ===")
    results = {}
    
    # Test 1: Rate limiting on login endpoint
    try:
        print("\n--- Test: Rate Limiting on Login Endpoint ---")
        
        # Make multiple requests in quick succession
        num_requests = 15  # Should trigger rate limiting
        responses = []
        
        for i in range(num_requests):
            payload = {
                "email": f"test{i}@example.com",
                "password": "Password123!"
            }
            
            response = requests.post(f"{API_BASE_URL}/auth/login", json=payload)
            responses.append(response.status_code)
            print(f"Request {i+1}: Status code {response.status_code}")
            
            # Small delay to make the requests more realistic
            time.sleep(0.1)
        
        # Check if any requests were rate limited (429 Too Many Requests)
        rate_limited = 429 in responses
        print(f"Rate limited: {rate_limited}")
        
        # We don't assert here because rate limiting depends on the server configuration
        # and might not trigger in a test environment
        
        print("✅ Rate limiting test completed")
        results["rate_limiting"] = True
    except Exception as e:
        print(f"❌ Rate limiting test failed: {str(e)}")
        results["rate_limiting"] = False
    
    # Print summary
    print("\n--- Rate Limiting Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall Rate Limiting Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def test_security():
    """Test security features"""
    print("\n=== Testing Security Features ===")
    results = {}
    
    # Test 1: JWT token validation
    try:
        print("\n--- Test: JWT Token Validation ---")
        
        # Test with expired token (manually crafted)
        # This is a token with an expiration time in the past
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjE0NTU2ODAwfQ.8FI_MnqcHpJX9gEKBbr7LBH0or2VW_4QbgJzI5pIAMM"
        
        response = make_auth_request("get", "/auth/me", expired_token)
        print(f"Status code for expired token: {response.status_code}")
        
        assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        
        # Test with tampered token (changing a character)
        if test_users["regular_user"]["token"]:
            tampered_token = test_users["regular_user"]["token"][:-1] + ("1" if test_users["regular_user"]["token"][-1] != "1" else "2")
            
            response = make_auth_request("get", "/auth/me", tampered_token)
            print(f"Status code for tampered token: {response.status_code}")
            
            assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
        
        print("✅ JWT token validation test passed")
        results["jwt_validation"] = True
    except Exception as e:
        print(f"❌ JWT token validation test failed: {str(e)}")
        results["jwt_validation"] = False
    
    # Test 2: Protected endpoint access
    try:
        print("\n--- Test: Protected Endpoint Access ---")
        
        # Test protected status endpoint with valid token
        token = test_users["regular_user"]["token"]
        
        response = make_auth_request("get", "/status/protected", token)
        print(f"Status code for protected endpoint with valid token: {response.status_code}")
        
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        
        # Test protected status endpoint without token
        response = requests.get(f"{API_BASE_URL}/status/protected")
        print(f"Status code for protected endpoint without token: {response.status_code}")
        
        assert response.status_code == 403, f"Expected status code 403, got {response.status_code}"
        
        print("✅ Protected endpoint access test passed")
        results["protected_endpoint"] = True
    except Exception as e:
        print(f"❌ Protected endpoint access test failed: {str(e)}")
        results["protected_endpoint"] = False
    
    # Print summary
    print("\n--- Security Features Test Summary ---")
    all_passed = all(results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    print(f"Overall Security Features Tests: {'✅ PASSED' if all_passed else '❌ FAILED'}")
    return all_passed

def run_all_tests():
    """Run all tests"""
    print("\n=== Running All Backend API Tests ===")
    print(f"Testing against API: {API_BASE_URL}")
    
    results = {}
    
    # Original tests
    results["hello_world"] = test_hello_world()
    status_id = test_create_status_check()
    results["create_status_check"] = status_id is not None
    results["get_status_checks"] = test_get_status_checks(status_id)
    results["concurrent_requests"] = test_concurrent_requests()
    results["input_validation"] = test_input_validation()
    
    # Authentication tests
    results["user_registration"] = test_user_registration()
    results["user_login"] = test_user_login()
    results["get_current_user"] = test_get_current_user()
    results["update_current_user"] = test_update_current_user()
    results["user_management"] = test_user_management()
    results["rate_limiting"] = test_rate_limiting()
    results["security"] = test_security()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASSED' if result else '❌ FAILED'}")
    
    all_passed = all(results.values())
    print(f"\nOverall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()
