"""
Referral Models
Digital Utopia Platform

Models cho Referral Codes và Registrations
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from datetime import datetime

from .base import Base, TimestampMixin


class ReferralCode(Base, TimestampMixin):
    """
    Bảng referral_codes - Mã giới thiệu
    
    Mã giới thiệu của staff để mời khách hàng mới
    """
    __tablename__ = "referral_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Code
    code = Column(String(50), unique=True, nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)  # For URL-based referral
    
    # Status
    status = Column(String(50), default="active", index=True)  # active, inactive, expired
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)  # NULL = unlimited
    used_count = Column(Integer, default=0)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Commission
    commission_rate = Column(Integer, default=10)  # Percentage
    commission_type = Column(String(50), default="percentage")  # percentage, fixed
    
    # Creator
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    staff = relationship("User", back_populates="referral_codes", foreign_keys=[staff_id])
    registrations = relationship("ReferralRegistration", back_populates="referral_code")
    
    def __repr__(self):
        return f"<ReferralCode(code={self.code}, staff_id={self.staff_id}, used={self.used_count})>"


class ReferralRegistration(Base, TimestampMixin):
    """
    Bảng referral_registrations - Đăng ký từ referral
    
    Theo dõi người dùng đăng ký qua referral code
    """
    __tablename__ = "referral_registrations"
    
    id = Column(Integer, primary_key=True, index=True)
    referral_code_id = Column(Integer, ForeignKey("referral_codes.id"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Source
    source_type = Column(String(20), nullable=False)  # code, link
    source_url = Column(String(500), nullable=True)
    
    # Metadata
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, verified, rejected, rewarded
    
    # Commission
    commission_paid = Column(Boolean, default=False)
    commission_amount = Column(Integer, default=0)
    commission_paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Verification
    verified_at = Column(DateTime(timezone=True), nullable=True)
    first_deposit_at = Column(DateTime(timezone=True), nullable=True)
    first_trade_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    referral_code = relationship("ReferralCode", back_populates="registrations")
    
    def __repr__(self):
        return f"<ReferralRegistration(user_id={self.referred_user_id}, code_id={self.referral_code_id})>"
