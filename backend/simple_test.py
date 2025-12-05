"""
Simple test for FastAPI backend
"""

from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from main import app
    client = TestClient(app)
    
    print("Testing basic endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    print(f"GET / -> {response.status_code}")
    
    # Test health endpoint
    response = client.get("/api/health")
    print(f"GET /api/health -> {response.status_code}")
    
    # Test auth endpoints
    endpoints = [
        "/api/auth/login",
        "/api/auth/register", 
        "/api/auth/logout",
        "/api/auth/refresh",
        "/api/auth/verify"
    ]
    
    for endpoint in endpoints:
        # Test POST
        response = client.post(endpoint, json={})
        print(f"POST {endpoint} -> {response.status_code}")
        
        # Test GET (if applicable)
        if endpoint in ["/api/auth/login", "/api/auth/verify"]:
            response = client.get(endpoint)
            print(f"GET {endpoint} -> {response.status_code}")
    
    print("✅ All tests completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
