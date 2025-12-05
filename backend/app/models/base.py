"""
Base Model
Digital Utopia Platform

Định nghĩa Base class và Mixins cho tất cả models
"""

from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr

# Base class cho tất cả models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin thêm timestamp columns cho models
    
    Columns:
        created_at: Thời gian tạo record
        updated_at: Thời gian cập nhật cuối cùng
    """
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False
        )
