"""
Middleware cho Authentication và Rate Limiting
Migration từ Next.js lib/middleware/auth và lib/middleware/rate-limit
"""

import os
import time
import asyncio
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import jwt
# from jwt import PyJWTError
from datetime import datetime, timedelta
# import redis  # TODO: Enable when Redis is available
import json

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 1

# Redis Configuration for rate limiting
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = None

# Rate limiting configuration
RATE_LIMITS = {
    "login": {"requests": 5, "window": 900},  # 5 requests per 15 minutes
    "register": {"requests": 3, "window": 3600},  # 3 requests per hour
    "login_failed": {"requests": 3, "window": 900},  # 3 failed attempts per 15 minutes
    "general": {"requests": 100, "window": 3600},  # 100 requests per hour
}

security = HTTPBearer()

class AuthenticationError(HTTPException):
    """Custom exception for authentication errors"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

class RateLimitError(HTTPException):
    """Custom exception for rate limiting errors"""
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )

class TokenValidationError(HTTPException):
    """Custom exception for token validation errors"""
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

# ========== RATE LIMITING FUNCTIONS ==========

async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    if redis_client is None:
        try:
            # redis_client = redis.from_url(REDIS_URL, decode_responses=True)  # TODO: Enable when Redis is available
            # Test connection
            # await redis_client.ping()  # TODO: Enable when Redis is available
            redis_client = None  # Disable Redis for now
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}")
            redis_client = None

async def rate_limit(client_ip: str, endpoint: str) -> None:
    """
    Rate limiting function - tương tự Next.js rateLimit
    """
    await init_redis()
    
    if redis_client is None:
        # Skip rate limiting if Redis is not available
        return
    
    try:
        # Get rate limit config
        config = RATE_LIMITS.get(endpoint, RATE_LIMITS["general"])
        max_requests = config["requests"]
        window_seconds = config["window"]
        
        # Create Redis key
        key = f"rate_limit:{endpoint}:{client_ip}"
        
        # Get current request count
        current_requests = await redis_client.get(key)
        
        if current_requests is None:
            # First request in window
            await redis_client.setex(key, window_seconds, 1)
        else:
            current_requests = int(current_requests)
            
            if current_requests >= max_requests:
                # Rate limit exceeded
                raise RateLimitError(
                    detail=f"Quá nhiều yêu cầu. Vui lòng thử lại sau {window_seconds // 60} phút."
                )
            
            # Increment counter
            await redis_client.incr(key)
        
        return True
        
    except RateLimitError:
        raise
    except Exception as e:
        print(f"Rate limiting error: {e}")
        # Continue if rate limiting fails
        return True

async def check_rate_limit(client_ip: str, endpoint: str) -> Dict[str, Any]:
    """
    Check current rate limit status
    """
    await init_redis()
    
    if redis_client is None:
        return {
            "current_requests": 0,
            "max_requests": RATE_LIMITS.get(endpoint, RATE_LIMITS["general"])["requests"],
            "window_seconds": RATE_LIMITS.get(endpoint, RATE_LIMITS["general"])["window"],
        }
    
    try:
        config = RATE_LIMITS.get(endpoint, RATE_LIMITS["general"])
        key = f"rate_limit:{endpoint}:{client_ip}"
        
        current_requests = await redis_client.get(key)
        current_requests = int(current_requests) if current_requests else 0
        
        ttl = await redis_client.ttl(key)
        
        return {
            "current_requests": current_requests,
            "max_requests": config["requests"],
            "window_seconds": config["window"],
            "remaining_requests": max(0, config["requests"] - current_requests),
            "reset_in_seconds": max(0, ttl) if ttl > 0 else config["window"]
        }
        
    except Exception as e:
        print(f"Rate limit check error: {e}")
        return {
            "current_requests": 0,
            "max_requests": config["requests"],
            "window_seconds": config["window"],
        }

# ========== JWT TOKEN FUNCTIONS ==========

def create_access_token(user_data: Dict[str, Any]) -> str:
    """
    Tạo JWT access token - tương tự Firebase ID token
    """
    now = datetime.utcnow()
    expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    payload = {
        "uid": user_data["uid"],
        "email": user_data["email"],
        "email_verified": user_data.get("email_verified", False),
        "display_name": user_data.get("display_name"),
        "photo_url": user_data.get("photo_url"),
        "disabled": user_data.get("disabled", False),
        "iat": now,
        "exp": expire,
        "iss": "digital-utopia-fastapi",
        "aud": "digital-utopia-client"
    }
    
    # token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # return token
    return f"mock_token_{payload.get('uid', 'unknown')}"  # Mock token for development

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token - Mock version for development
    """
    # Mock verification - accept any token in development
    if not token:
        raise TokenValidationError("Token không hợp lệ")
    
    # Return mock payload
    return {
        "uid": "mock_user",
        "email": "mock@example.com",
        "display_name": "Mock User",
        "iss": "digital-utopia-fastapi",
        "aud": "digital-utopia-client"
    }

# ========== AUTHENTICATION HELPERS ==========

async def get_current_user(credentials: HTTPAuthorizationCredentials = security) -> Dict[str, Any]:
    """
    Get current authenticated user - tương tự Next.js auth middleware
    """
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        return {
            "uid": payload["uid"],
            "email": payload["email"],
            "email_verified": payload.get("email_verified", False),
            "display_name": payload.get("display_name"),
            "photo_url": payload.get("photo_url"),
            "disabled": payload.get("disabled", False),
        }
        
    except TokenValidationError as e:
        raise AuthenticationError(str(e))
    except Exception as e:
        raise AuthenticationError("Không thể xác thực người dùng")

async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated (optional) - tương tự Next.js optional auth
    """
    try:
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = verify_token(token)
        
        return {
            "uid": payload["uid"],
            "email": payload["email"],
            "email_verified": payload.get("email_verified", False),
            "display_name": payload.get("display_name"),
            "photo_url": payload.get("photo_url"),
            "disabled": payload.get("disabled", False),
        }
        
    except TokenValidationError:
        return None
    except Exception:
        return None

def get_client_ip(request: Request) -> str:
    """
    Get client IP address - tương tự Next.js
    """
    # Check for forwarded headers first (for proxies/load balancers)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP if multiple IPs are present
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback to client host
    client_host = getattr(request.client, "host", "unknown")
    return client_host if client_host else "unknown"

# ========== REFFERAL TOKEN EXTRACTION ==========

def extract_referral_token(request: Request) -> Optional[str]:
    """
    Extract referral token from request - tương tự Next.js extractReferralToken
    """
    # Check query parameters
    ref_token = request.query_params.get("ref")
    if ref_token:
        return ref_token
    
    # Check headers
    ref_header = request.headers.get("x-referral-token")
    if ref_header:
        return ref_header
    
    # Check cookies
    ref_cookie = request.cookies.get("referral_token")
    if ref_cookie:
        return ref_cookie
    
    return None

# ========== FIREBASE REPLACEMENT FUNCTIONS ==========

# These functions will replace Firebase Auth functionality in migration
# For now, they're placeholder implementations that match the Firebase interface

async def sign_in_with_email_and_password(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in with email and password - Firebase replacement
    """
    # TODO: Implement with your own authentication system
    # This is a placeholder that matches Firebase interface
    return {
        "user": {
            "uid": "user_123456789",
            "email": email,
            "emailVerified": False,
            "displayName": "Test User",
            "photoURL": None,
            "disabled": False,
        },
        "refresh_token": "refresh_token_placeholder"
    }

async def create_user_with_email_and_password(email: str, password: str, display_name: str) -> Dict[str, Any]:
    """
    Create user with email and password - Firebase replacement
    """
    # TODO: Implement with your own authentication system
    return {
        "user": {
            "uid": "user_" + str(int(time.time())),
            "email": email,
            "emailVerified": False,
            "displayName": display_name,
            "photoURL": None,
            "disabled": False,
        }
    }

async def sign_out() -> None:
    """
    Sign out current user - Firebase replacement
    """
    # TODO: Implement token revocation
    pass

async def revoke_refresh_token(user_uid: str) -> None:
    """
    Revoke refresh token - Firebase replacement
    """
    # TODO: Implement token revocation in Redis/database
    pass

# ========== EMAIL FUNCTIONS ==========

async def send_email(email_data: Dict[str, Any]) -> bool:
    """
    Send email using SendGrid - tương tự Next.js sendEmail
    """
    # TODO: Implement SendGrid integration
    # Placeholder implementation
    print(f"Sending email to {email_data.get('to')}")
    print(f"Subject: {email_data.get('subject')}")
    print(f"Template: {email_data.get('template')}")
    print(f"Data: {email_data.get('data')}")
    return True

# ========== UTILITY FUNCTIONS ==========

async def cleanup_redis_connections():
    """Cleanup Redis connections"""
    global redis_client
    if redis_client:
        try:
            await redis_client.close()
        except Exception as e:
            print(f"Redis cleanup error: {e}")
        finally:
            redis_client = None

def get_error_message(error: Exception, error_type: str = "general") -> str:
    """
    Get appropriate error message based on error type - tương tự Next.js error handling
    """
    error_messages = {
        "auth": {
            "user-not-found": "Tài khoản không tồn tại",
            "wrong-password": "Mật khẩu không đúng",
            "email-already-in-use": "Email đã được sử dụng",
            "invalid-email": "Email không hợp lệ",
            "weak-password": "Mật khẩu quá yếu",
            "too-many-requests": "Quá nhiều lần đăng nhập thất bại. Vui lòng thử lại sau",
            "user-disabled": "Tài khoản đã bị vô hiệu hóa",
        },
        "validation": {
            "invalid-input": "Dữ liệu đầu vào không hợp lệ",
            "required-field": "Trường dữ liệu bắt buộc",
        }
    }
    
    if hasattr(error, "code"):
        return error_messages.get(error_type, {}).get(error.code, "Đã xảy ra lỗi")

# ========== ADMIN ROLE FUNCTIONS ==========

async def get_user_data(user_id: str) -> Dict[str, Any]:
    """
    Get user data from database - replacement for Firestore query
    """
    # TODO: Replace with actual database query
    # Mock user data for demonstration
    return {
        "email": f"user_{user_id}@example.com",
        "role": "user",
        "kycStatus": "verified",
        "isActive": True,
        "phoneVerified": True,
        "balance": {
            "usdt": 1000.50,
            "btc": 0.05,
            "eth": 0.1,
            "vnd": 5000000,
            "usd": 800.25
        },
        "displayName": f"User {user_id}",
        "createdAt": "2024-01-01User {user_idT00:00:00Z"
    }

def require_admin_role(decoded_token: Dict[str, Any]) -> bool:
    """
    Check if user has admin role - tương tự Next.js requireRole middleware
    """
    # TODO: Replace with actual database role check
    # Check token for admin role
    user_role = decoded_token.get("role", "user")
    
    # Allow admin and superadmin roles
    admin_roles = ["admin", "superadmin"]
    
    # For now, allow any user with admin role in token
    # In production, this should query the database to verify current role
    return user_role in admin_roles
    
    return str(error) if str(error) else "Đã xảy ra lỗi không xác định"
