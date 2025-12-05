"""
Trading module endpoints
Implements complete trading functionality based on Next.js source code
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import random
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError

from app.schemas.trading import (
    PlaceOrderRequest, OrderResponse, OrdersListResponse, CancelOrderRequest, CancelOrderResponse,
    PositionResponse, PositionsListResponse, ClosePositionRequest, ClosePositionResponse,
    MarketPrice, MarketPricesResponse, OrderBookResponse, TradeHistoryResponse
)
from app.middleware.auth import get_current_user

router = APIRouter()
security = HTTPBearer()

# Market data cache for real-time prices
MARKET_DATA_CACHE = {}
CACHE_DURATION = 5  # seconds

class TradingService:
    """Trading service with business logic from Next.js"""

    def __init__(self):
        self.orders = {}  # In-memory storage (replace with database)
        self.positions = {}  # In-memory storage (replace with database)
        self.market_data = {}  # Market data cache

    async def place_order(self, user_data: Dict[str, Any], order_data: PlaceOrderRequest) -> Dict[str, Any]:
        """Place new trading order with validation"""
        
        # Check if user is active and KYC verified
        if not user_data.get('isActive', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tài khoản không hoạt động"
            )

        if user_data.get('kycStatus') != 'verified':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác minh KYC trước khi giao dịch"
            )

        # Check available balance
        symbol = order_data.symbol
        quote_currency = symbol.split('USDT')[0] if 'USDT' in symbol else 'USDT'
        required_balance = order_data.quantity * (order_data.price or 50000)  # Default price

        user_balance = user_data.get('balance', {})
        available_balance = user_balance.get(quote_currency.lower(), 0)

        if available_balance < required_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số dư {quote_currency} không đủ để thực hiện giao dịch"
            )

        # Create order
        order_id = f"order_{int(datetime.now().timestamp())}_{random.randint(100000, 999999)}"
        
        order = {
            'id': order_id,
            'user_id': user_data['id'],
            'symbol': order_data.symbol,
            'side': order_data.side.value,
            'type': order_data.type.value,
            'quantity': order_data.quantity,
            'price': order_data.price,
            'stop_price': order_data.stop_price,
            'leverage': order_data.leverage,
            'status': 'pending',
            'executed_quantity': 0,
            'executed_price': 0,
            'filled_amount': 0,
            'fee': 0,
            'filled_time': None,
            'create_time': datetime.now(),
            'update_time': datetime.now(),
            'is_maker': False,
            'stop_loss': order_data.stop_loss,
            'take_profit': order_data.take_profit,
            'margin': order_data.margin,
        }

        # Store order (replace with database save)
        self.orders[order_id] = order

        # Simulate order execution for demo (in production, this would be async)
        await asyncio.sleep(0.1)
        
        # For market orders, simulate immediate execution
        if order_data.type.value == 'market':
            order['status'] = 'filled'
            order['executed_quantity'] = order_data.quantity
            order['executed_price'] = order_data.price or 50000  # Get from market data
            order['filled_time'] = datetime.now()
            order['fee'] = order_data.quantity * (order_data.price or 50000) * 0.001  # 0.1% fee

            # Create position for filled orders
            position_id = await self._create_position(user_data, order)
            order['position_id'] = position_id

        return order

    async def get_user_orders(self, user_data: Dict[str, Any], 
                             page: int = 1, limit: int = 20, 
                             symbol: Optional[str] = None, 
                             status: Optional[str] = None,
                             side: Optional[str] = None) -> Dict[str, Any]:
        """Get user's orders with pagination and filtering"""
        
        user_id = user_data['id']
        user_orders = [order for order in self.orders.values() if order['user_id'] == user_id]

        # Apply filters
        if symbol:
            user_orders = [order for order in user_orders if order['symbol'] == symbol]
        if status:
            user_orders = [order for order in user_orders if order['status'] == status]
        if side:
            user_orders = [order for order in user_orders if order['side'] == side]

        # Sort by creation time (newest first)
        user_orders.sort(key=lambda x: x['create_time'], reverse=True)

        # Apply pagination
        total_count = len(user_orders)
        offset = (page - 1) * limit
        paginated_orders = user_orders[offset:offset + limit]

        return {
            'orders': paginated_orders,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }

    async def cancel_order(self, user_data: Dict[str, Any], order_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        
        # Get order data
        if order_id not in self.orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy lệnh"
            )

        order = self.orders[order_id]

        # Verify ownership
        if order['user_id'] != user_data['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền hủy lệnh này"
            )

        # Check if order can be cancelled
        if order['status'] not in ['pending', 'partially_filled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể hủy lệnh có trạng thái {order['status']}"
            )

        # Update order status
        order['status'] = 'cancelled'
        order['cancelled_time'] = datetime.now()
        order['update_time'] = datetime.now()

        return order

    async def get_user_positions(self, user_data: Dict[str, Any], symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get user's current positions"""
        
        user_id = user_data['id']
        user_positions = [pos for pos in self.positions.values() 
                         if pos['user_id'] == user_id and pos['status'] == 'open']

        if symbol:
            user_positions = [pos for pos in user_positions if pos['symbol'] == symbol]

        # Calculate P&L for each position using real market data
        positions_with_pnl = []
        for position in user_positions:
            current_price = await self._get_market_price(position['symbol'])
            
            entry_price = position['entry_price']
            quantity = position['quantity']
            side = position['side']
            
            unrealized_pnl = 0
            if side == 'long':
                unrealized_pnl = (current_price - entry_price) * quantity
            else:  # short
                unrealized_pnl = (entry_price - current_price) * quantity

            unrealized_pnl_percent = (unrealized_pnl / (entry_price * quantity)) * 100

            position_with_pnl = position.copy()
            position_with_pnl.update({
                'current_price': current_price,
                'unrealized_pnl': round(unrealized_pnl, 2),
                'unrealized_pnl_percent': round(unrealized_pnl_percent, 2)
            })
            positions_with_pnl.append(position_with_pnl)

        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in positions_with_pnl)

        return {
            'positions': positions_with_pnl,
            'summary': {
                'total_positions': len(positions_with_pnl),
                'total_unrealized_pnl': round(total_unrealized_pnl, 2)
            }
        }

    async def close_position(self, user_data: Dict[str, Any], position_id: str) -> Dict[str, Any]:
        """Close a position"""
        
        if position_id not in self.positions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy vị thế"
            )

        position = self.positions[position_id]

        # Verify ownership
        if position['user_id'] != user_data['id']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền đóng vị thế này"
            )

        # Check if position is already closed
        if position['status'] == 'closed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vị thế đã được đóng"
            )

        # Get current market price
        current_price = await self._get_market_price(position['symbol'])
        
        # Calculate realized P&L
        entry_price = position['entry_price']
        quantity = position['quantity']
        side = position['side']
        
        if side == 'long':
            realized_pnl = (current_price - entry_price) * quantity
        else:  # short
            realized_pnl = (entry_price - current_price) * quantity

        realized_pnl_percent = (realized_pnl / (entry_price * quantity)) * 100

        # Update position status
        close_time = datetime.now()
        position.update({
            'status': 'closed',
            'exit_price': current_price,
            'realized_pnl': round(realized_pnl, 2),
            'realized_pnl_percent': round(realized_pnl_percent, 4),
            'close_time': close_time,
            'update_time': close_time
        })

        # Update user's trading statistics
        await self._update_user_trading_stats(user_data['id'], realized_pnl)

        return position

    async def _create_position(self, user_data: Dict[str, Any], order: Dict[str, Any]) -> str:
        """Create a new position from a filled order"""
        
        position_id = f"pos_{int(datetime.now().timestamp())}_{random.randint(100000, 999999)}"
        
        # Determine position side
        position_side = 'long' if order['side'] == 'buy' else 'short'
        
        position = {
            'id': position_id,
            'user_id': user_data['id'],
            'order_id': order['id'],
            'symbol': order['symbol'],
            'side': position_side,
            'quantity': order['executed_quantity'],
            'entry_price': order['executed_price'],
            'leverage': order['leverage'],
            'margin': order['margin'] or (order['executed_quantity'] * order['executed_price'] / order['leverage']),
            'status': 'open',
            'create_time': datetime.now(),
            'update_time': datetime.now()
        }

        # Store position
        self.positions[position_id] = position
        
        return position_id

    async def _get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        
        # Check cache first
        cache_key = f"price_{symbol}"
        cached_data = MARKET_DATA_CACHE.get(cache_key)
        
        if cached_data and (datetime.now() - cached_data['timestamp']).seconds < CACHE_DURATION:
            return cached_data['price']

        # Generate realistic price (in production, fetch from real API)
        base_prices = {
            'BTCUSDT': 50000,
            'ETHUSDT': 3000,
            'BNBUSDT': 300,
            'ADAUSDT': 0.5,
            'DOTUSDT': 6.0,
            'LINKUSDT': 15.0,
            'LTCUSDT': 80.0,
            'XRPUSDT': 0.6,
            'BCHUSDT': 150.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add some realistic volatility
        volatility = 0.02  # 2% volatility
        price_change = (random.random() - 0.5) * base_price * volatility
        current_price = base_price + price_change
        
        # Cache the result
        MARKET_DATA_CACHE[cache_key] = {
            'price': current_price,
            'timestamp': datetime.now()
        }
        
        return round(current_price, 2)

    async def _update_user_trading_stats(self, user_id: str, realized_pnl: float):
        """Update user's trading statistics"""
        # In production, update database
        # For demo, just log the update
        print(f"Updated trading stats for user {user_id}: P&L = {realized_pnl}")

# Initialize trading service
trading_service = TradingService()

@router.post("/orders", response_model=OrderResponse)
async def place_order(
    order_data: PlaceOrderRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Place new trading order"""
    try:
        # Get current user data
        user_data = await get_current_user(credentials.credentials)
        
        # Place the order
        order = await trading_service.place_order(user_data, order_data)
        
        return OrderResponse(**order)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dữ liệu đầu vào không hợp lệ",
            headers={"X-Error-Details": str(e)}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Place order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể đặt lệnh"
        )

@router.get("/orders", response_model=OrdersListResponse)
async def get_orders(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status"),
    side: Optional[str] = Query(None, description="Filter by side"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's orders with pagination and filters"""
    try:
        user_data = await get_current_user(credentials.credentials)
        result = await trading_service.get_user_orders(
            user_data, page, limit, symbol, status, side
        )
        
        # Convert to response format
        orders_response = [OrderResponse(**order) for order in result['orders']]
        
        return OrdersListResponse(
            orders=orders_response,
            pagination=result['pagination'],
            total_count=result['pagination']['total']
        )
        
    except Exception as e:
        print(f"Get orders error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách lệnh"
        )

@router.put("/orders/{order_id}/cancel", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Cancel a pending order"""
    try:
        user_data = await get_current_user(credentials.credentials)
        order = await trading_service.cancel_order(user_data, order_id)
        
        return CancelOrderResponse(
            order_id=order['id'],
            status=order['status'],
            cancelled_time=order['cancelled_time'],
            message="Hủy lệnh thành công"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Cancel order error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể hủy lệnh"
        )

@router.get("/positions", response_model=PositionsListResponse)
async def get_positions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get user's current positions"""
    try:
        user_data = await get_current_user(credentials.credentials)
        result = await trading_service.get_user_positions(user_data, symbol)
        
        # Convert to response format
        positions_response = [PositionResponse(**pos) for pos in result['positions']]
        
        return PositionsListResponse(
            positions=positions_response,
            summary=result['summary']
        )
        
    except Exception as e:
        print(f"Get positions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể lấy danh sách vị thế"
        )

@router.post("/positions/{position_id}/close", response_model=ClosePositionResponse)
async def close_position(
    position_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Close a position"""
    try:
        user_data = await get_current_user(credentials.credentials)
        position = await trading_service.close_position(user_data, position_id)
        
        return ClosePositionResponse(
            position_id=position['id'],
            exit_price=position['exit_price'],
            realized_pnl=position['realized_pnl'],
            realized_pnl_percent=position['realized_pnl_percent'],
            close_time=position['close_time'],
            message="Đóng vị thế thành công"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Close position error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể đóng vị thế"
        )