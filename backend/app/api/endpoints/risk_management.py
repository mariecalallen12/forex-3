"""
Risk Management API Endpoints
Phase 5: Risk Management & Compliance
Author: MiniMax Agent
Date: 2025-12-05
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import math
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.schemas.risk_management import (
    RiskAssessmentResponse,
    PortfolioRisk,
    RiskExposure,
    RiskLimit,
    CreateRiskLimitRequest,
    UpdateRiskLimitRequest,
    RiskLimitResponse,
    StressTestRequest,
    StressTestResult,
    MarginAccount,
    Position,
    RiskAlert,
    MarginCall,
    RiskManagementResponse,
    CacheClearResponse,
    RiskCalculationParams,
    RiskLevel,
    LimitType,
    LimitStatus,
    AlertSeverity,
    AlertType,
    StressTestScenario,
    PositionSide
)

from app.middleware.auth import get_current_user

# Initialize router
router = APIRouter()

# In-memory storage for risk management (in production, use database)
risk_cache: Dict[str, Dict[str, Any]] = {}
risk_limits: List[RiskLimit] = []
position_risks: List[RiskExposure] = []
portfolio_risks: List[PortfolioRisk] = []
risk_alerts: List[RiskAlert] = []
margin_calls: List[MarginCall] = []
margin_accounts: List[MarginAccount] = []
positions: List[Position] = []

# Cache duration (5 minutes)
CACHE_DURATION = 5 * 60

# Valid limit types
VALID_LIMIT_TYPES = [
    LimitType.POSITION_SIZE,
    LimitType.EXPOSURE, 
    LimitType.LEVERAGE,
    LimitType.DAILY_LOSS,
    LimitType.DAILY_VOLUME
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def get_cache_key(user_id: str) -> str:
    """Generate cache key for user"""
    return f"risk_assessment_{user_id}"


def calculate_portfolio_risk_metrics(user_id: str) -> PortfolioRisk:
    """
    Calculate comprehensive portfolio risk metrics
    Based on Next.js business logic with 100% feature parity
    """
    try:
        # Get user positions
        user_positions = [p for p in positions if p.user_id == user_id and p.unrealized_pnl != 0]
        
        if not user_positions:
            # Return neutral risk metrics for empty portfolio
            return PortfolioRisk(
                total_exposure=0.0,
                total_portfolio_value=0.0,
                exposure_percentage=0.0,
                risk_score=50.0,  # Neutral risk score
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                var95=0.0,
                var99=0.0,
                concentration_risk=0.0,
                correlation_risk=0.0,
                liquidity_risk=0.0,
                market_risk=0.0,
                calculated_at=datetime.utcnow()
            )
        
        # Calculate total exposure and portfolio value
        total_exposure = 0.0
        total_portfolio_value = 0.0
        symbol_exposure: Dict[str, float] = {}
        
        for position in user_positions:
            position_value = position.size * position.current_price
            total_exposure += abs(position_value)
            total_portfolio_value += position_value
            
            if position.symbol in symbol_exposure:
                symbol_exposure[position.symbol] += abs(position_value)
            else:
                symbol_exposure[position.symbol] = abs(position_value)
        
        # Calculate exposure percentage
        exposure_percentage = (total_exposure / abs(total_portfolio_value) * 100) if total_portfolio_value > 0 else 0
        
        # Calculate risk score (0-100)
        risk_score = 0.0
        
        # Concentration risk (top symbol exposure %)
        max_symbol_exposure = max(symbol_exposure.values()) if symbol_exposure else 0
        concentration_risk = (max_symbol_exposure / total_exposure * 100) if total_exposure > 0 else 0
        risk_score += min(concentration_risk * 0.4, 40)  # Max 40 points
        
        # Leverage risk
        leveraged_positions = [p for p in user_positions if p.leverage > 1]
        leverage_ratio = len(leveraged_positions) / len(user_positions) if user_positions else 0
        risk_score += min(leverage_ratio * 30, 30)  # Max 30 points
        
        # Diversification risk
        symbol_count = len(symbol_exposure)
        diversification_score = max(0, (10 - symbol_count) / 10 * 20)  # Max 20 points
        risk_score += diversification_score
        
        # Volatility risk (simplified calculation)
        volatility_risk = min(total_exposure / 100000 * 10, 10)  # Max 10 points
        risk_score += volatility_risk
        
        # Clamp risk score between 0-100
        risk_score = max(0, min(risk_score, 100))
        
        # Calculate Value at Risk (simplified 95% VaR)
        volatility = math.sqrt(0.02 if symbol_count > 1 else 0.05)  # Simplified volatility
        var95 = total_exposure * volatility * 1.645  # 95% confidence level
        var99 = total_exposure * volatility * 2.326  # 99% confidence level
        
        # Calculate max drawdown (simplified)
        max_drawdown = min(risk_score / 100 * 0.2, 0.2)  # Max 20%
        
        # Calculate Sharpe ratio (simplified)
        expected_return = 0.08  # 8% annual return assumption
        sharpe_ratio = expected_return / volatility if total_exposure > 0 else 0
        
        # Calculate additional risk metrics
        correlation_risk = concentration_risk * 0.6  # Simplified correlation risk
        liquidity_risk = min(0.1 if symbol_count < 3 else 0, 0.1)  # Simplified liquidity risk
        market_risk = volatility_risk * 10  # Simplified market risk
        
        return PortfolioRisk(
            total_exposure=total_exposure,
            total_portfolio_value=total_portfolio_value,
            exposure_percentage=exposure_percentage,
            risk_score=risk_score,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            var95=var95,
            var99=var99,
            concentration_risk=concentration_risk,
            correlation_risk=correlation_risk,
            liquidity_risk=liquidity_risk,
            market_risk=market_risk,
            calculated_at=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error calculating portfolio risk: {error}")
        
        # Return default risk metrics if calculation fails
        return PortfolioRisk(
            total_exposure=0.0,
            total_portfolio_value=0.0,
            exposure_percentage=0.0,
            risk_score=50.0,  # Neutral risk score
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            var95=0.0,
            var99=0.0,
            concentration_risk=0.0,
            correlation_risk=0.0,
            liquidity_risk=0.0,
            market_risk=0.0,
            calculated_at=datetime.utcnow()
        )


def calculate_position_risks(user_id: str) -> List[RiskExposure]:
    """
    Calculate position-specific risk metrics
    Based on Next.js business logic
    """
    try:
        user_positions = [p for p in positions if p.user_id == user_id and p.unrealized_pnl != 0]
        risks: List[RiskExposure] = []
        
        for position in user_positions:
            position_value = abs(position.size * position.current_price)
            exposure_percentage = position_value / 100000 * 100  # Simplified percentage
            
            # Calculate risk score
            risk_score = min(
                (position.leverage - 1) * 10 + 
                (20 if position_value > 10000 else 0) + 
                abs(position.unrealized_pnl / position_value * 100) if position_value > 0 else 0,
                100
            )
            
            # Determine risk level
            risk_level = RiskLevel.LOW
            if risk_score > 80:
                risk_level = RiskLevel.CRITICAL
            elif risk_score > 60:
                risk_level = RiskLevel.HIGH
            elif risk_score > 30:
                risk_level = RiskLevel.MEDIUM
            
            risk_exposure = RiskExposure(
                id=generate_id(),
                user_id=user_id,
                symbol=position.symbol,
                position_value=position_value,
                exposure_percentage=exposure_percentage,
                risk_score=risk_score,
                leverage_used=position.leverage,
                margin_used=position.margin_used,
                available_margin=position.current_price * position.size * 0.1,  # Simplified
                risk_level=risk_level,
                calculated_at=datetime.utcnow()
            )
            
            risks.append(risk_exposure)
        
        return risks
        
    except Exception as error:
        print(f"Error calculating position risks: {error}")
        return []


def generate_risk_recommendations(portfolio_risk: PortfolioRisk, position_risks: List[RiskExposure]) -> List[str]:
    """
    Generate risk management recommendations
    Based on Next.js business logic
    """
    recommendations: List[str] = []
    
    # Portfolio-level recommendations
    if portfolio_risk.risk_score > 80:
        recommendations.append("Your portfolio risk is critically high. Consider reducing position sizes or closing some positions.")
    elif portfolio_risk.risk_score > 60:
        recommendations.append("Your portfolio risk is elevated. Monitor positions closely and consider risk reduction strategies.")
    
    if portfolio_risk.concentration_risk > 50:
        recommendations.append("Your portfolio is highly concentrated. Consider diversifying across more symbols.")
    
    if portfolio_risk.exposure_percentage > 200:
        recommendations.append("Your exposure ratio is very high. Consider reducing leverage or position sizes.")
    
    # Position-level recommendations
    for risk in position_risks:
        if risk.risk_level == RiskLevel.CRITICAL:
            recommendations.append(f"Position in {risk.symbol} has critical risk level. Immediate action recommended.")
        elif risk.risk_level == RiskLevel.HIGH and risk.leverage_used > 5:
            recommendations.append(f"High leverage detected in {risk.symbol}. Consider reducing leverage.")
    
    if not recommendations:
        recommendations.append("Your risk levels appear to be within acceptable ranges. Continue monitoring.")
    
    return recommendations


def check_limit_breaches(user_id: str) -> List[RiskLimit]:
    """
    Check for risk limit breaches
    """
    breaches: List[RiskLimit] = []
    user_limits = [limit for limit in risk_limits if limit.user_id == user_id and limit.status == LimitStatus.ACTIVE]
    
    for limit in user_limits:
        # Get current values based on limit type
        current_value = 0.0
        
        if limit.limit_type == LimitType.POSITION_SIZE:
            user_positions = [p for p in positions if p.user_id == user_id and p.symbol == limit.symbol]
            current_value = sum(abs(p.size * p.current_price) for p in user_positions)
            
        elif limit.limit_type == LimitType.EXPOSURE:
            user_positions = [p for p in positions if p.user_id == user_id]
            current_value = sum(abs(p.size * p.current_price) for p in user_positions)
            
        elif limit.limit_type == LimitType.LEVERAGE:
            user_positions = [p for p in positions if p.user_id == user_id and p.symbol == limit.symbol]
            current_value = max(p.leverage for p in user_positions) if user_positions else 0
            
        elif limit.limit_type == LimitType.DAILY_LOSS:
            # Simplified daily loss calculation
            current_value = sum(abs(p.unrealized_pnl) for p in positions if p.user_id == user_id)
        
        # Check if limit is breached
        if current_value > limit.limit_value:
            limit.current_value = current_value
            limit.status = LimitStatus.BREACHED
            breaches.append(limit)
    
    return breaches


# ============================================================================
# RISK ASSESSMENT ENDPOINTS
# ============================================================================

@router.get("/assessment", response_model=RiskManagementResponse)
async def get_risk_assessment(current_user: str = Depends(get_current_user)):
    """
    Get comprehensive risk assessment
    GET /api/risk-management/assessment
    
    Returns complete portfolio risk analysis including:
    - Portfolio risk metrics
    - Position-level risk exposures
    - Risk recommendations
    - Action requirements
    """
    try:
        user_id = current_user
        
        # Check cache first
        cache_key = get_cache_key(user_id)
        cached_data = risk_cache.get(cache_key)
        
        if cached_data and (datetime.utcnow() - cached_data.get('timestamp', datetime.min)).seconds < CACHE_DURATION:
            return RiskManagementResponse(
                success=True,
                data=cached_data['data'],
                timestamp=datetime.utcnow()
            )
        
        # Calculate risk metrics
        portfolio_risk = calculate_portfolio_risk_metrics(user_id)
        position_risk_list = calculate_position_risks(user_id)
        
        # Determine overall risk level
        risk_level = RiskLevel.LOW
        if portfolio_risk.risk_score > 80:
            risk_level = RiskLevel.CRITICAL
        elif portfolio_risk.risk_score > 60:
            risk_level = RiskLevel.HIGH
        elif portfolio_risk.risk_score > 30:
            risk_level = RiskLevel.MEDIUM
        
        # Generate recommendations
        recommendations = generate_risk_recommendations(portfolio_risk, position_risk_list)
        
        # Determine if action is required
        action_required = (risk_level == RiskLevel.CRITICAL or 
                          portfolio_risk.risk_score > 70 or
                          any(r.risk_level == RiskLevel.CRITICAL for r in position_risk_list))
        
        assessment = RiskAssessmentResponse(
            user_id=user_id,
            risk_level=risk_level,
            risk_score=portfolio_risk.risk_score,
            portfolio_risk=portfolio_risk,
            position_risks=position_risk_list,
            recommendations=recommendations,
            action_required=action_required,
            calculated_at=datetime.utcnow()
        )
        
        # Cache the result
        risk_cache[cache_key] = {
            'data': assessment.dict(),
            'timestamp': datetime.utcnow()
        }
        
        return RiskManagementResponse(
            success=True,
            data=assessment,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error performing risk assessment: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'ASSESSMENT_ERROR',
                'message': 'Failed to perform risk assessment',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.post("/assessment/stress-test", response_model=RiskManagementResponse)
async def perform_stress_test(
    stress_request: StressTestRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Perform portfolio stress testing
    POST /api/risk-management/assessment/stress-test
    
    Test portfolio performance under adverse market conditions
    """
    try:
        user_id = current_user
        user_positions = [p for p in positions if p.user_id == user_id and p.unrealized_pnl != 0]
        
        # Calculate stress test results
        total_stress_loss = 0.0
        stress_results = []
        
        for position in user_positions:
            original_value = position.size * position.current_price
            stressed_price = position.current_price * (1 - stress_request.shock_percentage / 100)
            stressed_value = position.size * stressed_price
            loss = stressed_value - original_value
            total_stress_loss += loss
            
            stress_results.append({
                'symbol': position.symbol,
                'original_value': original_value,
                'stressed_value': stressed_value,
                'loss': loss,
                'loss_percentage': (loss / abs(original_value)) * 100 if original_value != 0 else 0
            })
        
        total_portfolio_value = sum(p.size * p.current_price for p in user_positions)
        
        stress_test_result = StressTestResult(
            scenario=stress_request.scenario.value,
            shock_percentage=stress_request.shock_percentage,
            total_stress_loss=total_stress_loss,
            stress_loss_percentage=(total_stress_loss / abs(total_portfolio_value) * 100) if total_portfolio_value > 0 else 0,
            position_results=stress_results,
            tested_at=datetime.utcnow()
        )
        
        return RiskManagementResponse(
            success=True,
            data=stress_test_result,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error performing stress test: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'STRESS_TEST_ERROR',
                'message': 'Failed to perform stress test',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.delete("/assessment/cache", response_model=RiskManagementResponse)
async def clear_risk_cache(current_user: str = Depends(get_current_user)):
    """
    Clear risk assessment cache
    DELETE /api/risk-management/assessment/cache
    
    Utility endpoint for clearing cached risk data
    """
    try:
        user_id = current_user
        cache_key = get_cache_key(user_id)
        
        if cache_key in risk_cache:
            del risk_cache[cache_key]
        
        return RiskManagementResponse(
            success=True,
            data={'cache_cleared': True},
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error clearing cache: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'CACHE_ERROR',
                'message': 'Failed to clear cache',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


# ============================================================================
# RISK LIMITS ENDPOINTS
# ============================================================================

@router.get("/limits", response_model=RiskManagementResponse)
async def get_risk_limits(
    limit_type: Optional[LimitType] = Query(None, description="Filter by limit type"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    current_user: str = Depends(get_current_user)
):
    """
    Get user's risk limits
    GET /api/risk-management/limits
    
    Returns risk limits with filtering options
    """
    try:
        user_id = current_user
        user_limits = [limit for limit in risk_limits if limit.user_id == user_id]
        
        # Apply filters
        if limit_type:
            user_limits = [limit for limit in user_limits if limit.limit_type == limit_type]
        
        if symbol:
            user_limits = [limit for limit in user_limits if limit.symbol == symbol]
        
        # Update current values
        for limit in user_limits:
            # Update current values based on limit type (simplified)
            limit.current_value = 0.0
            
            if limit.limit_type == LimitType.POSITION_SIZE:
                user_positions = [p for p in positions if p.user_id == user_id and p.symbol == limit.symbol]
                limit.current_value = sum(abs(p.size * p.current_price) for p in user_positions)
            elif limit.limit_type == LimitType.EXPOSURE:
                user_positions = [p for p in positions if p.user_id == user_id]
                limit.current_value = sum(abs(p.size * p.current_price) for p in user_positions)
            elif limit.limit_type == LimitType.LEVERAGE:
                user_positions = [p for p in positions if p.user_id == user_id and p.symbol == limit.symbol]
                if user_positions:
                    limit.current_value = max(p.leverage for p in user_positions)
        
        # Get current exposures and check for breaches
        position_risk_list = calculate_position_risks(user_id)
        breaches = check_limit_breaches(user_id)
        
        # Generate recommendations
        recommendations = []
        for breach in breaches:
            recommendations.append(f"Limit breach detected for {breach.symbol} - {breach.limit_type.value}. Current: {breach.current_value:.2f}, Limit: {breach.limit_value:.2f}")
        
        if not recommendations:
            recommendations.append("All risk limits are within acceptable ranges.")
        
        response_data = RiskLimitResponse(
            limits=user_limits,
            current_exposures=position_risk_list,
            breaches=breaches,
            recommendations=recommendations
        )
        
        return RiskManagementResponse(
            success=True,
            data=response_data,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error fetching risk limits: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'FETCH_ERROR',
                'message': 'Failed to fetch risk limits',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.post("/limits", response_model=RiskManagementResponse)
async def create_risk_limit(
    limit_request: CreateRiskLimitRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Create new risk limit
    POST /api/risk-management/limits
    
    Set up risk limits for position sizing, exposure, leverage, etc.
    """
    try:
        user_id = current_user
        
        # Validation
        if limit_request.limit_value <= 0:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'INVALID_LIMIT_VALUE',
                    'message': 'Limit value must be greater than 0'
                },
                timestamp=datetime.utcnow()
            )
        
        if limit_request.limit_type not in VALID_LIMIT_TYPES:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'INVALID_LIMIT_TYPE',
                    'message': f'Invalid limit type. Must be one of: {[t.value for t in VALID_LIMIT_TYPES]}'
                },
                timestamp=datetime.utcnow()
            )
        
        # Check for existing active limit of same type and symbol
        existing_limit = next(
            (limit for limit in risk_limits 
             if limit.user_id == user_id and 
                limit.symbol == limit_request.symbol and 
                limit.limit_type == limit_request.limit_type and
                limit.status == LimitStatus.ACTIVE),
            None
        )
        
        if existing_limit:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'LIMIT_EXISTS',
                    'message': 'An active limit already exists for this symbol and limit type'
                },
                timestamp=datetime.utcnow()
            )
        
        # Create new risk limit
        now = datetime.utcnow()
        new_limit = RiskLimit(
            id=generate_id(),
            user_id=user_id,
            symbol=limit_request.symbol,
            limit_type=limit_request.limit_type,
            limit_value=limit_request.limit_value,
            current_value=0.0,  # Initialize to 0
            status=LimitStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            auto_close=limit_request.auto_close
        )
        
        risk_limits.append(new_limit)
        
        return RiskManagementResponse(
            success=True,
            data=new_limit,
            timestamp=now
        )
        
    except Exception as error:
        print(f"Error creating risk limit: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'CREATE_ERROR',
                'message': 'Failed to create risk limit',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.patch("/limits", response_model=RiskManagementResponse)
async def update_risk_limit(
    update_request: UpdateRiskLimitRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Update risk limit
    PATCH /api/risk-management/limits
    
    Modify existing risk limits
    """
    try:
        user_id = current_user
        
        # Find the risk limit
        limit = next(
            (limit for limit in risk_limits if limit.id == update_request.id),
            None
        )
        
        if not limit:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'NOT_FOUND',
                    'message': 'Risk limit not found'
                },
                timestamp=datetime.utcnow()
            )
        
        # Verify ownership
        if limit.user_id != user_id:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'FORBIDDEN',
                    'message': 'You can only modify your own risk limits'
                },
                timestamp=datetime.utcnow()
            )
        
        # Apply updates
        now = datetime.utcnow()
        updates: Dict[str, Any] = {'updated_at': now}
        
        if update_request.limit_value is not None:
            if update_request.limit_value <= 0:
                return RiskManagementResponse(
                    success=False,
                    error={
                        'code': 'INVALID_LIMIT_VALUE',
                        'message': 'Limit value must be greater than 0'
                    },
                    timestamp=now
                )
            updates['limit_value'] = update_request.limit_value
        
        if update_request.status is not None:
            updates['status'] = update_request.status
        
        if update_request.auto_close is not None:
            updates['auto_close'] = update_request.auto_close
        
        # Apply updates to limit
        for key, value in updates.items():
            setattr(limit, key, value)
        
        return RiskManagementResponse(
            success=True,
            data=limit,
            timestamp=now
        )
        
    except Exception as error:
        print(f"Error updating risk limit: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'UPDATE_ERROR',
                'message': 'Failed to update risk limit',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.delete("/limits", response_model=RiskManagementResponse)
async def delete_risk_limit(
    limit_id: str = Query(..., description="Risk limit ID"),
    current_user: str = Depends(get_current_user)
):
    """
    Delete risk limit
    DELETE /api/risk-management/limits
    
    Remove risk limits
    """
    try:
        user_id = current_user
        
        # Find the risk limit
        limit = next(
            (limit for limit in risk_limits if limit.id == limit_id),
            None
        )
        
        if not limit:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'NOT_FOUND',
                    'message': 'Risk limit not found'
                },
                timestamp=datetime.utcnow()
            )
        
        # Verify ownership
        if limit.user_id != user_id:
            return RiskManagementResponse(
                success=False,
                error={
                    'code': 'FORBIDDEN',
                    'message': 'You can only delete your own risk limits'
                },
                timestamp=datetime.utcnow()
            )
        
        # Remove from storage
        risk_limits.remove(limit)
        
        return RiskManagementResponse(
            success=True,
            data={'deleted': True},
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error deleting risk limit: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'DELETE_ERROR',
                'message': 'Failed to delete risk limit',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


# ============================================================================
# ADDITIONAL RISK MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/alerts", response_model=RiskManagementResponse)
async def get_risk_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    current_user: str = Depends(get_current_user)
):
    """
    Get risk alerts
    GET /api/risk-management/alerts
    
    Returns risk alerts with filtering options
    """
    try:
        user_id = current_user
        user_alerts = [alert for alert in risk_alerts if alert.user_id == user_id]
        
        # Apply filters
        if severity:
            user_alerts = [alert for alert in user_alerts if alert.severity == severity]
        
        if resolved is not None:
            user_alerts = [alert for alert in user_alerts if alert.is_resolved == resolved]
        
        # Sort by creation date (newest first)
        user_alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        return RiskManagementResponse(
            success=True,
            data=user_alerts,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error fetching risk alerts: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'FETCH_ALERTS_ERROR',
                'message': 'Failed to fetch risk alerts',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.get("/margin-calls", response_model=RiskManagementResponse)
async def get_margin_calls(
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: str = Depends(get_current_user)
):
    """
    Get margin calls
    GET /api/risk-management/margin-calls
    
    Returns margin call alerts
    """
    try:
        user_id = current_user
        user_calls = [call for call in margin_calls if call.user_id == user_id]
        
        # Apply filters
        if status:
            user_calls = [call for call in user_calls if call.status == status]
        
        # Sort by issued date (newest first)
        user_calls.sort(key=lambda x: x.issued_at, reverse=True)
        
        return RiskManagementResponse(
            success=True,
            data=user_calls,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error fetching margin calls: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'FETCH_MARGIN_CALLS_ERROR',
                'message': 'Failed to fetch margin calls',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )


@router.get("/metrics", response_model=RiskManagementResponse)
async def get_risk_metrics(current_user: str = Depends(get_current_user)):
    """
    Get risk metrics summary
    GET /api/risk-management/metrics
    
    Returns high-level risk metrics for dashboard
    """
    try:
        user_id = current_user
        
        # Calculate metrics
        user_limits = [limit for limit in risk_limits if limit.user_id == user_id]
        active_limits = [limit for limit in user_limits if limit.status == LimitStatus.ACTIVE]
        breached_limits = [limit for limit in user_limits if limit.status == LimitStatus.BREACHED]
        
        portfolio_risk = calculate_portfolio_risk_metrics(user_id)
        position_risks = calculate_position_risks(user_id)
        critical_positions = [r for r in position_risks if r.risk_level == RiskLevel.CRITICAL]
        
        metrics = {
            'total_limits': len(user_limits),
            'active_limits': len(active_limits),
            'breached_limits': len(breached_limits),
            'portfolio_risk_score': portfolio_risk.risk_score,
            'portfolio_risk_level': portfolio_risk.risk_score,
            'total_exposure': portfolio_risk.total_exposure,
            'position_count': len([p for p in positions if p.user_id == user_id and p.unrealized_pnl != 0]),
            'critical_positions': len(critical_positions),
            'active_alerts': len([a for a in risk_alerts if a.user_id == user_id and not a.is_resolved]),
            'margin_calls': len([c for c in margin_calls if c.user_id == user_id and c.status == 'pending']),
            'calculated_at': datetime.utcnow()
        }
        
        return RiskManagementResponse(
            success=True,
            data=metrics,
            timestamp=datetime.utcnow()
        )
        
    except Exception as error:
        print(f"Error calculating risk metrics: {error}")
        return RiskManagementResponse(
            success=False,
            error={
                'code': 'METRICS_ERROR',
                'message': 'Failed to calculate risk metrics',
                'details': str(error)
            },
            timestamp=datetime.utcnow()
        )