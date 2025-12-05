"""
API Endpoints Package
Migration from Next.js API routes to FastAPI routers
"""

from .auth import router as auth_router
from .client import router as client_router
from .admin import router as admin_router
from .financial import router as financial_router
from .trading import router as trading_router
from .market import router as market_router
from .portfolio import router as portfolio_router
from .compliance import router as compliance_router
from .risk_management import router as risk_management_router
from .staff_referrals import router as staff_referrals_router
from .users import router as users_router
from .advanced_trading import router as advanced_trading_router

__all__ = [
    "auth_router",
    "client_router", 
    "admin_router",
    "financial_router",
    "trading_router",
    "market_router",
    "portfolio_router",
    "compliance_router",
    "risk_management_router",
    "staff_referrals_router",
    "users_router",
    "advanced_trading_router"
]
