"""
Portfolio Models
Digital Utopia Platform

Models cho Trading Bots và Watchlists
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, DECIMAL
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime

from .base import Base, TimestampMixin


class TradingBot(Base, TimestampMixin):
    """
    Bảng trading_bots - Bot giao dịch tự động
    
    Quản lý các bot giao dịch của người dùng
    """
    __tablename__ = "trading_bots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Bot info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Strategy
    strategy_id = Column(String(100), nullable=True)
    strategy_name = Column(String(255), nullable=True)
    strategy_parameters = Column(JSONB, default={})
    
    # Config
    symbols = Column(ARRAY(String), default=[])
    base_amount = Column(DECIMAL(20, 8), default=0)
    leverage = Column(DECIMAL(10, 2), default=1)
    max_positions = Column(Integer, default=5)
    risk_per_trade = Column(DECIMAL(5, 2), default=1)  # Percentage
    
    # Status
    status = Column(String(50), default="PAUSED", index=True)  # STARTED, PAUSED, STOPPED
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(DECIMAL(20, 8), default=0)
    max_drawdown = Column(DECIMAL(20, 8), default=0)
    
    # Logs
    logs = Column(JSONB, default=[])
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<TradingBot(id={self.id}, name={self.name}, status={self.status})>"


class Watchlist(Base, TimestampMixin):
    """
    Bảng watchlists - Danh sách theo dõi
    
    Quản lý danh sách symbols người dùng theo dõi
    """
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Watchlist info
    name = Column(String(255), default="Default")
    description = Column(Text, nullable=True)
    
    # Symbols
    symbols = Column(ARRAY(String), default=[])
    
    # Settings
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Sorting
    sort_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Watchlist(id={self.id}, user_id={self.user_id}, symbols_count={len(self.symbols or [])})>"
