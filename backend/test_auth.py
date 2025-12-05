"""
Test Authentication Endpoints
Kiểm tra hoạt động của authentication system đã migrate từ Next.js
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import status
import json

# Import the main app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from main import app

client = TestClient(app)

class TestAuthenticationEndpoints:
    """Test suite for authentication endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint - migrated from Next.js"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend"
        assert data["version"] == "2.0.0"
        print("✅ Health check endpoint working")
    
    def test_login_endpoint_exists(self):
        """Test login endpoint exists and accepts requests"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        # Should return error for invalid credentials, but endpoint should exist
        assert response.status_code in [401, 422]  # 401 for auth error, 422 for validation
        print("✅ Login endpoint exists and responding")
    
    def test_register_endpoint_exists(self):
        """Test register endpoint exists and accepts requests"""
        register_data = {
            "email": "newuser@example.com",
            "password": "password123",
            "displayName": "Test User",
            "agreeToTerms": True,
            "referralCode": "REF001"
        }
        
        response = client.post("/api/auth/register", json=register_data)
        # Should return error for validation or business logic, but endpoint should exist
        assert response.status_code in [400, 422]  # 400 for business logic, 422 for validation
        print("✅ Register endpoint exists and responding")
    
    def test_logout_endpoint_exists(self):
        """Test logout endpoint exists"""
        headers = {"Authorization": "Bearer fake_token"}
        response = client.post("/api/auth/logout", headers=headers)
        # Should return 200 even with invalid token (matching Next.js behavior)
        assert response.status_code == 200
        print("✅ Logout endpoint exists and responding")
    
    def test_refresh_token_endpoint_exists(self):
        """Test refresh token endpoint exists"""
        headers = {"Authorization": "Bearer fake_token"}
        response = client.post("/api/auth/refresh", headers=headers)
        # Should return 401 for invalid token, but endpoint should exist
        assert response.status_code == 401
        print("✅ Refresh token endpoint exists and responding")
    
    def test_verify_token_endpoint_exists(self):
        """Test verify token endpoint exists"""
        headers = {"Authorization": "Bearer fake_token"}
        response = client.get("/api/auth/verify", headers=headers)
        # Should return 401 for invalid token, but endpoint should exist
        assert response.status_code == 401
        print("✅ Verify token endpoint exists and responding")
    
    def test_login_get_method_verification(self):
        """Test GET method on login endpoint (for token verification)"""
        headers = {"Authorization": "Bearer fake_token"}
        response = client.get("/api/auth/login", headers=headers)
        # Should return 401 for invalid token, but GET should work
        assert response.status_code == 401
        print("✅ GET method on login endpoint working (token verification)")
    
    def test_rate_limit_endpoint_exists(self):
        """Test rate limit status endpoint exists"""
        response = client.get("/api/auth/rate-limit/login")
        assert response.status_code == 200
        data = response.json()
        assert "endpoint" in data
        assert "client_ip" in data
        assert "status" in data
        print("✅ Rate limit status endpoint exists")
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "health" in data
        print("✅ Root endpoint working")
    
    def test_api_structure_consistency(self):
        """Test API structure matches Next.js version"""
        # Test that API routes exist
        endpoints_to_test = [
            ("GET", "/api/health"),
            ("POST", "/api/auth/login"),
            ("GET", "/api/auth/login"),
            ("POST", "/api/auth/register"),
            ("POST", "/api/auth/logout"),
            ("POST", "/api/auth/refresh"),
            ("GET", "/api/auth/verify"),
        ]
        
        for method, endpoint in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            # All endpoints should exist and return valid responses
            assert response.status_code in [200, 400, 401, 422, 429], f"Endpoint {method} {endpoint} not working"
        
        print("✅ API structure matches Next.js version")

def test_main():
    """Main test runner"""
    print("🧪 Starting Authentication System Tests...")
    print("=" * 60)
    
    test_instance = TestAuthenticationEndpoints()
    
    # Run all tests
    tests = [
        ("Health Check", test_instance.test_health_check),
        ("Login Endpoint", test_instance.test_login_endpoint_exists),
        ("Register Endpoint", test_instance.test_register_endpoint_exists),
        ("Logout Endpoint", test_instance.test_logout_endpoint_exists),
        ("Refresh Token Endpoint", test_instance.test_refresh_token_endpoint_exists),
        ("Verify Token Endpoint", test_instance.test_verify_token_endpoint_exists),
        ("Login GET Method", test_instance.test_login_get_method_verification),
        ("Rate Limit Endpoint", test_instance.test_rate_limit_endpoint_exists),
        ("Root Endpoint", test_instance.test_root_endpoint),
        ("API Structure Consistency", test_instance.test_api_structure_consistency),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Testing: {test_name}")
            test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            print(f"❌ {test_name} FAILED: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication system is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = test_main()
    exit(0 if success else 1)
