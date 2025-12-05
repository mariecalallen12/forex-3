"""
Comprehensive test cho authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_comprehensive_auth():
    print("🔐 COMPREHENSIVE AUTHENTICATION TESTS")
    print("=" * 60)
    
    # Test 1: Đăng nhập thành công
    print("\n1. Test Login (Thành công)")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Login thành công!")
        login_result = response.json()
        print(f"   Message: {login_result['message']}")
        print(f"   User: {login_result['data']['user']['email']}")
        print(f"   Token: {login_result['data']['token'][:50]}...")
    else:
        print(f"❌ Login thất bại: {response.text}")
    
    # Test 2: Đăng ký với thiếu thông tin
    print("\n2. Test Register (Thiếu thông tin)")
    register_data = {
        "email": "newuser@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print("✅ Validation error như mong đợi!")
        print(f"   Errors: {response.json()['detail']}")
    else:
        print(f"❌ Không mong đợi: {response.text}")
    
    # Test 3: Đăng ký với đầy đủ thông tin
    print("\n3. Test Register (Đầy đủ thông tin)")
    register_data_full = {
        "email": "newuser@example.com",
        "password": "password123",
        "displayName": "New User",
        "agreeToTerms": True,
        "referralCode": "REF001"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data_full)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✅ Register thành công!")
        register_result = response.json()
        print(f"   Message: {register_result['message']}")
        print(f"   User: {register_result['data']['user']['email']}")
        print(f"   Approval Status: {register_result['data']['user']['approvalStatus']}")
        print(f"   Needs Approval: {register_result['needsApproval']}")
    else:
        print(f"   Response: {response.text}")
    
    # Test 4: Đăng xuất
    print("\n4. Test Logout")
    response = requests.post(f"{BASE_URL}/api/auth/logout")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Logout thành công!")
        print(f"   Message: {response.json()['message']}")
    else:
        print(f"❌ Logout thất bại: {response.text}")
    
    # Test 5: Refresh token (không có token)
    print("\n5. Test Refresh Token (Không có token)")
    response = requests.post(f"{BASE_URL}/api/auth/refresh")
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Error như mong đợi!")
        print(f"   Error: {response.json()['message']}")
    else:
        print(f"❌ Không mong đợi: {response.text}")
    
    # Test 6: Verify token (không có token)
    print("\n6. Test Verify Token (Không có token)")
    response = requests.get(f"{BASE_URL}/api/auth/verify")
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Error như mong đợi!")
        print(f"   Error: {response.json()['message']}")
    else:
        print(f"❌ Không mong đợi: {response.text}")
    
    # Test 7: Login với sai thông tin
    print("\n7. Test Login (Sai thông tin)")
    wrong_login = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=wrong_login)
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Login failed như mong đợi!")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   Response: {response.text}")
    
    # Test 8: Rate limit check
    print("\n8. Test Rate Limit Status")
    response = requests.get(f"{BASE_URL}/api/auth/rate-limit/login")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Rate limit status retrieved!")
        rate_limit_data = response.json()
        print(f"   Endpoint: {rate_limit_data['endpoint']}")
        print(f"   Client IP: {rate_limit_data['client_ip']}")
        print(f"   Current requests: {rate_limit_data['status']['current_requests']}")
        print(f"   Max requests: {rate_limit_data['status']['max_requests']}")
    
    print("\n" + "=" * 60)
    print("🎉 COMPREHENSIVE AUTH TESTS COMPLETED!")

if __name__ == "__main__":
    test_comprehensive_auth()
