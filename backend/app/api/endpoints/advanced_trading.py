"""
Advanced Trading Orders API Endpoints
Iceberg Orders, OCO Orders, và Trailing Stop Orders
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime

from app.schemas.advanced_trading import (
    # Iceberg Orders
    IcebergOrder,
    IcebergOrderResponse,
    CreateIcebergOrderRequest,
    UpdateIcebergOrderRequest,
    OrderListRequest,
    OrderListResponse,
    # OCO Orders
    OcoOrder,
    OcoOrderResponse,
    CreateOcoOrderRequest,
    # Trailing Stop Orders
    TrailingStopOrder,
    TrailingStopOrderResponse,
    CreateTrailingStopOrderRequest,
    UpdateTrailingStopOrderRequest,
    CancelTrailingStopOrderRequest,
    OrderStatus,
    OrderSide,
    get_mock_iceberg_orders,
    get_mock_oco_orders,
    get_mock_trailing_stop_orders,
    get_mock_current_price
)

router = APIRouter()
security = HTTPBearer()

# In-memory storage cho development
iceberg_orders_storage = {}
oco_orders_storage = {}
trailing_stop_orders_storage = {}


async def verify_user_session(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Verify user session từ token
    Trong production sẽ verify JWT/Firebase token
    """
    token = credentials.credentials
    
    # Mock verification - trong production sẽ verify JWT/Firebase token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy token xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mock user session
    return {
        "uid": "user_001",
        "email": "user@example.com",
        "displayName": "Trading User",
        "role": "user"
    }


# ========== ICEBERG ORDERS ==========

@router.post(
    "/api/trading/orders/iceberg",
    response_model=IcebergOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo Iceberg Order",
    tags=["advanced-trading", "iceberg"]
)
async def create_iceberg_order(
    request: Request,
    create_request: CreateIcebergOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Tạo Iceberg Order với slicing logic
    
    Iceberg Order chia tổng số lượng thành nhiều slice nhỏ để tránh tác động lớn lên thị trường
    """
    try:
        user_id = user_session["uid"]
        
        # Check user balance (simplified)
        user_balance = 10000.0  # Mock balance
        required_margin = create_request.totalQuantity * (create_request.price or 1000) * 0.1
        
        if user_balance < required_margin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số dư không đủ để tạo Iceberg Order"
            )
        
        # Create iceberg order
        iceberg_order_id = f"ICEBERG_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        iceberg_order = IcebergOrder(
            orderId=iceberg_order_id,
            userId=user_id,
            symbol=create_request.symbol,
            side=create_request.side,
            totalQuantity=create_request.totalQuantity,
            visibleQuantity=create_request.visibleQuantity,
            remainingQuantity=create_request.totalQuantity,
            price=create_request.price,
            timeInForce=create_request.timeInForce,
            maxSlices=create_request.maxSlices
        )
        
        # Store in memory
        iceberg_orders_storage[iceberg_order_id] = iceberg_order
        
        # Log activity
        print(f"Iceberg order created: {iceberg_order_id} for user {user_id}")
        
        return IcebergOrderResponse(
            success=True,
            data=iceberg_order,
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "Iceberg Order được tạo thành công"
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Create Iceberg Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo Iceberg Order: {str(error)}"
        )


@router.get(
    "/api/trading/orders/iceberg",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách Iceberg Orders",
    tags=["advanced-trading", "iceberg"]
)
async def get_iceberg_orders(
    request: Request,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    page: int = Query(1, ge=1, description="Page number"),
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy danh sách Iceberg Orders với pagination và filtering
    """
    try:
        user_id = user_session["uid"]
        
        # Get all orders for user
        user_orders = [
            order for order in iceberg_orders_storage.values()
            if order.userId == user_id
        ]
        
        # Apply filters
        if symbol:
            user_orders = [order for order in user_orders if order.symbol == symbol]
        
        if status_filter:
            user_orders = [order for order in user_orders if order.status == status_filter]
        
        # Sort by creation date (newest first)
        user_orders.sort(key=lambda x: x.createdAt, reverse=True)
        
        # Apply pagination
        total = len(user_orders)
        offset = (page - 1) * limit
        paginated_orders = user_orders[offset:offset + limit]
        
        return OrderListResponse(
            success=True,
            data=[order.dict() for order in paginated_orders],
            metadata={
                "timestamp": datetime.utcnow(),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "hasNext": offset + limit < total,
                    "hasPrev": page > 1
                }
            }
        )
        
    except Exception as error:
        print("Get Iceberg Orders Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách Iceberg Orders: {str(error)}"
        )


@router.patch(
    "/api/trading/orders/iceberg",
    response_model=IcebergOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật Iceberg Order",
    tags=["advanced-trading", "iceberg"]
)
async def update_iceberg_order(
    request: Request,
    update_request: UpdateIcebergOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Cập nhật Iceberg Order (visible quantity, max slices)
    """
    try:
        user_id = user_session["uid"]
        
        # Check if order exists and belongs to user
        if update_request.orderId not in iceberg_orders_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Iceberg Order không tồn tại"
            )
        
        order = iceberg_orders_storage[update_request.orderId]
        
        if order.userId != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền cập nhật order này"
            )
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order không thể cập nhật (không còn PENDING)"
            )
        
        # Update fields
        if update_request.visibleQuantity:
            if update_request.visibleQuantity > order.remainingQuantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Visible quantity không thể vượt quá remaining quantity"
                )
            order.visibleQuantity = update_request.visibleQuantity
        
        if update_request.maxSlices:
            if update_request.maxSlices <= order.executedSlices:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Max slices phải lớn hơn executed slices"
                )
            order.maxSlices = update_request.maxSlices
        
        order.updatedAt = datetime.utcnow()
        
        # Save updated order
        iceberg_orders_storage[update_request.orderId] = order
        
        return IcebergOrderResponse(
            success=True,
            data=order,
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "Iceberg Order được cập nhật thành công"
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Update Iceberg Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật Iceberg Order: {str(error)}"
        )


# ========== OCO ORDERS ==========

@router.post(
    "/api/trading/orders/oco",
    response_model=OcoOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo OCO Order",
    tags=["advanced-trading", "oco"]
)
async def create_oco_order(
    request: Request,
    create_request: CreateOcoOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Tạo OCO (One-Cancels-Order) Order
    
    OCO order bao gồm take profit và stop loss orders.
    Khi một order được thực hiện, order kia sẽ tự động bị hủy.
    """
    try:
        user_id = user_session["uid"]
        
        # Check user balance
        user_balance = 10000.0  # Mock balance
        required_margin = create_request.quantity * max(
            create_request.takeProfitPrice, 
            create_request.stopLossPrice
        ) * 0.1
        
        if user_balance < required_margin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số dư không đủ để tạo OCO Order"
            )
        
        # Create OCO order
        oco_order_id = f"OCO_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create take profit order
        take_profit_order_id = f"TP_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        # Create stop loss order
        stop_loss_order_id = f"SL_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        oco_order = OcoOrder(
            orderId=oco_order_id,
            userId=user_id,
            symbol=create_request.symbol,
            orders={
                "takeProfit": {
                    "orderId": take_profit_order_id,
                    "side": create_request.side,
                    "price": create_request.takeProfitPrice,
                    "quantity": create_request.quantity,
                    "status": OrderStatus.PENDING
                },
                "stopLoss": {
                    "orderId": stop_loss_order_id,
                    "side": create_request.side,
                    "price": create_request.stopLossPrice,
                    "quantity": create_request.quantity,
                    "status": OrderStatus.PENDING
                }
            }
        )
        
        # Store in memory
        oco_orders_storage[oco_order_id] = oco_order
        
        print(f"OCO order created: {oco_order_id} for user {user_id}")
        
        return OcoOrderResponse(
            success=True,
            data=oco_order,
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "OCO Order được tạo thành công"
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Create OCO Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo OCO Order: {str(error)}"
        )


@router.get(
    "/api/trading/orders/oco",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách OCO Orders",
    tags=["advanced-trading", "oco"]
)
async def get_oco_orders(
    request: Request,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    page: int = Query(1, ge=1, description="Page number"),
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy danh sách OCO Orders với pagination và filtering
    """
    try:
        user_id = user_session["uid"]
        
        # Get all orders for user
        user_orders = [
            order for order in oco_orders_storage.values()
            if order.userId == user_id
        ]
        
        # Apply filters
        if symbol:
            user_orders = [order for order in user_orders if order.symbol == symbol]
        
        if status_filter:
            user_orders = [order for order in user_orders if order.status == status_filter]
        
        # Sort by creation date
        user_orders.sort(key=lambda x: x.createdAt, reverse=True)
        
        # Apply pagination
        total = len(user_orders)
        offset = (page - 1) * limit
        paginated_orders = user_orders[offset:offset + limit]
        
        return OrderListResponse(
            success=True,
            data=[order.dict() for order in paginated_orders],
            metadata={
                "timestamp": datetime.utcnow(),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "hasNext": offset + limit < total,
                    "hasPrev": page > 1
                }
            }
        )
        
    except Exception as error:
        print("Get OCO Orders Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách OCO Orders: {str(error)}"
        )


# ========== TRAILING STOP ORDERS ==========

@router.post(
    "/api/trading/orders/trailing-stop",
    response_model=TrailingStopOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo Trailing Stop Order",
    tags=["advanced-trading", "trailing-stop"]
)
async def create_trailing_stop_order(
    request: Request,
    create_request: CreateTrailingStopOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Tạo Trailing Stop Order
    
    Trailing stop order tự động điều chỉnh stop price theo giá thị trường
    """
    try:
        user_id = user_session["uid"]
        
        # Get current market price
        current_price = get_mock_current_price(create_request.symbol)
        
        if not current_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể lấy giá hiện tại cho symbol {create_request.symbol}"
            )
        
        # Check activation price logic
        if create_request.activationPrice:
            if create_request.side == OrderSide.BUY and create_request.activationPrice > current_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Activation price cho BUY order phải thấp hơn giá hiện tại"
                )
            elif create_request.side == OrderSide.SELL and create_request.activationPrice < current_price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Activation price cho SELL order phải cao hơn giá hiện tại"
                )
        
        # Check user balance
        user_balance = 10000.0  # Mock balance
        required_margin = current_price * create_request.quantity * 0.1
        
        if user_balance < required_margin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số dư không đủ để tạo Trailing Stop Order"
            )
        
        # Calculate initial stop price
        if create_request.trailingType.value == "PERCENTAGE":
            percentage = create_request.trailValue / 100
            initial_stop_price = current_price * (1 - percentage) if create_request.side == OrderSide.BUY else current_price * (1 + percentage)
        else:  # FIXED_AMOUNT
            initial_stop_price = current_price - create_request.trailValue if create_request.side == OrderSide.BUY else current_price + create_request.trailValue
        
        # Create trailing stop order
        trailing_stop_order_id = f"TRAILING_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        trailing_stop_order = TrailingStopOrder(
            orderId=trailing_stop_order_id,
            userId=user_id,
            symbol=create_request.symbol,
            side=create_request.side,
            quantity=create_request.quantity,
            trailingType=create_request.trailingType,
            trailValue=create_request.trailValue,
            currentTrailValue=create_request.trailValue,
            stopPrice=initial_stop_price,
            activationPrice=create_request.activationPrice,
            timeInForce=create_request.timeInForce
        )
        
        # Store in memory
        trailing_stop_orders_storage[trailing_stop_order_id] = trailing_stop_order
        
        print(f"Trailing stop order created: {trailing_stop_order_id} for user {user_id}")
        
        return TrailingStopOrderResponse(
            success=True,
            data=trailing_stop_order,
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "Trailing Stop Order được tạo thành công",
                "currentPrice": current_price
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Create Trailing Stop Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo Trailing Stop Order: {str(error)}"
        )


@router.get(
    "/api/trading/orders/trailing-stop",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách Trailing Stop Orders",
    tags=["advanced-trading", "trailing-stop"]
)
async def get_trailing_stop_orders(
    request: Request,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status_filter: Optional[OrderStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    page: int = Query(1, ge=1, description="Page number"),
    user_session: dict = Depends(verify_user_session)
):
    """
    Lấy danh sách Trailing Stop Orders với pagination và filtering
    """
    try:
        user_id = user_session["uid"]
        
        # Get all orders for user
        user_orders = [
            order for order in trailing_stop_orders_storage.values()
            if order.userId == user_id
        ]
        
        # Apply filters
        if symbol:
            user_orders = [order for order in user_orders if order.symbol == symbol]
        
        if status_filter:
            user_orders = [order for order in user_orders if order.status == status_filter]
        
        # Sort by creation date
        user_orders.sort(key=lambda x: x.createdAt, reverse=True)
        
        # Apply pagination
        total = len(user_orders)
        offset = (page - 1) * limit
        paginated_orders = user_orders[offset:offset + limit]
        
        return OrderListResponse(
            success=True,
            data=[order.dict() for order in paginated_orders],
            metadata={
                "timestamp": datetime.utcnow(),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "hasNext": offset + limit < total,
                    "hasPrev": page > 1
                }
            }
        )
        
    except Exception as error:
        print("Get Trailing Stop Orders Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy danh sách Trailing Stop Orders: {str(error)}"
        )


@router.patch(
    "/api/trading/orders/trailing-stop",
    response_model=TrailingStopOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật Trailing Stop Order",
    tags=["advanced-trading", "trailing-stop"]
)
async def update_trailing_stop_order(
    request: Request,
    update_request: UpdateTrailingStopOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Cập nhật Trailing Stop Order (trail value, activation price, stop price)
    """
    try:
        user_id = user_session["uid"]
        
        # Check if order exists and belongs to user
        if update_request.orderId not in trailing_stop_orders_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trailing Stop Order không tồn tại"
            )
        
        order = trailing_stop_orders_storage[update_request.orderId]
        
        if order.userId != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền cập nhật order này"
            )
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order không thể cập nhật (không còn PENDING)"
            )
        
        # Update fields
        if update_request.trailValue:
            order.trailValue = update_request.trailValue
            order.currentTrailValue = update_request.trailValue
        
        if update_request.activationPrice is not None:
            order.activationPrice = update_request.activationPrice
        
        if update_request.stopPrice:
            order.stopPrice = update_request.stopPrice
        
        order.updatedAt = datetime.utcnow()
        
        # Save updated order
        trailing_stop_orders_storage[update_request.orderId] = order
        
        return TrailingStopOrderResponse(
            success=True,
            data=order,
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "Trailing Stop Order được cập nhật thành công"
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Update Trailing Stop Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật Trailing Stop Order: {str(error)}"
        )


@router.delete(
    "/api/trading/orders/trailing-stop",
    response_model=TrailingStopOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Hủy Trailing Stop Order",
    tags=["advanced-trading", "trailing-stop"]
)
async def cancel_trailing_stop_order(
    request: Request,
    cancel_request: CancelTrailingStopOrderRequest,
    user_session: dict = Depends(verify_user_session)
):
    """
    Hủy Trailing Stop Order
    """
    try:
        user_id = user_session["uid"]
        
        # Check if order exists and belongs to user
        if cancel_request.orderId not in trailing_stop_orders_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trailing Stop Order không tồn tại"
            )
        
        order = trailing_stop_orders_storage[cancel_request.orderId]
        
        if order.userId != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền hủy order này"
            )
        
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order không thể hủy (không còn PENDING)"
            )
        
        # Update order status to cancelled
        order.status = OrderStatus.CANCELLED
        order.updatedAt = datetime.utcnow()
        
        # Save updated order
        trailing_stop_orders_storage[cancel_request.orderId] = order
        
        return TrailingStopOrderResponse(
            success=True,
            data={"orderId": cancel_request.orderId, "status": OrderStatus.CANCELLED},
            metadata={
                "timestamp": datetime.utcnow(),
                "message": "Trailing Stop Order đã được hủy thành công"
            }
        )
        
    except HTTPException:
        raise
    except Exception as error:
        print("Cancel Trailing Stop Order Error:", error)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi hủy Trailing Stop Order: {str(error)}"
        )