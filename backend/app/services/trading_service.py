"""
Trading Service
Digital Utopia Platform

Business logic cho Trading operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from decimal import Decimal
import logging
from datetime import datetime

from ..models.trading import TradingOrder, PortfolioPosition, IcebergOrder, OcoOrder, TrailingStopOrder
from ..models.financial import WalletBalance
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)


class TradingService:
    """
    Service class cho Trading operations
    
    Cung cấp business logic cho:
    - Order management
    - Position management
    - Advanced orders (Iceberg, OCO, Trailing Stop)
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo TradingService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== Orders ===============
    
    def create_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC"
    ) -> TradingOrder:
        """
        Tạo lệnh giao dịch mới
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            side: buy/sell
            order_type: market/limit/stop/etc.
            quantity: Số lượng
            price: Giá (cho limit orders)
            stop_price: Giá stop
            time_in_force: GTC/IOC/FOK
            
        Returns:
            TradingOrder mới
        """
        order = TradingOrder(
            user_id=user_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            remaining_quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            status="pending"
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Order created: {order.id} ({symbol} {side} {quantity})")
        return order
    
    def get_order(self, order_id: int) -> Optional[TradingOrder]:
        """Lấy order theo ID"""
        return self.db.query(TradingOrder).filter(TradingOrder.id == order_id).first()
    
    def get_user_orders(
        self,
        user_id: int,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[TradingOrder]:
        """
        Lấy danh sách orders của user
        
        Args:
            user_id: User ID
            status: Filter theo status
            symbol: Filter theo symbol
            limit: Số orders tối đa
            
        Returns:
            Danh sách orders
        """
        query = self.db.query(TradingOrder).filter(TradingOrder.user_id == user_id)
        
        if status:
            query = query.filter(TradingOrder.status == status)
        if symbol:
            query = query.filter(TradingOrder.symbol == symbol)
        
        return query.order_by(desc(TradingOrder.created_at)).limit(limit).all()
    
    def cancel_order(self, order_id: int, user_id: int) -> Optional[TradingOrder]:
        """
        Hủy order
        
        Args:
            order_id: Order ID
            user_id: User ID (để verify ownership)
            
        Returns:
            Order đã hủy hoặc None
        """
        order = self.db.query(TradingOrder).filter(
            and_(
                TradingOrder.id == order_id,
                TradingOrder.user_id == user_id,
                TradingOrder.status.in_(["pending", "open", "partial"])
            )
        ).first()
        
        if not order:
            return None
        
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Order cancelled: {order_id}")
        return order
    
    def update_order_status(
        self,
        order_id: int,
        status: str,
        filled_quantity: Optional[Decimal] = None,
        filled_price: Optional[Decimal] = None
    ) -> Optional[TradingOrder]:
        """
        Cập nhật trạng thái order
        
        Args:
            order_id: Order ID
            status: Trạng thái mới
            filled_quantity: Số lượng đã khớp
            filled_price: Giá khớp
            
        Returns:
            Order đã cập nhật
        """
        order = self.get_order(order_id)
        if not order:
            return None
        
        order.status = status
        
        if filled_quantity is not None:
            order.filled_quantity = filled_quantity
            order.remaining_quantity = order.quantity - filled_quantity
        
        if filled_price is not None:
            order.filled_price = filled_price
        
        if status == "filled":
            order.filled_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(order)
        
        return order
    
    # =============== Positions ===============
    
    def get_position(self, position_id: int) -> Optional[PortfolioPosition]:
        """Lấy position theo ID"""
        return self.db.query(PortfolioPosition).filter(PortfolioPosition.id == position_id).first()
    
    def get_user_positions(
        self,
        user_id: int,
        is_closed: bool = False,
        symbol: Optional[str] = None
    ) -> List[PortfolioPosition]:
        """
        Lấy danh sách positions của user
        
        Args:
            user_id: User ID
            is_closed: True = lấy positions đã đóng
            symbol: Filter theo symbol
            
        Returns:
            Danh sách positions
        """
        query = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.user_id == user_id,
                PortfolioPosition.is_closed == is_closed
            )
        )
        
        if symbol:
            query = query.filter(PortfolioPosition.symbol == symbol)
        
        return query.all()
    
    def create_or_update_position(
        self,
        user_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        position_type: str = "long",
        leverage: Decimal = Decimal("1")
    ) -> PortfolioPosition:
        """
        Tạo hoặc cập nhật position
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            quantity: Số lượng (positive = add, negative = reduce)
            price: Giá
            position_type: long/short
            leverage: Đòn bẩy
            
        Returns:
            Position
        """
        # Find existing open position
        position = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.user_id == user_id,
                PortfolioPosition.symbol == symbol,
                PortfolioPosition.position_type == position_type,
                PortfolioPosition.is_closed == False
            )
        ).first()
        
        if position:
            # Update existing position
            old_value = position.quantity * position.average_price
            new_value = quantity * price
            total_quantity = position.quantity + quantity
            
            if total_quantity > 0:
                position.average_price = (old_value + new_value) / total_quantity
                position.quantity = total_quantity
            else:
                # Position closed
                position.is_closed = True
                position.closed_at = datetime.utcnow()
                position.closed_price = price
                position.quantity = Decimal("0")
        else:
            # Create new position
            position = PortfolioPosition(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                average_price=price,
                entry_price=price,
                position_type=position_type,
                leverage=leverage,
                margin_used=quantity * price / leverage
            )
            self.db.add(position)
        
        self.db.commit()
        self.db.refresh(position)
        
        # Invalidate portfolio cache
        if self.cache:
            self.cache.delete(f"portfolio:{user_id}")
        
        return position
    
    def close_position(
        self,
        position_id: int,
        user_id: int,
        close_price: Decimal,
        reason: str = "manual"
    ) -> Optional[PortfolioPosition]:
        """
        Đóng position
        
        Args:
            position_id: Position ID
            user_id: User ID
            close_price: Giá đóng
            reason: Lý do đóng
            
        Returns:
            Position đã đóng
        """
        position = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.id == position_id,
                PortfolioPosition.user_id == user_id,
                PortfolioPosition.is_closed == False
            )
        ).first()
        
        if not position:
            return None
        
        # Calculate P&L
        pnl = (close_price - position.average_price) * position.quantity
        if position.position_type == "short":
            pnl = -pnl
        
        position.is_closed = True
        position.closed_at = datetime.utcnow()
        position.closed_price = close_price
        position.closed_reason = reason
        position.realized_pnl = pnl
        
        self.db.commit()
        self.db.refresh(position)
        
        # Invalidate portfolio cache
        if self.cache:
            self.cache.delete(f"portfolio:{user_id}")
        
        logger.info(f"Position closed: {position_id} with P&L: {pnl}")
        return position
    
    # =============== Advanced Orders ===============
    
    def create_iceberg_order(
        self,
        user_id: int,
        symbol: str,
        side: str,
        total_quantity: Decimal,
        slice_quantity: Decimal,
        price: Optional[Decimal] = None
    ) -> IcebergOrder:
        """Tạo Iceberg order"""
        order = IcebergOrder(
            user_id=user_id,
            symbol=symbol,
            side=side,
            total_quantity=total_quantity,
            slice_quantity=slice_quantity,
            remaining_quantity=total_quantity,
            price=price,
            status="active"
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Iceberg order created: {order.id}")
        return order
    
    def create_oco_order(
        self,
        user_id: int,
        symbol: str,
        primary_order_id: int,
        secondary_order_id: int
    ) -> OcoOrder:
        """Tạo OCO order"""
        order = OcoOrder(
            user_id=user_id,
            symbol=symbol,
            primary_order_id=primary_order_id,
            secondary_order_id=secondary_order_id,
            status="active"
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"OCO order created: {order.id}")
        return order
    
    def create_trailing_stop(
        self,
        user_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        stop_type: str,
        stop_value: Decimal,
        trailing_distance: Decimal,
        activation_price: Optional[Decimal] = None
    ) -> TrailingStopOrder:
        """Tạo Trailing Stop order"""
        order = TrailingStopOrder(
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            stop_type=stop_type,
            stop_value=stop_value,
            trailing_distance=trailing_distance,
            activation_price=activation_price,
            status="active"
        )
        
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        
        logger.info(f"Trailing stop created: {order.id}")
        return order
