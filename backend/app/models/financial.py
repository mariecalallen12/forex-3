"""
Financial Models
Digital Utopia Platform

Models cho Transactions, Wallet Balances, và Exchange Rates
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, DECIMAL, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from datetime import datetime

from .base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    """
    Bảng transactions - Giao dịch tài chính
    
    Lưu trữ tất cả giao dịch: nạp tiền, rút tiền, chuyển khoản, phí, trading
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction type
    transaction_type = Column(String(50), nullable=False, index=True)  # deposit, withdrawal, transfer, fee, trading
    category = Column(String(50), nullable=True)  # crypto_deposit, bank_transfer, vietqr, etc.
    
    # Amount
    asset = Column(String(20), nullable=False, index=True)
    amount = Column(DECIMAL(20, 8), nullable=False)
    fee = Column(DECIMAL(20, 8), default=0)
    net_amount = Column(DECIMAL(20, 8), nullable=False)
    
    # Balance tracking
    balance_before = Column(DECIMAL(20, 8), nullable=True)
    balance_after = Column(DECIMAL(20, 8), nullable=True)
    
    # Status
    status = Column(String(50), default="pending", index=True)  # pending, completed, failed, cancelled
    
    # Reference
    reference_id = Column(String(100), nullable=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    # Bank transfer details
    bank_account = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    
    # Crypto details
    transaction_hash = Column(String(255), nullable=True, index=True)
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    network = Column(String(50), nullable=True)
    confirmations = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSONB, default={})
    ip_address = Column(INET, nullable=True)
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    failed_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class WalletBalance(Base, TimestampMixin):
    """
    Bảng wallet_balances - Số dư ví
    
    Theo dõi số dư của mỗi loại tiền tệ cho mỗi người dùng
    """
    __tablename__ = "wallet_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Balance
    asset = Column(String(20), nullable=False, index=True)
    available_balance = Column(DECIMAL(20, 8), nullable=False, default=0)
    locked_balance = Column(DECIMAL(20, 8), nullable=False, default=0)
    pending_balance = Column(DECIMAL(20, 8), nullable=False, default=0)
    reserved_balance = Column(DECIMAL(20, 8), nullable=False, default=0)
    
    # Constraint to ensure unique user-asset pair
    __table_args__ = (
        UniqueConstraint('user_id', 'asset', name='uq_wallet_user_asset'),
    )
    
    # Relationships
    user = relationship("User", back_populates="wallet_balances")
    
    @property
    def total_balance(self) -> float:
        """Tổng số dư = available + locked"""
        return float(self.available_balance or 0) + float(self.locked_balance or 0)
    
    def __repr__(self):
        return f"<WalletBalance(user_id={self.user_id}, asset={self.asset}, balance={self.total_balance})>"


class ExchangeRate(Base, TimestampMixin):
    """
    Bảng exchange_rates - Tỷ giá hối đoái
    
    Lưu trữ tỷ giá giữa các cặp tiền tệ
    """
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Currency pair
    base_asset = Column(String(20), nullable=False, index=True)
    target_asset = Column(String(20), nullable=False, index=True)
    
    # Rate
    rate = Column(DECIMAL(20, 8), nullable=False)
    inverse_rate = Column(DECIMAL(20, 8), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    
    # Source
    source = Column(String(50), nullable=True)  # internal, binance, exchangerate-api
    
    # Constraint
    __table_args__ = (
        UniqueConstraint('base_asset', 'target_asset', name='uq_exchange_rate_pair'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.base_asset}/{self.target_asset}={self.rate})>"
