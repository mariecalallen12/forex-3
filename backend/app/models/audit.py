"""
Audit Models
Digital Utopia Platform

Models cho Audit Logs và Analytics Events
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB, INET

from .base import Base, TimestampMixin


class AuditLog(Base):
    """
    Bảng audit_logs - Nhật ký kiểm toán
    
    Ghi lại tất cả các hành động quan trọng trong hệ thống
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user_role = Column(String(50), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    
    # Changes
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    
    # Request info
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Result
    result = Column(String(50), default="success")  # success, failure, error
    error_message = Column(Text, nullable=True)
    
    # Classification
    category = Column(String(50), nullable=True)  # authentication, financial, trading, admin, etc.
    severity = Column(String(20), default="info")  # info, warning, critical
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default='now()', index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


class AnalyticsEvent(Base):
    """
    Bảng analytics_events - Sự kiện phân tích
    
    Thu thập dữ liệu sử dụng để phân tích và tối ưu
    """
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event details
    event_name = Column(String(100), nullable=False, index=True)
    event_category = Column(String(50), nullable=True, index=True)
    event_label = Column(String(255), nullable=True)
    event_value = Column(Integer, nullable=True)
    
    # Properties
    event_properties = Column(JSONB, default={})
    
    # Session info
    session_id = Column(String(255), nullable=True, index=True)
    page_url = Column(String(500), nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Device info
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    
    # Geo info
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default='now()', index=True)
    
    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, name={self.event_name}, user_id={self.user_id})>"
