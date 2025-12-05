"""
Trading module schemas for FastAPI endpoints
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit" 
    STOP_LOSS = "stop-loss"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"

class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"

class PlaceOrderRequest(BaseModel):
    """Request model for placing trading orders"""
    symbol: str = Field(..., min_length=3, description="Trading pair symbol")
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    type: OrderType = Field(..., description="Order type")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Order price for limit orders")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price for stop-loss orders")
    leverage: int = Field(default=1, ge=1, le=100, description="Leverage factor")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    margin: Optional[float] = Field(None, gt=0, description="Margin amount")

    @validator('price')
    def validate_price(cls, v, values):
        if values.get('type') == OrderType.LIMIT and not v:
            raise ValueError('Giá khớp lệnh là bắt buộc cho lệnh giới hạn')
        return v

    @validator('stop_price') 
    def validate_stop_price(cls, v, values):
        if values.get('type') == OrderType.STOP_LOSS and not v:
            raise ValueError('Giá kích hoạt là bắt buộc cho lệnh stop-loss')
        return v

class OrderResponse(BaseModel):
    """Response model for order data"""
    id: str
    user_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]
    stop_price: Optional[float]
    leverage: int
    status: OrderStatus
    executed_quantity: float = 0
    executed_price: float = 0
    filled_amount: float = 0
    fee: float = 0
    filled_time: Optional[datetime]
    create_time: datetime
    update_time: datetime
    is_maker: bool = False

class OrdersListResponse(BaseModel):
    """Response model for orders list"""
    orders: List[OrderResponse]
    pagination: Dict[str, int]
    total_count: int

class CancelOrderRequest(BaseModel):
    """Request model for cancelling orders"""
    order_id: str

class CancelOrderResponse(BaseModel):
    """Response model for order cancellation"""
    order_id: str
    status: OrderStatus = OrderStatus.CANCELLED
    cancelled_time: datetime
    message: str

class PositionResponse(BaseModel):
    """Response model for position data"""
    id: str
    user_id: str
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    leverage: int
    margin: float
    status: PositionStatus
    current_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None
    create_time: datetime
    update_time: Optional[datetime] = None
    close_time: Optional[datetime] = None

class PositionsListResponse(BaseModel):
    """Response model for positions list"""
    positions: List[PositionResponse]
    summary: Dict[str, Any]

class ClosePositionRequest(BaseModel):
    """Request model for closing positions"""
    position_id: str

class ClosePositionResponse(BaseModel):
    """Response model for position closure"""
    position_id: str
    exit_price: float
    realized_pnl: float
    realized_pnl_percent: float
    close_time: datetime
    message: str

class MarketPrice(BaseModel):
    """Market price data model"""
    symbol: str
    price: float
    change_24h: float
    change_percent: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: int

class MarketPricesResponse(BaseModel):
    """Response model for market prices"""
    prices: Dict[str, MarketPrice]
    timestamp: datetime
    symbols: List[str]
    data_source: str = "real-time"

class OrderBookEntry(BaseModel):
    """Order book entry model"""
    price: float
    quantity: float
    total: float

class OrderBookResponse(BaseModel):
    """Response model for order book data"""
    symbol: str
    bids: List[OrderBookEntry]
    asks: List[OrderBookEntry]
    last_update_id: int

class TradeEntry(BaseModel):
    """Trade entry model"""
    id: str
    price: float
    quantity: float
    time: int
    timestamp: str
    is_buyer_maker: bool
    is_best_match: bool

class TradeHistoryResponse(BaseModel):
    """Response model for trade history"""
    symbol: str
    trades: List[TradeEntry]
    timestamp: datetime

class TradingStats(BaseModel):
    """Trading statistics model"""
    total_trades: int
    total_trading_volume: float
    profit_loss: float = 0.0
    total_pnl: float = 0.0
    closed_positions: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0