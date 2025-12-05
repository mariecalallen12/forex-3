"""
User Management Schemas
User profile management và account operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"
    SUSPENDED = "suspended"


class UserRole(str, Enum):
    """User roles"""
    USER = "user"
    ADMIN = "admin"
    STAFF = "staff"


class UserInfo(BaseModel):
    """Basic user information"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    displayName: str = Field(..., description="Display name")
    phoneNumber: Optional[str] = Field(None, description="Phone number")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    role: UserRole = Field(default=UserRole.USER)
    isActive: bool = Field(default=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")
    deletedAt: Optional[datetime] = Field(None, description="Deletion timestamp")


class UserProfile(BaseModel):
    """Complete user profile"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str = Field(..., description="User email")
    displayName: str = Field(..., description="Display name")
    phoneNumber: Optional[str] = Field(None, description="Phone number")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    role: UserRole = Field(default=UserRole.USER)
    isActive: bool = Field(default=True)
    
    # Profile fields
    firstName: Optional[str] = Field(None, description="First name")
    lastName: Optional[str] = Field(None, description="Last name")
    dateOfBirth: Optional[datetime] = Field(None, description="Date of birth")
    address: Optional[str] = Field(None, description="Address")
    city: Optional[str] = Field(None, description="City")
    country: Optional[str] = Field(None, description="Country")
    
    # Account fields
    emailVerified: bool = Field(default=False, description="Email verification status")
    phoneVerified: bool = Field(default=False, description="Phone verification status")
    twoFactorEnabled: bool = Field(default=False, description="2FA status")
    
    # Timestamps
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")
    lastLoginAt: Optional[datetime] = Field(None, description="Last login timestamp")
    deletedAt: Optional[datetime] = Field(None, description="Deletion timestamp")


class UpdateProfileRequest(BaseModel):
    """Request để cập nhật user profile"""
    displayName: Optional[str] = Field(None, min_length=2, max_length=50, description="Display name")
    phoneNumber: Optional[str] = Field(None, description="Phone number")
    avatar: Optional[str] = Field(None, description="Avatar URL")
    firstName: Optional[str] = Field(None, max_length=50, description="First name")
    lastName: Optional[str] = Field(None, max_length=50, description="Last name")
    address: Optional[str] = Field(None, max_length=200, description="Address")
    city: Optional[str] = Field(None, max_length=50, description="City")
    country: Optional[str] = Field(None, max_length=50, description="Country")
    
    @validator('displayName')
    def validate_display_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Tên hiển thị phải có ít nhất 2 ký tự')
        return v.strip() if v else v
    
    @validator('phoneNumber')
    def validate_phone_number(cls, v):
        if v is not None:
            # Simple phone validation
            v = v.strip()
            if len(v) < 10 or len(v) > 15:
                raise ValueError('Số điện thoại phải có 10-15 ký tự')
        return v
    
    @validator('avatar')
    def validate_avatar_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('Avatar phải là URL hợp lệ')
        return v


class UserProfileResponse(BaseModel):
    """Response cho user profile"""
    success: bool = Field(..., description="Operation success status")
    data: UserProfile


class UpdateProfileResponse(BaseModel):
    """Response cho cập nhật profile"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Dict[str, Any] = Field(..., description="Updated fields")


class DeleteAccountResponse(BaseModel):
    """Response cho xóa tài khoản"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")


class UserActivity(BaseModel):
    """User activity tracking"""
    action: str = Field(..., description="Action performed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = Field(None, description="Action details")
    ipAddress: Optional[str] = Field(None, description="IP address")
    userAgent: Optional[str] = Field(None, description="User agent")


class UserPreferences(BaseModel):
    """User preferences and settings"""
    language: str = Field(default="vi", description="Preferred language")
    timezone: str = Field(default="Asia/Ho_Chi_Minh", description="Timezone")
    currency: str = Field(default="VND", description="Preferred currency")
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "sms": False,
            "push": True,
            "marketing": False
        },
        description="Notification preferences"
    )
    privacy: Dict[str, bool] = Field(
        default_factory=lambda: {
            "profileVisible": True,
            "activityVisible": False,
            "shareData": False
        },
        description="Privacy settings"
    )


# Mock data functions for development
def get_mock_user_profile() -> UserProfile:
    """Tạo mock user profile"""
    return UserProfile(
        id="user_001",
        email="user@example.com",
        displayName="Nguyễn Văn A",
        phoneNumber="+84901234567",
        avatar="https://example.com/avatar.jpg",
        firstName="Nguyễn Văn",
        lastName="A",
        address="123 Đường ABC",
        city="Hồ Chí Minh",
        country="Việt Nam",
        emailVerified=True,
        phoneVerified=False,
        twoFactorEnabled=False,
        createdAt=datetime.utcnow(),
        lastLoginAt=datetime.utcnow()
    )


def get_mock_user_preferences() -> UserPreferences:
    """Tạo mock user preferences"""
    return UserPreferences()


def get_mock_user_activity() -> List[UserActivity]:
    """Tạo mock user activity"""
    return [
        UserActivity(
            action="login",
            timestamp=datetime.utcnow(),
            details={"method": "email"},
            ipAddress="192.168.1.1"
        ),
        UserActivity(
            action="profile_updated",
            timestamp=datetime.utcnow(),
            details={"fields": ["displayName", "phoneNumber"]},
            ipAddress="192.168.1.1"
        )
    ]