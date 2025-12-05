"""
SQLAlchemy Models Module
Digital Utopia Platform

Tất cả các model database theo schema thiết kế
"""

from .base import Base, TimestampMixin
from .user import User, UserProfile, Role, Permission, RolePermission
from .trading import TradingOrder, PortfolioPosition, IcebergOrder, OcoOrder, TrailingStopOrder
from .financial import Transaction, WalletBalance, ExchangeRate
from .compliance import KYCDocument, ComplianceEvent, RiskAssessment, AMLScreening
from .portfolio import TradingBot, Watchlist
from .referral import ReferralCode, ReferralRegistration
from .audit import AuditLog, AnalyticsEvent

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    
    # User
    "User",
    "UserProfile", 
    "Role",
    "Permission",
    "RolePermission",
    
    # Trading
    "TradingOrder",
    "PortfolioPosition",
    "IcebergOrder",
    "OcoOrder",
    "TrailingStopOrder",
    
    # Financial
    "Transaction",
    "WalletBalance",
    "ExchangeRate",
    
    # Compliance
    "KYCDocument",
    "ComplianceEvent",
    "RiskAssessment",
    "AMLScreening",
    
    # Portfolio
    "TradingBot",
    "Watchlist",
    
    # Referral
    "ReferralCode",
    "ReferralRegistration",
    
    # Audit
    "AuditLog",
    "AnalyticsEvent"
]
