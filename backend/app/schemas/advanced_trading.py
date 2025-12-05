"""
Advanced Trading Orders Schemas
Iceberg Orders, OCO Orders, và Trailing Stop Orders
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class OrderSide(str, Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    TRAILING_STOP = "TRAILING_STOP"
    ICEBERG = "ICEBERG"
    OCO = "OCO"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    TRIGGERED = "TRIGGERED"
    EXPIRED = "EXPIRED"


class TimeInForce(str, Enum):
    """Time in force"""
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill


class TrailingType(str, Enum):
    """Trailing stop types"""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


# ========== ICEBERG ORDERS ==========

class IcebergOrder(BaseModel):
    """Iceberg Order Model"""
    orderId: str = Field(..., description="Unique order ID")
    userId: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    totalQuantity: float = Field(..., description="Total order quantity")
    visibleQuantity: float = Field(..., description="Visible quantity per slice")
    remainingQuantity: float = Field(..., description="Remaining quantity")
    filledQuantity: float = Field(default=0.0, description="Filled quantity")
    executedSlices: int = Field(default=0, description="Number of slices executed")
    maxSlices: Optional[int] = Field(None, description="Maximum number of slices")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    timeInForce: TimeInForce = Field(default=TimeInForce.GTC)
    price: Optional[float] = Field(None, description="Limit price")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CreateIcebergOrderRequest(BaseModel):
    """Request to create iceberg order"""
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    totalQuantity: float = Field(..., gt=0, description="Total quantity")
    visibleQuantity: float = Field(..., gt=0, description="Visible quantity per slice")
    price: Optional[float] = Field(None, gt=0, description="Limit price")
    timeInForce: TimeInForce = Field(default=TimeInForce.GTC)
    maxSlices: Optional[int] = Field(None, gt=0, description="Maximum slices")
    
    @validator('visibleQuantity')
    def validate_visible_quantity(cls, v, values):
        if 'totalQuantity' in values and v > values['totalQuantity']:
            raise ValueError('Visible quantity cannot exceed total quantity')
        if 'totalQuantity' in values and v < (values['totalQuantity'] * 0.01):
            raise ValueError('Visible quantity too small (minimum 1% of total)')
        if 'totalQuantity' in values and v > (values['totalQuantity'] * 0.5):
            raise ValueError('Visible quantity too large (maximum 50% of total)')
        return v


class IcebergOrderResponse(BaseModel):
    """Response for iceberg order"""
    success: bool = Field(..., description="Operation success")
    data: IcebergOrder
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


class UpdateIcebergOrderRequest(BaseModel):
    """Request to update iceberg order"""
    orderId: str = Field(..., description="Order ID")
    visibleQuantity: Optional[float] = Field(None, gt=0, description="New visible quantity")
    maxSlices: Optional[int] = Field(None, gt=0, description="New max slices")


# ========== OCO ORDERS ==========

class OcoOrder(BaseModel):
    """OCO (One-Cancels-Other) Order Model"""
    orderId: str = Field(..., description="Unique order ID")
    userId: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    orders: Dict[str, Dict[str, Any]] = Field(..., description="Take profit và stop loss orders")
    status: OrderStatus = Field(default=OrderStatus.ACTIVE)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CreateOcoOrderRequest(BaseModel):
    """Request to create OCO order"""
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Order quantity")
    takeProfitPrice: float = Field(..., gt=0, description="Take profit price")
    stopLossPrice: float = Field(..., gt=0, description="Stop loss price")
    timeInForce: TimeInForce = Field(default=TimeInForce.GTC)
    
    @validator('takeProfitPrice', 'stopLossPrice')
    def validate_prices(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('takeProfitPrice', 'stopLossPrice', pre=True)
    def validate_price_logic(cls, v, values, **kwargs):
        if 'takeProfitPrice' in values and 'stopLossPrice' in values and 'side' in values:
            tp = values['takeProfitPrice']
            sl = values['stopLossPrice']
            side = values['side']
            
            if side == OrderSide.BUY and tp <= sl:
                raise ValueError('For BUY orders: take profit must be above stop loss')
            elif side == OrderSide.SELL and tp >= sl:
                raise ValueError('For SELL orders: take profit must be below stop loss')
        return v


class OcoOrderResponse(BaseModel):
    """Response for OCO order"""
    success: bool = Field(..., description="Operation success")
    data: OcoOrder
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


# ========== TRAILING STOP ORDERS ==========

class TrailingStopOrder(BaseModel):
    """Trailing Stop Order Model"""
    orderId: str = Field(..., description="Unique order ID")
    userId: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., description="Order quantity")
    trailingType: TrailingType = Field(..., description="Trailing type")
    trailValue: float = Field(..., description="Trailing value")
    currentTrailValue: float = Field(..., description="Current trailing value")
    stopPrice: float = Field(..., description="Current stop price")
    activationPrice: Optional[float] = Field(None, description="Activation price")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    timeInForce: TimeInForce = Field(default=TimeInForce.GTC)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


class CreateTrailingStopOrderRequest(BaseModel):
    """Request to create trailing stop order"""
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Order quantity")
    trailingType: TrailingType = Field(..., description="PERCENTAGE or FIXED_AMOUNT")
    trailValue: float = Field(..., gt=0, description="Trailing value")
    activationPrice: Optional[float] = Field(None, description="Activation price")
    timeInForce: TimeInForce = Field(default=TimeInForce.GTC)
    
    @validator('activationPrice')
    def validate_activation_price(cls, v, values):
        if v is not None and v <= 0:
            raise ValueError('Activation price must be positive')
        return v


class UpdateTrailingStopOrderRequest(BaseModel):
    """Request to update trailing stop order"""
    orderId: str = Field(..., description="Order ID")
    trailValue: Optional[float] = Field(None, gt=0, description="New trailing value")
    activationPrice: Optional[float] = Field(None, description="New activation price")
    stopPrice: Optional[float] = Field(None, gt=0, description="Manual stop price")


class CancelTrailingStopOrderRequest(BaseModel):
    """Request to cancel trailing stop order"""
    orderId: str = Field(..., description="Order ID to cancel")


class TrailingStopOrderResponse(BaseModel):
    """Response for trailing stop order"""
    success: bool = Field(..., description="Operation success")
    data: Union[TrailingStopOrder, Dict[str, Any]]
    metadata: Dict[str, Any] = Field(..., description="Response metadata")


# ========== PAGINATION AND FILTERS ==========

class OrderListRequest(BaseModel):
    """Request for listing orders with pagination"""
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    status: Optional[OrderStatus] = Field(None, description="Filter by status")
    limit: int = Field(default=50, ge=1, le=100, description="Page size")
    page: int = Field(default=1, ge=1, description="Page number")


class OrderListResponse(BaseModel):
    """Response for order list"""
    success: bool = Field(..., description="Operation success")
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(..., description="Response metadata with pagination")


# ========== MOCK DATA FOR DEVELOPMENT ==========

def get_mock_iceberg_orders() -> List[IcebergOrder]:
    """Generate mock iceberg orders"""
    return [
        IcebergOrder(
            orderId="ICEBERG_001",
            userId="user_001",
            symbol="BTCUSDT",
            side=OrderSide.BUY,
            totalQuantity=10.0,
            visibleQuantity=2.0,
            remainingQuantity=8.0,
            filledQuantity=2.0,
            executedSlices=1,
            maxSlices=5,
            status=OrderStatus.ACTIVE,
            price=45000.0
        )
    ]


def get_mock_oco_orders() -> List[OcoOrder]:
    """Generate mock OCO orders"""
    return [
        OcoOrder(
            orderId="OCO_001",
            userId="user_001",
            symbol="ETHUSDT",
            orders={
                "takeProfit": {
                    "orderId": "TP_001",
                    "side": OrderSide.BUY,
                    "price": 3200.0,
                    "status": OrderStatus.PENDING
                },
                "stopLoss": {
                    "orderId": "SL_001",
                    "side": OrderSide.BUY,
                    "price": 2900.0,
                    "status": OrderStatus.PENDING
                }
            },
            status=OrderStatus.ACTIVE
        )
    ]


def get_mock_trailing_stop_orders() -> List[TrailingStopOrder]:
    """Generate mock trailing stop orders"""
    return [
        TrailingStopOrder(
            orderId="TRAILING_001",
            userId="user_001",
            symbol="ADAUSDT",
            side=OrderSide.SELL,
            quantity=1000.0,
            trailingType=TrailingType.PERCENTAGE,
            trailValue=5.0,
            currentTrailValue=5.0,
            stopPrice=1.43,
            activationPrice=1.55,
            status=OrderStatus.PENDING
        )
    ]


def get_mock_current_price(symbol: str) -> float:
    """Get mock current price for symbol"""
    mock_prices = {
        "BTCUSDT": 45000.0,
        "ETHUSDT": 3000.0,
        "ADAUSDT": 1.5,
        "DOTUSDT": 25.0,
        "LINKUSDT": 15.0
    }
    return mock_prices.get(symbol, 100.0)