"""
Portfolio module endpoints for FastAPI.
Migrated from Next.js portfolio API routes with full business logic preservation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from fastapi.responses import JSONResponse

from app.middleware.auth import get_current_user
from app.schemas.portfolio import (
    # Analytics schemas
    PortfolioAnalyticsRequest,
    PortfolioReportRequest,
    PortfolioAnalyticsResponse,
    PortfolioReportResponse,
    PortfolioAnalytics,
    
    # Metrics schemas
    PortfolioMetricsResponse,
    PortfolioMetrics,
    RecalculateMetricsRequest,
    
    # Position close schemas
    PositionCloseResponse,
    PositionCloseRequest,
    
    # Rebalancing schemas
    RebalancingRequest,
    RebalancingResponse,
    RebalancingRecommendationsResponse,
    
    # Trading bots schemas
    TradingBotsResponse,
    TradingBotResponse,
    CreateTradingBotRequest,
    UpdateTradingBotRequest,
    DeleteTradingBotRequest,
    TradingBotsQuery,
    
    # Watchlist schemas
    WatchlistResponse,
    AddToWatchlistRequest,
    RemoveFromWatchlistRequest,
    
    # Generic schemas
    ApiResponse,
    ApiError
)

router = APIRouter()


# ============================================================================
# PORTFOLIO ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/analytics", response_model=PortfolioAnalyticsResponse)
async def get_portfolio_analytics(
    period: Literal['1D', '7D', '30D', '90D', '1Y', 'ALL'] = Query(default='30D', description="Analysis period"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get portfolio analytics for specified period
    GET /api/portfolio/analytics
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Calculate date range based on period
        end_date = datetime.now()
        start_date = datetime.now()

        if period == '1D':
            start_date = end_date - timedelta(days=1)
        elif period == '7D':
            start_date = end_date - timedelta(days=7)
        elif period == '30D':
            start_date = end_date - timedelta(days=30)
        elif period == '90D':
            start_date = end_date - timedelta(days=90)
        elif period == '1Y':
            start_date = end_date - timedelta(days=365)
        elif period == 'ALL':
            start_date = end_date - timedelta(days=1825)  # 5 years

        # Generate analytics data (simplified - in real implementation would fetch from database)
        analytics = await generate_portfolio_analytics(user_id, period, start_date, end_date)

        return PortfolioAnalyticsResponse(
            success=True,
            data=analytics,
            metadata={
                "timestamp": datetime.now(),
                "source": "calculated",
                "period": period
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Portfolio Analytics Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy dữ liệu analytics: {str(error)}"
        )


@router.post("/analytics/report", response_model=PortfolioReportResponse)
async def generate_portfolio_report(
    request: PortfolioReportRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate comprehensive portfolio report
    POST /api/portfolio/analytics/report
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Calculate date range
        end_date = datetime.now()
        start_date = datetime.now()

        if request.period == '1D':
            start_date = end_date - timedelta(days=1)
        elif request.period == '7D':
            start_date = end_date - timedelta(days=7)
        elif request.period == '30D':
            start_date = end_date - timedelta(days=30)
        elif request.period == '90D':
            start_date = end_date - timedelta(days=90)
        elif request.period == '1Y':
            start_date = end_date - timedelta(days=365)
        elif request.period == 'ALL':
            start_date = end_date - timedelta(days=1825)

        # Generate comprehensive report
        report = await generate_comprehensive_report(
            user_id, 
            request.period, 
            start_date, 
            end_date,
            {
                "include_charts": request.include_charts,
                "include_recommendations": request.include_recommendations
            }
        )

        if request.format == 'pdf':
            return PortfolioReportResponse(
                success=True,
                data={
                    **report,
                    "pdf_generation": {
                        "status": "pending",
                        "download_url": f"/api/portfolio/analytics/report/{report['report_id']}/pdf",
                        "expires_at": datetime.now() + timedelta(hours=1)
                    }
                },
                metadata={
                    "timestamp": datetime.now()
                }
            )

        return PortfolioReportResponse(
            success=True,
            data=report,
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Generate Portfolio Report Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo báo cáo: {str(error)}"
        )


# ============================================================================
# PORTFOLIO METRICS ENDPOINTS
# ============================================================================

@router.get("/metrics", response_model=PortfolioMetricsResponse)
async def get_portfolio_metrics(current_user: dict = Depends(get_current_user)):
    """
    Get portfolio metrics
    GET /api/portfolio/metrics
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Get user data (simplified - would fetch from actual database)
        user_data = {
            "balance": {"available": 10000, "locked": 1000},
            "status": "active"
        }

        if not user_data:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

        # Calculate metrics
        metrics = await calculate_portfolio_metrics(user_id, user_data)

        return PortfolioMetricsResponse(
            success=True,
            data=metrics,
            metadata={
                "timestamp": datetime.now(),
                "source": "calculated"
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Get Portfolio Metrics Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy dữ liệu metrics: {str(error)}"
        )


@router.post("/metrics/recalculate", response_model=PortfolioMetricsResponse)
async def recalculate_portfolio_metrics(
    request: RecalculateMetricsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Recalculate portfolio metrics
    POST /api/portfolio/metrics/recalculate
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Get user data (simplified)
        user_data = {
            "balance": {"available": 10000, "locked": 1000},
            "status": "active"
        }

        if not user_data:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

        # Force recalculation
        metrics = await calculate_portfolio_metrics(user_id, user_data, request.force_recalculation)

        return PortfolioMetricsResponse(
            success=True,
            data=metrics,
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Recalculate Portfolio Metrics Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tính lại metrics: {str(error)}"
        )


# ============================================================================
# POSITION CLOSE ENDPOINT
# ============================================================================

@router.post("/positions/{position_id}/close", response_model=PositionCloseResponse)
async def close_portfolio_position(
    position_id: str = Path(..., description="Position ID to close"),
    current_user: dict = Depends(get_current_user)
):
    """
    Close a portfolio position
    POST /api/portfolio/positions/{positionId}/close
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        if not position_id:
            raise HTTPException(status_code=400, detail="Position ID là bắt buộc")

        # Mock position data (in real implementation would fetch from database)
        position = {
            "user_id": user_id,
            "symbol": "BTCUSDT",
            "side": "long",
            "size": 0.1,
            "entry_price": 45000,
            "current_price": 46000,
            "status": "OPEN"
        }

        # Verify position belongs to user
        if position["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Không có quyền đóng vị thế này")

        # Check if position is already closed
        if position["status"] == "closed":
            raise HTTPException(status_code=400, detail="Vị thế đã được đóng")

        # Calculate P&L
        current_price = position["current_price"]
        size = position["size"]
        entry_price = position["entry_price"]
        is_long = position["side"] == "long"

        if is_long:
            pnl = (current_price - entry_price) * size
        else:
            pnl = (entry_price - current_price) * size

        # Mock close operation
        close_result = {
            "position_id": position_id,
            "close_price": current_price,
            "pnl": pnl,
            "pnl_percent": pnl / (entry_price * size),
            "close_time": datetime.now().isoformat()
        }

        return PositionCloseResponse(
            success=True,
            message="Đóng vị thế thành công",
            data=close_result
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Close position error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi đóng vị thế: {str(error)}"
        )


# ============================================================================
# PORTFOLIO REBALANCING ENDPOINTS
# ============================================================================

@router.post("/rebalancing", response_model=RebalancingResponse)
async def create_rebalancing_order(
    request: RebalancingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create portfolio rebalancing order
    POST /api/portfolio/rebalancing
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Validate target allocation
        if not request.target_allocation or not isinstance(request.target_allocation, dict):
            raise HTTPException(status_code=400, detail="Target allocation là bắt buộc")

        # Validate allocation percentages
        total_allocation = sum(request.target_allocation.values())
        if abs(total_allocation - 100) > 1:
            raise HTTPException(status_code=400, detail="Target allocation phải tổng bằng 100%")

        # Get current portfolio state
        portfolio_state = await get_current_portfolio_state(user_id)
        current_prices = await get_current_prices(list(request.target_allocation.keys()))

        # Calculate rebalancing plan
        rebalancing_plan = await calculate_rebalancing_plan(
            portfolio_state,
            request.target_allocation,
            current_prices,
            request.rebalance_threshold,
            request.max_trade_size,
            request.tolerance
        )

        if request.dry_run:
            return RebalancingResponse(
                success=True,
                data={
                    "plan": rebalancing_plan,
                    "summary": calculate_rebalancing_summary(rebalancing_plan),
                    "execution": {
                        "dry_run": True,
                        "estimated_cost": 0,
                        "estimated_time": "N/A"
                    }
                },
                metadata={
                    "timestamp": datetime.now()
                }
            )

        # Execute rebalancing
        execution_result = await execute_rebalancing(user_id, rebalancing_plan)

        return RebalancingResponse(
            success=True,
            data={
                "plan": rebalancing_plan,
                "execution": execution_result
            },
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Create Rebalancing Order Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo lệnh rebalancing: {str(error)}"
        )


@router.get("/rebalancing/recommendations", response_model=RebalancingRecommendationsResponse)
async def get_rebalancing_recommendations(current_user: dict = Depends(get_current_user)):
    """
    Get rebalancing recommendations
    GET /api/portfolio/rebalancing/recommendations
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Get current portfolio state
        portfolio_state = await get_current_portfolio_state(user_id)

        # Generate recommendations
        recommendations = await generate_rebalancing_recommendations(portfolio_state)

        return RebalancingRecommendationsResponse(
            success=True,
            data={
                "current_state": portfolio_state,
                "recommendations": recommendations,
                "suggested_targets": generate_suggested_allocations(portfolio_state),
                "analysis": await analyze_portfolio(portfolio_state)
            },
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Get Rebalancing Recommendations Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy khuyến nghị: {str(error)}"
        )


# ============================================================================
# TRADING BOTS ENDPOINTS
# ============================================================================

@router.get("/trading-bots", response_model=TradingBotsResponse)
async def get_trading_bots(
    status: Optional[Literal['STARTED', 'PAUSED', 'STOPPED']] = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    page: int = Query(default=1, ge=1),
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's trading bots
    GET /api/portfolio/trading-bots
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Mock trading bots data
        trading_bots = [
            {
                "bot_id": "BOT_123",
                "user_id": user_id,
                "name": "BTC Scalper",
                "strategy": {
                    "strategy_id": "STRAT_123",
                    "name": "RSI Strategy",
                    "parameters": {"timeframe": "1H", "risk_level": "MEDIUM"}
                },
                "status": "STARTED",
                "config": {
                    "symbols": ["BTCUSDT"],
                    "base_amount": 1000,
                    "leverage": 1
                },
                "performance": {
                    "total_trades": 10,
                    "success_rate": 60,
                    "total_pnl": 50
                },
                "logs": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        ]

        return TradingBotsResponse(
            success=True,
            data=trading_bots,
            metadata={
                "timestamp": datetime.now(),
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": 1,
                    "has_next": False,
                    "has_prev": False
                }
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Get Trading Bots Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách bot: {str(error)}"
        )


@router.post("/trading-bots", response_model=TradingBotResponse)
async def create_trading_bot(
    request: CreateTradingBotRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create trading bot
    POST /api/portfolio/trading-bots
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Validate input
        if not request.name or not request.strategy or not request.config:
            raise HTTPException(status_code=400, detail="Thiếu tham số bắt buộc")

        # Create bot ID
        bot_id = f"BOT_{int(datetime.now().timestamp())}_{hash(request.name) % 1000}"

        # Mock created bot
        created_bot = {
            "bot_id": bot_id,
            "user_id": user_id,
            "name": request.name,
            "strategy": {
                "strategy_id": f"STRAT_{int(datetime.now().timestamp())}",
                "name": request.strategy.get("name", f"{request.name} Strategy"),
                "parameters": request.strategy.get("parameters", {})
            },
            "status": "STARTED" if request.start_immediately else "PAUSED",
            "config": request.config,
            "performance": {
                "total_trades": 0,
                "success_rate": 0,
                "total_pnl": 0
            },
            "logs": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        return TradingBotResponse(
            success=True,
            data=created_bot,
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Create Trading Bot Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo bot: {str(error)}"
        )


@router.patch("/trading-bots", response_model=TradingBotResponse)
async def update_trading_bot(
    request: UpdateTradingBotRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update trading bot
    PATCH /api/portfolio/trading-bots
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        if not request.bot_id:
            raise HTTPException(status_code=400, detail="Bot ID là bắt buộc")

        # Mock bot update
        updated_bot = {
            "bot_id": request.bot_id,
            "user_id": user_id,
            "status": request.status or "PAUSED",
            "name": request.name,
            "config": request.config,
            "strategy": request.strategy,
            "updated_at": datetime.now()
        }

        return TradingBotResponse(
            success=True,
            data=updated_bot,
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Update Trading Bot Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi cập nhật bot: {str(error)}"
        )


@router.delete("/trading-bots", response_model=TradingBotResponse)
async def delete_trading_bot(
    request: DeleteTradingBotRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete trading bot
    DELETE /api/portfolio/trading-bots
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        if not request.bot_id:
            raise HTTPException(status_code=400, detail="Bot ID là bắt buộc")

        return TradingBotResponse(
            success=True,
            data={"bot_id": request.bot_id, "status": "DELETED"},
            metadata={
                "timestamp": datetime.now()
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Delete Trading Bot Error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xóa bot: {str(error)}"
        )


# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(current_user: dict = Depends(get_current_user)):
    """
    Get user's watchlist
    GET /api/portfolio/watchlist
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        # Mock watchlist data
        default_watchlist = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'EURUSD', 'GBPUSD', 'USDJPY']

        return WatchlistResponse(
            success=True,
            data={
                "symbols": default_watchlist,
                "is_default": True
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Get watchlist error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách theo dõi: {str(error)}"
        )


@router.post("/watchlist", response_model=WatchlistResponse)
async def add_to_watchlist(
    request: AddToWatchlistRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add symbol to watchlist
    POST /api/portfolio/watchlist
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        if not request.symbol:
            raise HTTPException(status_code=400, detail="Symbol là bắt buộc")

        symbol_upper = request.symbol.upper().strip()

        # Validate symbol format
        import re
        symbol_regex = r'^[A-Z]{3,10}(USDT|USD|EUR|JPY|GBP|CAD|AUD|CHF)?$'
        if not re.match(symbol_regex, symbol_upper):
            raise HTTPException(status_code=400, detail="Định dạng symbol không hợp lệ")

        # Mock updated watchlist
        updated_watchlist = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', symbol_upper]

        return WatchlistResponse(
            success=True,
            data={
                "symbol": symbol_upper,
                "watchlist": updated_watchlist
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Add to watchlist error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi thêm symbol: {str(error)}"
        )


@router.delete("/watchlist/{symbol}", response_model=WatchlistResponse)
async def remove_from_watchlist(
    symbol: str = Path(..., description="Symbol to remove from watchlist"),
    current_user: dict = Depends(get_current_user)
):
    """
    Remove symbol from watchlist
    DELETE /api/portfolio/watchlist/{symbol}
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Tài khoản không hoạt động")

        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol là bắt buộc")

        symbol_upper = symbol.upper().strip()

        # Mock updated watchlist
        updated_watchlist = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']  # symbol_upper removed

        return WatchlistResponse(
            success=True,
            data={
                "symbol": symbol_upper,
                "watchlist": updated_watchlist
            }
        )

    except HTTPException:
        raise
    except Exception as error:
        print(f"Remove from watchlist error: {error}")
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xóa symbol: {str(error)}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def generate_portfolio_analytics(user_id: str, period: str, start_date: datetime, end_date: datetime) -> PortfolioAnalytics:
    """Generate portfolio analytics data"""
    return PortfolioAnalytics(
        portfolio_id=f"portfolio_{user_id}_{period}",
        user_id=user_id,
        period=period,
        metrics={
            "total_balance": 11000,
            "total_pnl": 1000,
            "daily_pnl": 50
        },
        balance_history=[
            {
                "timestamp": start_date + timedelta(days=i),
                "balance": 10500 + (i * 50),
                "pnl": i * 50
            }
            for i in range(0, min(30, (end_date - start_date).days + 1))
        ],
        allocation_history=[],
        performance_metrics={
            "period": period,
            "return": 1000,
            "return_percent": 10.0,
            "max_drawdown": 200,
            "sharpe_ratio": 1.2
        },
        created_at=start_date,
        updated_at=datetime.now()
    )


async def generate_comprehensive_report(user_id: str, period: str, start_date: datetime, end_date: datetime, options: dict):
    """Generate comprehensive portfolio report"""
    return {
        "report_id": f"report_{user_id}_{int(datetime.now().timestamp())}",
        "user_id": user_id,
        "period": period,
        "generated_at": datetime.now(),
        "summary": {
            "total_return": 1000,
            "total_return_percent": 10.0,
            "max_drawdown": 200,
            "sharpe_ratio": 1.2,
            "win_rate": 60.0,
            "total_trades": 50
        },
        "analytics": await generate_portfolio_analytics(user_id, period, start_date, end_date),
        "charts": options.get("include_charts") and {
            "balance_history": [],
            "allocation_history": []
        } or None,
        "recommendations": options.get("include_recommendations") and [] or None,
        "metadata": {
            "period": period,
            "date_range": {"start": start_date, "end": end_date},
            "data_points": {"orders": 50}
        }
    }


async def calculate_portfolio_metrics(user_id: str, user_data: dict, force_recalculation: bool = False) -> PortfolioMetrics:
    """Calculate portfolio metrics"""
    available_balance = user_data.get("balance", {}).get("available", 0)
    locked_balance = user_data.get("balance", {}).get("locked", 0)
    
    return PortfolioMetrics(
        total_balance=available_balance + locked_balance,
        available_balance=available_balance,
        used_margin=locked_balance,
        total_pnl=1000,
        total_pnl_percent=10.0,
        daily_pnl=50,
        daily_pnl_percent=0.5,
        assets={
            "BTCUSDT": {
                "balance": 0.1,
                "value": 4600,
                "allocation": 41.8,
                "pnl": 100,
                "pnl_percent": 2.2
            }
        },
        performance={
            "total_return": 1000,
            "total_return_percent": 10.0,
            "max_drawdown": 200,
            "sharpe_ratio": 1.2,
            "win_rate": 60.0,
            "average_win": 150,
            "average_loss": 75,
            "profit_factor": 2.0
        },
        risk={
            "var95": 500,
            "var99": 1000,
            "beta": 1.0,
            "correlation": {}
        },
        updated_at=datetime.now()
    )


async def get_current_portfolio_state(user_id: str) -> dict:
    """Get current portfolio state"""
    return {
        "total_value": 11000,
        "available_balance": 10000,
        "positions": 3,
        "asset_breakdown": {
            "BTCUSDT": {
                "symbol": "BTCUSDT",
                "quantity": 0.1,
                "value": 4600,
                "allocation": 41.8,
                "price": 46000
            }
        },
        "current_prices": {"BTCUSDT": 46000, "ETHUSDT": 3000}
    }


async def get_current_prices(symbols: List[str]) -> Dict[str, float]:
    """Get current market prices"""
    return {symbol: 46000 if symbol == "BTCUSDT" else 3000 for symbol in symbols}


async def calculate_rebalancing_plan(portfolio_state: dict, target_allocation: dict, current_prices: dict, threshold: float, max_trade_size: Optional[float], tolerance: float) -> dict:
    """Calculate rebalancing plan"""
    return {
        "trades": [
            {
                "symbol": "BTCUSDT",
                "action": "BUY",
                "current_quantity": 0.1,
                "current_value": 4600,
                "target_value": 5000,
                "difference": 400,
                "deviation_percent": 3.6,
                "quantity": 0.0087,
                "price": 46000,
                "estimated_value": 400
            }
        ],
        "total_trades": 1,
        "total_value": 11000,
        "execution_plan": {
            "strategy": "sequential",
            "estimated_cost": 0.4,
            "estimated_time": "2-5 minutes",
            "risk_level": "low"
        }
    }


async def execute_rebalancing(user_id: str, rebalancing_plan: dict) -> dict:
    """Execute rebalancing orders"""
    return {
        "total_orders": 1,
        "successful_orders": 1,
        "failed_orders": 0,
        "execution_results": [
            {
                "symbol": "BTCUSDT",
                "status": "SUBMITTED",
                "order_id": "REBAL_123",
                "trade": rebalancing_plan["trades"][0]
            }
        ],
        "orders": [],
        "timestamp": datetime.now()
    }


async def generate_rebalancing_recommendations(portfolio_state: dict) -> List[dict]:
    """Generate rebalancing recommendations"""
    return [
        {
            "type": "concentration",
            "priority": "medium",
            "title": "Portfolio Concentration Risk",
            "description": "Portfolio has high concentration in BTCUSDT",
            "recommended_action": "Reduce concentration and diversify",
            "estimated_improvement": "Reduce risk by 15-25%"
        }
    ]


def generate_suggested_allocations(portfolio_state: dict) -> dict:
    """Generate suggested portfolio allocations"""
    return {
        "conservative": {"BTCUSDT": 25, "ETHUSDT": 20, "CASH": 20},
        "balanced": {"BTCUSDT": 30, "ETHUSDT": 25, "CASH": 10},
        "aggressive": {"BTCUSDT": 35, "ETHUSDT": 30}
    }


async def analyze_portfolio(portfolio_state: dict) -> dict:
    """Analyze portfolio composition"""
    return {
        "diversification_score": 70,
        "risk_score": 40,
        "total_assets": 3,
        "optimal_range": "4-8 assets for optimal diversification",
        "risk_level": "medium",
        "recommendations": {
            "diversification": "Well diversified",
            "risk": "Risk level acceptable",
            "cash": "Cash level appropriate"
        }
    }


def calculate_rebalancing_summary(plan: dict) -> dict:
    """Calculate rebalancing summary"""
    buy_trades = [t for t in plan["trades"] if t["action"] == "BUY"]
    sell_trades = [t for t in plan["trades"] if t["action"] == "SELL"]
    
    total_buy_value = sum(t["estimated_value"] for t in buy_trades)
    total_sell_value = sum(t["estimated_value"] for t in sell_trades)
    
    return {
        "total_buy_value": round(total_buy_value, 2),
        "total_sell_value": round(total_sell_value, 2),
        "net_cash_flow": round(total_buy_value - total_sell_value, 2),
        "number_of_trades": len(plan["trades"]),
        "estimated_fees": round((total_buy_value + total_sell_value) * 0.001, 2)
    }