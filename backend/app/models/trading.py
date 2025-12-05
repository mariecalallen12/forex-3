"""
Trading Models
Digital Utopia Platform

Models cho Trading Orders, Positions, và Advanced Orders
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, DECIMAL, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from datetime import datetime
import enum

from .base import Base, TimestampMixin


class OrderType(enum.Enum):
    """Loại lệnh giao dịch"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    ICEBERG = "iceberg"
    OCO = "oco"
    TRAILING_STOP = "trailing_stop"


class OrderSide(enum.Enum):
    """Phía giao dịch"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(enum.Enum):
    """Trạng thái lệnh"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(enum.Enum):
    """Thời gian hiệu lực lệnh"""
    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill


class TradingOrder(Base, TimestampMixin):
    """
    Bảng trading_orders - Lệnh giao dịch
    
    Lưu trữ tất cả các lệnh giao dịch của người dùng
    """
    __tablename__ = "trading_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Order details
    order_type = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=True)  # Null for market orders
    stop_price = Column(DECIMAL(20, 8), nullable=True)
    time_in_force = Column(String(10), default="GTC")
    
    # Status
    status = Column(String(50), default="pending", index=True)
    filled_quantity = Column(DECIMAL(20, 8), default=0)
    filled_price = Column(DECIMAL(20, 8), nullable=True)
    remaining_quantity = Column(DECIMAL(20, 8), nullable=True)
    average_price = Column(DECIMAL(20, 8), nullable=True)
    commission = Column(DECIMAL(20, 8), default=0)
    
    # Metadata
    source = Column(String(100), nullable=True)  # web, mobile, api, bot
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="trading_orders")
    
    def __repr__(self):
        return f"<TradingOrder(id={self.id}, symbol={self.symbol}, side={self.side}, status={self.status})>"


class PortfolioPosition(Base, TimestampMixin):
    """
    Bảng portfolio_positions - Vị thế portfolio
    
    Theo dõi vị thế giao dịch hiện tại của người dùng
    """
    __tablename__ = "portfolio_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Position details
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    average_price = Column(DECIMAL(20, 8), nullable=False)
    market_value = Column(DECIMAL(20, 8), nullable=True)
    unrealized_pnl = Column(DECIMAL(20, 8), nullable=True)
    realized_pnl = Column(DECIMAL(20, 8), default=0)
    
    # Position type
    position_type = Column(String(20), default="long")  # long, short
    entry_price = Column(DECIMAL(20, 8), nullable=True)
    entry_time = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Leverage
    leverage = Column(DECIMAL(10, 2), default=1)
    margin_used = Column(DECIMAL(20, 8), default=0)
    
    # Close info
    is_closed = Column(Boolean, default=False, index=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_price = Column(DECIMAL(20, 8), nullable=True)
    closed_reason = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="positions")
    
    def __repr__(self):
        return f"<Position(id={self.id}, symbol={self.symbol}, quantity={self.quantity})>"


class IcebergOrder(Base, TimestampMixin):
    """
    Bảng iceberg_orders - Lệnh Iceberg
    
    Lệnh lớn được chia thành nhiều lệnh nhỏ để tránh tác động thị trường
    """
    __tablename__ = "iceberg_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_order_id = Column(Integer, ForeignKey("trading_orders.id"), nullable=True)
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    total_quantity = Column(DECIMAL(20, 8), nullable=False)
    slice_quantity = Column(DECIMAL(20, 8), nullable=False)
    remaining_quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=True)
    
    # Execution
    status = Column(String(50), default="active", index=True)
    slices_completed = Column(Integer, default=0)
    total_filled = Column(DECIMAL(20, 8), default=0)
    average_fill_price = Column(DECIMAL(20, 8), nullable=True)
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<IcebergOrder(id={self.id}, symbol={self.symbol}, total={self.total_quantity})>"


class OcoOrder(Base, TimestampMixin):
    """
    Bảng oco_orders - Lệnh One-Cancels-Other
    
    Cặp lệnh take-profit và stop-loss, khi một lệnh khớp thì lệnh kia bị hủy
    """
    __tablename__ = "oco_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Linked orders
    primary_order_id = Column(Integer, ForeignKey("trading_orders.id"), nullable=True)
    secondary_order_id = Column(Integer, ForeignKey("trading_orders.id"), nullable=True)
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    primary_side = Column(String(10), nullable=True)
    secondary_side = Column(String(10), nullable=True)
    
    # Status
    status = Column(String(50), default="active", index=True)
    triggered_order_id = Column(Integer, nullable=True)
    
    # Timestamps
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<OcoOrder(id={self.id}, symbol={self.symbol}, status={self.status})>"


class TrailingStopOrder(Base, TimestampMixin):
    """
    Bảng trailing_stop_orders - Lệnh Trailing Stop
    
    Stop-loss tự động điều chỉnh theo giá thị trường
    """
    __tablename__ = "trailing_stop_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_order_id = Column(Integer, ForeignKey("trading_orders.id"), nullable=True)
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    
    # Trailing config
    stop_type = Column(String(20), nullable=True)  # percentage, amount
    stop_value = Column(DECIMAL(20, 8), nullable=True)
    trailing_distance = Column(DECIMAL(20, 8), nullable=True)
    current_stop_price = Column(DECIMAL(20, 8), nullable=True)
    activation_price = Column(DECIMAL(20, 8), nullable=True)
    
    # Price tracking
    highest_price = Column(DECIMAL(20, 8), nullable=True)  # For long positions
    lowest_price = Column(DECIMAL(20, 8), nullable=True)   # For short positions
    
    # Status
    status = Column(String(50), default="active", index=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<TrailingStop(id={self.id}, symbol={self.symbol}, status={self.status})>"
