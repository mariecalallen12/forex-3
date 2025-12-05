"""
Dependencies Module
Digital Utopia Platform

Dependency injection cho FastAPI endpoints
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .db.session import SessionLocal, get_db
from .db.redis_client import redis_client, RedisCache, get_redis
from .services.user_service import UserService
from .services.trading_service import TradingService
from .services.financial_service import FinancialService
from .services.cache_service import CacheService
from .core.security import verify_access_token
from .models.user import User

# Security
security = HTTPBearer()


# =============== Database Dependencies ===============

def get_user_service(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_redis)
) -> UserService:
    """
    Dependency để inject UserService vào endpoints
    
    Sử dụng:
        @router.get("/users")
        def get_users(service: UserService = Depends(get_user_service)):
            return service.list_users()
    """
    return UserService(db, cache)


def get_trading_service(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_redis)
) -> TradingService:
    """
    Dependency để inject TradingService vào endpoints
    """
    return TradingService(db, cache)


def get_financial_service(
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_redis)
) -> FinancialService:
    """
    Dependency để inject FinancialService vào endpoints
    """
    return FinancialService(db, cache)


def get_cache_service(
    cache: RedisCache = Depends(get_redis)
) -> CacheService:
    """
    Dependency để inject CacheService vào endpoints
    """
    return CacheService(cache)


# =============== Authentication Dependencies ===============

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    cache: RedisCache = Depends(get_redis)
) -> User:
    """
    Dependency để lấy current user từ JWT token
    
    Sử dụng:
        @router.get("/me")
        def get_me(user: User = Depends(get_current_user)):
            return user
    """
    token = credentials.credentials
    
    # Verify token
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user_id from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa thông tin người dùng",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check cache first
    cache_service = CacheService(cache)
    cached_user = cache_service.get_user(int(user_id))
    if cached_user:
        # Return cached user data
        user = User()
        for key, value in cached_user.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user
    
    # Query database
    user_service = UserService(db, cache)
    user = user_service.get_by_id(int(user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if user.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản đã bị xóa",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if user.status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị tạm khóa"
        )
    
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Dependency để lấy current active user (status = active)
    """
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa được kích hoạt"
        )
    return user


async def get_current_verified_user(
    user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency để lấy current verified user (KYC verified)
    """
    if user.kyc_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản chưa xác minh KYC"
        )
    return user


# =============== Role-based Access Control ===============

def require_role(allowed_roles: list):
    """
    Dependency factory để kiểm tra role của user
    
    Sử dụng:
        @router.get("/admin")
        def admin_only(user: User = Depends(require_role(["admin", "owner"]))):
            return {"message": "Admin access"}
    """
    async def role_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's role
        if user.role and user.role.name in allowed_roles:
            return user
        
        # Fallback: check role_id directly
        if user.role_id:
            from .models.user import Role
            role = db.query(Role).filter(Role.id == user.role_id).first()
            if role and role.name in allowed_roles:
                return user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Yêu cầu quyền: {', '.join(allowed_roles)}"
        )
    
    return role_checker


def require_permission(permission_name: str):
    """
    Dependency factory để kiểm tra permission của user
    
    Sử dụng:
        @router.post("/users")
        def create_user(user: User = Depends(require_permission("user.create"))):
            return {"message": "Permission granted"}
    """
    async def permission_checker(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Check if user has permission through role
        if user.role and user.role.permissions:
            for perm in user.role.permissions:
                if perm.name == permission_name:
                    return user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Yêu cầu quyền: {permission_name}"
        )
    
    return permission_checker


# =============== Rate Limiting ===============

def rate_limit(limit: int = 60, window: int = 60):
    """
    Dependency factory cho rate limiting
    
    Args:
        limit: Số request tối đa
        window: Thời gian window (seconds)
    
    Sử dụng:
        @router.get("/api/data")
        def get_data(
            _: None = Depends(rate_limit(100, 60)),
            user: User = Depends(get_current_user)
        ):
            return {"data": "..."}
    """
    async def check_rate_limit(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        cache: RedisCache = Depends(get_redis)
    ):
        # Use token as identifier
        identifier = f"rate_limit:{credentials.credentials[:20]}"
        
        cache_service = CacheService(cache)
        allowed, remaining = cache_service.check_rate_limit(identifier, limit, window)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Quá nhiều request. Vui lòng thử lại sau.",
                headers={"X-RateLimit-Remaining": "0"}
            )
        
        return None
    
    return check_rate_limit
