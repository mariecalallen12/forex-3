"""
User Models
Digital Utopia Platform

Models cho User, Profile, Role, Permission
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, Table, Date, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from .base import Base, TimestampMixin


class Role(Base, TimestampMixin):
    """
    Bảng roles - Vai trò người dùng
    
    Các vai trò mặc định:
    - owner: Chủ sở hữu hệ thống
    - admin: Quản trị viên  
    - staff: Nhân viên
    - customer: Khách hàng
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)
    
    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles"
    )


class Permission(Base, TimestampMixin):
    """
    Bảng permissions - Quyền hạn
    
    Định nghĩa các quyền truy cập tài nguyên
    """
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    resource = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions"
    )


class RolePermission(Base):
    """
    Bảng role_permissions - Mapping vai trò và quyền hạn
    """
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    granted_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class User(Base, TimestampMixin):
    """
    Bảng users - Người dùng chính
    
    Lưu trữ thông tin xác thực và trạng thái người dùng
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    
    # Status
    status = Column(String(50), default="pending", index=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    kyc_status = Column(String(50), default="pending", index=True)
    
    # Identifiers
    customer_payment_id = Column(String(50), unique=True, nullable=True)
    referral_code = Column(String(50), nullable=True, index=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Login tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Legal
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    privacy_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    wallet_balances = relationship("WalletBalance", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    trading_orders = relationship("TradingOrder", back_populates="user")
    positions = relationship("PortfolioPosition", back_populates="user")
    kyc_documents = relationship("KYCDocument", back_populates="user")
    referral_codes = relationship("ReferralCode", back_populates="staff", foreign_keys="ReferralCode.staff_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class UserProfile(Base, TimestampMixin):
    """
    Bảng user_profiles - Thông tin chi tiết người dùng
    
    Lưu trữ thông tin cá nhân, ngân hàng, và liên lạc khẩn cấp
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    
    # Personal info
    full_name = Column(String(255))
    display_name = Column(String(100))
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True, index=True)
    
    # Address
    address = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # ID verification
    id_type = Column(String(50), nullable=True)
    id_number = Column(String(100), nullable=True)
    id_verified = Column(Boolean, default=False)
    id_front_url = Column(String(500), nullable=True)
    id_back_url = Column(String(500), nullable=True)
    selfie_url = Column(String(500), nullable=True)
    
    # Bank info
    bank_account_name = Column(String(255), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_branch = Column(String(100), nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Preferences
    preferences = Column(JSONB, default={})
    notification_settings = Column(JSONB, default={
        "email": True,
        "sms": False,
        "push": True
    })
    
    # Avatar
    avatar_url = Column(String(500), nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="profile")
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, name={self.full_name})>"
