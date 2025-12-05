"""
Portfolio module schemas for FastAPI endpoints.
Migrated from Next.js Next.js portfolio API routes.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field


# Analytics Schemas
class PortfolioAnalyticsRequest(BaseModel):
    """Request model for portfolio analytics"""
    period: Literal['1D', '7D', '30D', '90D', '1Y', 'ALL'] = Field(default='30D', description="Analysis period")


class PortfolioReportRequest(BaseModel):
    """Request model for portfolio report generation"""
    period: Literal['1D', '7D', '30D', '90D', '1Y', 'ALL'] = Field(default='30D', description="Report period")
    include_charts: bool = Field(default=True, description="Include charts in report")
    include_recommendations: bool = Field(default=True, description="Include recommendations in report")
    format: Literal['json', 'pdf'] = Field(default='json', description="Report format")


class BalanceHistoryPoint(BaseModel):
    """Single balance history point"""
    timestamp: datetime
    balance: float
    pnl: float


class AssetAllocationPoint(BaseModel):
    """Single asset allocation point"""
    timestamp: datetime
    assets: List[Dict[str, Any]]


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    period: str
    return_amount: float = Field(description="Absolute return amount")
    return_percent: float = Field(description="Return percentage")
    max_drawdown: float = Field(description="Maximum drawdown")
    sharpe_ratio: float = Field(description="Sharpe ratio")


class PortfolioAnalytics(BaseModel):
    """Portfolio analytics response"""
    portfolio_id: str
    user_id: str
    period: str
    metrics: Dict[str, Any]
    balance_history: List[BalanceHistoryPoint]
    allocation_history: List[AssetAllocationPoint]
    performance_metrics: PerformanceMetrics
    created_at: datetime
    updated_at: datetime


class PortfolioAnalyticsResponse(BaseModel):
    """Analytics response wrapper"""
    success: bool
    data: PortfolioAnalytics
    metadata: Dict[str, Any]


class PortfolioReportResponse(BaseModel):
    """Portfolio report response"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]


# Metrics Schemas
class PortfolioMetrics(BaseModel):
    """Comprehensive portfolio metrics"""
    total_balance: float
    available_balance: float
    used_margin: float
    total_pnl: float
    total_pnl_percent: float
    daily_pnl: float
    daily_pnl_percent: float
    assets: Dict[str, Any]
    performance: Dict[str, Any]
    risk: Dict[str, Any]
    updated_at: datetime


class PortfolioMetricsResponse(BaseModel):
    """Metrics response wrapper"""
    success: bool
    data: PortfolioMetrics
    metadata: Dict[str, Any]


class RecalculateMetricsRequest(BaseModel):
    """Request model for recalculating metrics"""
    force_recalculation: bool = Field(default=False, description="Force recalculation ignoring cache")


# Position Close Schemas
class PositionCloseRequest(BaseModel):
    """Request model for closing a position"""
    pass  # Position ID comes from URL path


class PositionCloseResponse(BaseModel):
    """Response model for position close"""
    success: bool
    message: str
    data: Dict[str, Any]


# Rebalancing Schemas
class RebalancingRequest(BaseModel):
    """Request model for portfolio rebalancing"""
    target_allocation: Dict[str, float] = Field(description="Target allocation percentages")
    rebalance_threshold: float = Field(default=5.0, description="% deviation to trigger rebalancing")
    max_trade_size: Optional[float] = Field(default=None, description="Maximum trade size in USDT")
    tolerance: float = Field(default=1.0, description="% tolerance for target allocation")
    dry_run: bool = Field(default=False, description="If true, only calculate without executing")


class RebalancingTrade(BaseModel):
    """Individual rebalancing trade"""
    symbol: str
    action: Literal['BUY', 'SELL']
    current_quantity: float
    current_value: float
    target_value: float
    difference: float
    deviation_percent: float
    quantity: float
    price: float
    estimated_value: float


class RebalancingPlan(BaseModel):
    """Portfolio rebalancing plan"""
    trades: List[RebalancingTrade]
    total_trades: int
    total_value: float
    execution_plan: Dict[str, Any]


class RebalancingSummary(BaseModel):
    """Rebalancing summary"""
    total_buy_value: float
    total_sell_value: float
    net_cash_flow: float
    number_of_trades: int
    estimated_fees: float


class RebalancingResponse(BaseModel):
    """Rebalancing response wrapper"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]


# Rebalancing Recommendations Schemas
class RebalancingRecommendation(BaseModel):
    """Single rebalancing recommendation"""
    type: str
    priority: Literal['low', 'medium', 'high']
    title: str
    description: str
    recommended_action: Optional[str] = None
    estimated_improvement: Optional[str] = None


class PortfolioAnalysis(BaseModel):
    """Portfolio analysis results"""
    diversification_score: int
    risk_score: int
    total_assets: int
    optimal_range: str
    risk_level: Literal['low', 'medium', 'high']
    recommendations: Dict[str, str]


class SuggestedAllocations(BaseModel):
    """Suggested portfolio allocations"""
    conservative: Dict[str, float]
    balanced: Dict[str, float]
    aggressive: Dict[str, float]


class RebalancingRecommendationsResponse(BaseModel):
    """Rebalancing recommendations response"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]


# Trading Bots Schemas
class TradingBotConfig(BaseModel):
    """Trading bot configuration"""
    symbols: List[str]
    base_amount: float
    leverage: int
    max_concurrent_orders: int
    risk_management: Dict[str, Any]


class TradingBotPerformance(BaseModel):
    """Trading bot performance metrics"""
    total_trades: int
    success_rate: float
    total_pnl: float
    total_pnl_percent: float
    average_trade_time: float
    max_drawdown: float


class BotLog(BaseModel):
    """Trading bot log entry"""
    timestamp: datetime
    level: Literal['INFO', 'WARNING', 'ERROR']
    message: str
    data: Optional[Dict[str, Any]] = None


class TradingBotStrategy(BaseModel):
    """Trading bot strategy"""
    strategy_id: str
    user_id: str
    name: str
    description: str
    strategy_type: str
    parameters: Dict[str, Any]
    performance: Dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime


class TradingBot(BaseModel):
    """Trading bot model"""
    bot_id: str
    user_id: str
    name: str
    strategy: TradingBotStrategy
    status: Literal['STARTED', 'PAUSED', 'STOPPED']
    config: TradingBotConfig
    performance: TradingBotPerformance
    logs: List[BotLog]
    created_at: datetime
    updated_at: datetime


class CreateTradingBotRequest(BaseModel):
    """Request model for creating trading bot"""
    name: str = Field(min_length=3, max_length=100)
    strategy: Dict[str, Any]
    config: Dict[str, Any]
    start_immediately: bool = Field(default=False)


class UpdateTradingBotRequest(BaseModel):
    """Request model for updating trading bot"""
    bot_id: str
    name: Optional[str] = None
    status: Optional[Literal['STARTED', 'PAUSED', 'STOPPED']] = None
    config: Optional[Dict[str, Any]] = None
    strategy: Optional[Dict[str, Any]] = None


class DeleteTradingBotRequest(BaseModel):
    """Request model for deleting trading bot"""
    bot_id: str


class TradingBotsResponse(BaseModel):
    """Trading bots response wrapper"""
    success: bool
    data: List[TradingBot]
    metadata: Dict[str, Any]


class TradingBotResponse(BaseModel):
    """Single trading bot response wrapper"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]


class TradingBotsQuery(BaseModel):
    """Query parameters for trading bots"""
    status: Optional[Literal['STARTED', 'PAUSED', 'STOPPED']] = None
    limit: int = Field(default=50, ge=1, le=100)
    page: int = Field(default=1, ge=1)


# Watchlist Schemas
class WatchlistResponse(BaseModel):
    """Watchlist response wrapper"""
    success: bool
    data: Dict[str, Any]


class AddToWatchlistRequest(BaseModel):
    """Request model for adding symbol to watchlist"""
    symbol: str = Field(description="Trading symbol to add")


class RemoveFromWatchlistRequest(BaseModel):
    """Request model for removing symbol from watchlist"""
    symbol: str = Field(description="Trading symbol to remove")


# Generic API Response Schemas
class ApiResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int
    limit: int
    total: int
    has_next: bool
    has_prev: bool


class ApiError(BaseModel):
    """API error response"""
    code: str
    message: str
    details: Optional[str] = None