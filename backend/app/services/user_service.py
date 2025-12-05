"""
User Service
Digital Utopia Platform

Business logic cho User operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from ..models.user import User, UserProfile, Role
from ..core.security import get_password_hash, verify_password
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class cho User operations
    
    Cung cấp business logic cho:
    - Tạo, cập nhật, xóa user
    - Authentication
    - Profile management
    - Cache management
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo UserService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== User CRUD ===============
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Lấy user theo ID
        
        Args:
            user_id: User ID
            
        Returns:
            User hoặc None
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get_cached_user(user_id)
            if cached:
                logger.debug(f"User {user_id} retrieved from cache")
                return self._dict_to_user(cached)
        
        # Query database
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Cache result
        if user and self.cache:
            self.cache.cache_user(user_id, self._user_to_dict(user))
        
        return user
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Lấy user theo email
        
        Args:
            email: Email address
            
        Returns:
            User hoặc None
        """
        return self.db.query(User).filter(User.email == email.lower()).first()
    
    def create(
        self,
        email: str,
        password: str,
        role_name: str = "customer",
        referral_code: Optional[str] = None
    ) -> User:
        """
        Tạo user mới
        
        Args:
            email: Email address
            password: Plain text password
            role_name: Tên role (default: customer)
            referral_code: Mã giới thiệu (optional)
            
        Returns:
            User mới được tạo
        """
        # Get role
        role = self.db.query(Role).filter(Role.name == role_name).first()
        
        # Create user
        user = User(
            email=email.lower(),
            password_hash=get_password_hash(password),
            role_id=role.id if role else None,
            referral_code=referral_code,
            status="pending"
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Create empty profile
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        self.db.commit()
        
        logger.info(f"User created: {user.id} ({email})")
        return user
    
    def update(self, user_id: int, data: Dict[str, Any]) -> Optional[User]:
        """
        Cập nhật user
        
        Args:
            user_id: User ID
            data: Dữ liệu cập nhật
            
        Returns:
            User đã cập nhật hoặc None
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Update allowed fields
        allowed_fields = ['status', 'email_verified', 'phone_verified', 'kyc_status']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        self.db.commit()
        self.db.refresh(user)
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_user_cache(user_id)
        
        logger.info(f"User updated: {user_id}")
        return user
    
    def delete(self, user_id: int, soft: bool = True) -> bool:
        """
        Xóa user
        
        Args:
            user_id: User ID
            soft: True = soft delete (update status), False = hard delete
            
        Returns:
            True nếu xóa thành công
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        if soft:
            user.status = "deleted"
            self.db.commit()
        else:
            self.db.delete(user)
            self.db.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_user_cache(user_id)
        
        logger.info(f"User {'soft ' if soft else ''}deleted: {user_id}")
        return True
    
    # =============== Authentication ===============
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Xác thực user
        
        Args:
            email: Email address
            password: Plain text password
            
        Returns:
            User nếu xác thực thành công, None nếu thất bại
        """
        user = self.get_by_email(email)
        if not user:
            logger.warning(f"Authentication failed: user not found ({email})")
            return None
        
        if not verify_password(password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            self.db.commit()
            logger.warning(f"Authentication failed: wrong password ({email})")
            return None
        
        # Reset failed attempts on success
        user.failed_login_attempts = 0
        from datetime import datetime
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"User authenticated: {user.id} ({email})")
        return user
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        Cập nhật password
        
        Args:
            user_id: User ID
            new_password: Password mới
            
        Returns:
            True nếu thành công
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        user.password_hash = get_password_hash(new_password)
        self.db.commit()
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_user_cache(user_id)
        
        logger.info(f"Password updated for user: {user_id}")
        return True
    
    # =============== Profile ===============
    
    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Lấy user profile
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile hoặc None
        """
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def update_profile(self, user_id: int, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Cập nhật profile
        
        Args:
            user_id: User ID
            data: Dữ liệu profile
            
        Returns:
            Profile đã cập nhật hoặc None
        """
        profile = self.get_profile(user_id)
        if not profile:
            # Create profile if not exists
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
        
        # Update fields
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self.db.commit()
        self.db.refresh(profile)
        
        # Invalidate user cache
        if self.cache:
            self.cache.invalidate_user_cache(user_id)
        
        return profile
    
    # =============== List & Search ===============
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> List[User]:
        """
        Lấy danh sách users
        
        Args:
            skip: Số records bỏ qua
            limit: Số records tối đa
            status: Filter theo status
            role_id: Filter theo role
            
        Returns:
            Danh sách users
        """
        query = self.db.query(User)
        
        if status:
            query = query.filter(User.status == status)
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        return query.offset(skip).limit(limit).all()
    
    def count_users(
        self,
        status: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> int:
        """
        Đếm số users
        
        Args:
            status: Filter theo status
            role_id: Filter theo role
            
        Returns:
            Số users
        """
        query = self.db.query(User)
        
        if status:
            query = query.filter(User.status == status)
        if role_id:
            query = query.filter(User.role_id == role_id)
        
        return query.count()
    
    # =============== Helpers ===============
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User to dict for caching"""
        return {
            "id": user.id,
            "email": user.email,
            "role_id": user.role_id,
            "status": user.status,
            "email_verified": user.email_verified,
            "phone_verified": user.phone_verified,
            "kyc_status": user.kyc_status
        }
    
    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        """Convert dict back to User object"""
        user = User()
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        return user
