"""
Bảo mật - Security Module
Digital Utopia Platform

Quản lý JWT tokens, password hashing, và các chức năng bảo mật
"""

from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Xác thực password
    
    Args:
        plain_password: Password người dùng nhập
        hashed_password: Password đã hash trong database
        
    Returns:
        True nếu password khớp
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password
    
    Args:
        password: Password cần hash
        
    Returns:
        Password đã được hash
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT access token
    
    Args:
        data: Dữ liệu để encode vào token
        expires_delta: Thời gian hết hạn (mặc định: ACCESS_TOKEN_EXPIRE_MINUTES)
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Tạo JWT refresh token
    
    Args:
        data: Dữ liệu để encode vào token
        expires_delta: Thời gian hết hạn (mặc định: REFRESH_TOKEN_EXPIRE_DAYS)
        
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Xác thực và decode JWT token
    
    Args:
        token: JWT token cần xác thực
        
    Returns:
        Payload của token nếu hợp lệ, None nếu không hợp lệ
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Xác thực access token
    
    Args:
        token: JWT access token
        
    Returns:
        Payload nếu là access token hợp lệ
    """
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Xác thực refresh token
    
    Args:
        token: JWT refresh token
        
    Returns:
        Payload nếu là refresh token hợp lệ
    """
    payload = verify_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None
