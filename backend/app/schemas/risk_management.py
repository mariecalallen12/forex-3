"""
Risk Management Module Schemas
Phase 5: Risk Management & Compliance
Author: MiniMax Agent
Date: 2025-12-05
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class RiskLevel(str, Enum):
    """Risk level enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LimitType(str, Enum):
    """Risk limit type enumeration"""
    POSITION_SIZE = "position_size"
    EXPOSURE = "exposure"
    LEVERAGE = "leverage"
    DAILY_LOSS = "daily_loss"
    DAILY_VOLUME = "daily_volume"


class LimitStatus(str, Enum):
    """Risk limit status enumeration"""
    ACTIVE = "active"
    BREACHED = "breached"
    DISABLED = "disabled"


class AlertSeverity(str, Enum):
    """Alert severity enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Alert type enumeration"""
    POSITION_LIMIT = "position_limit"
    EXPOSURE_LIMIT = "exposure_limit"
    MARGIN_CALL = "margin_call"
    RISK_THRESHOLD = "risk_threshold"
    COMPLIANCE_VIOLATION = "compliance_violation"


class MarginAccountStatus(str, Enum):
    """Margin account status enumeration"""
    ACTIVE = "active"
    RESTRICTED = "restricted"
    LIQUIDATED = "liquidated"
    CLOSED = "closed"


class AccountType(str, Enum):
    """Account type enumeration"""
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    INSTITUTIONAL = "institutional"


class PositionSide(str, Enum):
    """Position side enumeration"""
    LONG = "long"
    SHORT = "short"


class StressTestScenario(str, Enum):
    """Stress test scenario enumeration"""
    MARKET_CRASH = "market_crash"
    FLASH_CRASH = "flash_crash"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    HIGH_VOLATILITY = "high_volatility"
    CUSTOME = "custom"


# ============================================================================
# CORE RISK MANAGEMENT SCHEMAS
# ============================================================================

class RiskLimit(BaseModel):
    """Risk limit schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    limit_type: LimitType = Field(..., description="Type of limit")
    limit_value: float = Field(..., gt=0, description="Limit value")
    current_value: float = Field(default=0, description="Current value")
    status: LimitStatus = Field(default=LimitStatus.ACTIVE, description="Limit status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
    auto_close: bool = Field(default=False, description="Auto close position when limit breached")

    class Config:
        use_enum_values = True


class PositionLimit(BaseModel):
    """Position limit schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    limit_type: LimitType = Field(LimitType.POSITION_SIZE, description="Limit type")
    limit_value: float = Field(..., gt=0, description="Limit value")
    current_value: float = Field(default=0, description="Current value")
    max_position: float = Field(..., gt=0, description="Maximum position size")
    max_exposure: float = Field(..., gt=0, description="Maximum exposure")
    max_leverage: float = Field(..., gt=0, description="Maximum leverage")
    status: LimitStatus = Field(default=LimitStatus.ACTIVE, description="Limit status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
    auto_close: bool = Field(default=False, description="Auto close position when limit breached")

    class Config:
        use_enum_values = True


class DailyLimit(BaseModel):
    """Daily limit schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    limit_type: LimitType = Field(LimitType.DAILY_LOSS, description="Limit type")
    limit_value: float = Field(..., gt=0, description="Limit value")
    current_value: float = Field(default=0, description="Current value")
    daily_loss_limit: float = Field(..., gt=0, description="Daily loss limit")
    daily_volume_limit: float = Field(..., gt=0, description="Daily volume limit")
    current_daily_loss: float = Field(default=0, description="Current daily loss")
    current_daily_volume: float = Field(default=0, description="Current daily volume")
    status: LimitStatus = Field(default=LimitStatus.ACTIVE, description="Limit status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")
    auto_close: bool = Field(default=False, description="Auto close position when limit breached")

    class Config:
        use_enum_values = True


class RiskExposure(BaseModel):
    """Risk exposure schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    position_value: float = Field(..., description="Position value")
    exposure_percentage: float = Field(..., description="Exposure percentage")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    leverage_used: float = Field(..., ge=1, description="Leverage used")
    margin_used: float = Field(..., ge=0, description="Margin used")
    available_margin: float = Field(..., ge=0, description="Available margin")
    risk_level: RiskLevel = Field(..., description="Risk level")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Calculation timestamp")

    class Config:
        use_enum_values = True


class PortfolioRisk(BaseModel):
    """Portfolio risk schema"""
    total_exposure: float = Field(..., description="Total exposure")
    total_portfolio_value: float = Field(..., description="Total portfolio value")
    exposure_percentage: float = Field(..., description="Exposure percentage")
    risk_score: float = Field(..., ge=0, le=100, description="Risk score (0-100)")
    max_drawdown: float = Field(..., ge=0, le=1, description="Maximum drawdown")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    var95: float = Field(..., description="Value at Risk 95%")
    var99: float = Field(..., description="Value at Risk 99%")
    concentration_risk: float = Field(..., ge=0, description="Concentration risk")
    correlation_risk: float = Field(..., ge=0, description="Correlation risk")
    liquidity_risk: float = Field(..., ge=0, le=1, description="Liquidity risk")
    market_risk: float = Field(..., ge=0, description="Market risk")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Calculation timestamp")


class RiskAlert(BaseModel):
    """Risk alert schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    alert_type: AlertType = Field(..., description="Alert type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Alert data")
    is_read: bool = Field(default=False, description="Alert read status")
    is_resolved: bool = Field(default=False, description="Alert resolved status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")


class MarginCall(BaseModel):
    """Margin call schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    position_id: str = Field(..., description="Position ID")
    symbol: str = Field(..., description="Trading symbol")
    margin_required: float = Field(..., ge=0, description="Margin required")
    margin_available: float = Field(..., ge=0, description="Margin available")
    margin_shortfall: float = Field(..., ge=0, description="Margin shortfall")
    liquidation_price: float = Field(..., gt=0, description="Liquidation price")
    current_price: float = Field(..., gt=0, description="Current price")
    status: str = Field(default="pending", description="Margin call status")
    issued_at: datetime = Field(default_factory=datetime.utcnow, description="Issued timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")


# ============================================================================
# ASSESSMENT & ANALYSIS SCHEMAS
# ============================================================================

class RiskAssessmentResponse(BaseModel):
    """Risk assessment response schema"""
    user_id: str = Field(..., description="User ID")
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0, le=100, description="Overall risk score")
    portfolio_risk: PortfolioRisk = Field(..., description="Portfolio risk metrics")
    position_risks: List[RiskExposure] = Field(default_factory=list, description="Position risk exposures")
    recommendations: List[str] = Field(default_factory=list, description="Risk recommendations")
    action_required: bool = Field(..., description="Whether action is required")
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="Calculation timestamp")

    class Config:
        use_enum_values = True


class StressTestRequest(BaseModel):
    """Stress test request schema"""
    scenario: StressTestScenario = Field(..., description="Stress test scenario")
    shock_percentage: float = Field(..., gt=0, le=100, description="Shock percentage")

    class Config:
        use_enum_values = True


class StressTestResult(BaseModel):
    """Stress test result schema"""
    scenario: str = Field(..., description="Test scenario")
    shock_percentage: float = Field(..., description="Shock percentage")
    total_stress_loss: float = Field(..., description="Total stress loss")
    stress_loss_percentage: float = Field(..., description="Stress loss percentage")
    position_results: List[Dict[str, Any]] = Field(default_factory=list, description="Position test results")
    tested_at: datetime = Field(default_factory=datetime.utcnow, description="Test timestamp")


# ============================================================================
# LIMITS MANAGEMENT SCHEMAS
# ============================================================================

class CreateRiskLimitRequest(BaseModel):
    """Create risk limit request schema"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    limit_type: LimitType = Field(..., description="Limit type")
    limit_value: float = Field(..., gt=0, description="Limit value")
    auto_close: bool = Field(default=False, description="Auto close position when limit breached")

    class Config:
        use_enum_values = True


class UpdateRiskLimitRequest(BaseModel):
    """Update risk limit request schema"""
    id: str = Field(..., description="Risk limit ID")
    limit_value: Optional[float] = Field(None, gt=0, description="New limit value")
    status: Optional[LimitStatus] = Field(None, description="Limit status")
    auto_close: Optional[bool] = Field(None, description="Auto close setting")

    class Config:
        use_enum_values = True


class RiskLimitResponse(BaseModel):
    """Risk limit response schema"""
    limits: List[RiskLimit] = Field(default_factory=list, description="Risk limits")
    current_exposures: List[RiskExposure] = Field(default_factory=list, description="Current exposures")
    breaches: List[RiskLimit] = Field(default_factory=list, description="Limit breaches")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


# ============================================================================
# MARGIN & POSITION SCHEMAS
# ============================================================================

class MarginAccount(BaseModel):
    """Margin account schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    account_type: AccountType = Field(..., description="Account type")
    currency: str = Field(..., description="Account currency")
    total_balance: float = Field(..., ge=0, description="Total balance")
    available_balance: float = Field(..., ge=0, description="Available balance")
    margin_used: float = Field(..., ge=0, description="Margin used")
    margin_available: float = Field(..., ge=0, description="Margin available")
    maintenance_margin: float = Field(..., ge=0, description="Maintenance margin")
    initial_margin: float = Field(..., ge=0, description="Initial margin")
    leverage: float = Field(..., ge=1, description="Leverage")
    margin_level: float = Field(..., gt=0, description="Margin level")
    status: MarginAccountStatus = Field(..., description="Account status")
    opened_at: datetime = Field(default_factory=datetime.utcnow, description="Account opened timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        use_enum_values = True


class Position(BaseModel):
    """Position schema"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    side: PositionSide = Field(..., description="Position side")
    size: float = Field(..., gt=0, description="Position size")
    entry_price: float = Field(..., gt=0, description="Entry price")
    current_price: float = Field(..., gt=0, description="Current price")
    margin_used: float = Field(..., ge=0, description="Margin used")
    unrealized_pnl: float = Field(..., description="Unrealized P&L")
    leverage: float = Field(..., ge=1, description="Leverage")
    liquidation_price: float = Field(..., gt=0, description="Liquidation price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    opened_at: datetime = Field(default_factory=datetime.utcnow, description="Position opened timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        use_enum_values = True


# ============================================================================
# MONITORING & CONFIGURATION SCHEMAS
# ============================================================================

class RiskMonitoringConfig(BaseModel):
    """Risk monitoring configuration schema"""
    user_id: str = Field(..., description="User ID")
    enabled: bool = Field(default=True, description="Monitoring enabled")
    alert_thresholds: Dict[str, float] = Field(
        default_factory=lambda: {
            "position_limit": 80.0,
            "exposure_limit": 70.0,
            "daily_loss_limit": 50.0,
            "margin_level": 150.0
        },
        description="Alert thresholds"
    )
    notification_methods: List[str] = Field(
        default_factory=lambda: ["email", "push"],
        description="Notification methods"
    )
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class RiskManagementResponse(BaseModel):
    """Generic risk management response schema"""
    success: bool = Field(..., description="Operation success")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CacheClearResponse(BaseModel):
    """Cache clear response schema"""
    cache_cleared: bool = Field(..., description="Cache cleared status")


# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class RiskCalculationParams(BaseModel):
    """Risk calculation parameters schema"""
    user_id: str = Field(..., description="User ID")
    include_positions: bool = Field(default=True, description="Include position calculations")
    detailed_analysis: bool = Field(default=True, description="Include detailed analysis")
    calculate_var: bool = Field(default=True, description="Calculate Value at Risk")
    stress_test: bool = Field(default=False, description="Include stress testing")


# Export all schemas
__all__ = [
    # Enums
    "RiskLevel",
    "LimitType", 
    "LimitStatus",
    "AlertSeverity",
    "AlertType",
    "MarginAccountStatus",
    "AccountType",
    "PositionSide",
    "StressTestScenario",
    
    # Core schemas
    "RiskLimit",
    "PositionLimit", 
    "DailyLimit",
    "RiskExposure",
    "PortfolioRisk",
    "RiskAlert",
    "MarginCall",
    
    # Assessment schemas
    "RiskAssessmentResponse",
    "StressTestRequest",
    "StressTestResult",
    
    # Limits schemas
    "CreateRiskLimitRequest",
    "UpdateRiskLimitRequest", 
    "RiskLimitResponse",
    
    # Margin & Position schemas
    "MarginAccount",
    "Position",
    
    # Monitoring schemas
    "RiskMonitoringConfig",
    
    # Response schemas
    "RiskManagementResponse",
    "CacheClearResponse",
    
    # Utility schemas
    "RiskCalculationParams"
]