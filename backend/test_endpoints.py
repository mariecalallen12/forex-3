"""
Test endpoints directly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, headers=None):
    try:
        if method.upper() == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method.upper() == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
        
        print(f"{method} {endpoint} -> {response.status_code}")
        print(f"Response: {response.text[:200]}")
        print()
        
    except Exception as e:
        print(f"Error testing {method} {endpoint}: {str(e)}")

print("Testing Digital Utopia FastAPI Backend")
print("=" * 50)

# Test basic endpoints
test_endpoint("GET", "/")
test_endpoint("GET", "/api/health")

# Test auth endpoints
auth_data = {"email": "test@example.com", "password": "password123"}
headers = {"Content-Type": "application/json"}

test_endpoint("POST", "/api/auth/login", auth_data, headers)
test_endpoint("GET", "/api/auth/login", headers=headers)
test_endpoint("POST", "/api/auth/register", auth_data, headers)
test_endpoint("POST", "/api/auth/logout", headers=headers)
test_endpoint("POST", "/api/auth/refresh", headers=headers)
test_endpoint("GET", "/api/auth/verify", headers=headers)

print("✅ All tests completed!")
