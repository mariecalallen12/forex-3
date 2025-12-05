"""
Digital Utopia Platform - FastAPI Backend
Main Application Entry Point

Migration from: Next.js 14.2.18 + React 18.2.0
Migration to: FastAPI + Vue.js 3 + TypeScript

Principle: Maintain 100% of existing functionality and content
Only change the implementation language and framework.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Digital Utopia Platform FastAPI Backend Starting...")
    
    # Initialize database connections
    # Setup authentication
    # Load configuration
    
    yield
    
    # Shutdown
    logger.info("🛑 Digital Utopia Platform FastAPI Backend Shutting Down...")

# Create FastAPI application
app = FastAPI(
    title="Digital Utopia Platform",
    description="High-performance API backend migrated from Next.js to FastAPI",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3001", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint - maintains Next.js API structure"""
    return {
        "message": "Digital Utopia Platform - FastAPI Backend",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "Test endpoint working", "status": "ok"}

@app.get("/api/health")
async def health_check():
    """
    Health Check Endpoint
    Migrated from: Next.js /api/health
    Maintains exact same response structure and functionality
    """
    import time
    import psutil
    
    return {
        "status": "ok",
        "service": "backend",
        "version": "2.0.0",
        "uptime": f"{time.time() - psutil.boot_time():.3f}s",
        "memory": {
            "rss": f"{psutil.virtual_memory().percent}%",
            "available": f"{psutil.virtual_memory().available / 1024 / 1024:.1f} MB"
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    }

# Import and register API routers
from app.api.endpoints import auth, client, admin, financial, trading, market, portfolio, compliance, risk_management, staff_referrals, users, advanced_trading

# Phase 1: Authentication endpoints (migrated from Next.js)
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# Phase 1: Client endpoints (migrated from Next.js)
app.include_router(client.router, prefix="/api/client", tags=["client"])

# Phase 1: Admin endpoints (migrated from Next.js)
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Phase 1: Financial endpoints (migrated from Next.js)
app.include_router(financial.router, prefix="/api/financial", tags=["financial"])

# Phase 1: Trading endpoints (migrated from Next.js)
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])

# Phase 1: Market data endpoints (migrated from Next.js)
app.include_router(market.router, prefix="/api/market", tags=["market"])

# Phase 1: Portfolio endpoints (migrated from Next.js)
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])

# Phase 1: Compliance endpoints (migrated from Next.js)
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])

# Phase 1: Risk Management endpoints (migrated from Next.js)
app.include_router(risk_management.router, prefix="/api/risk-management", tags=["risk-management"])

# Phase 1: Staff Referral Management endpoints (migrated from Next.js)
app.include_router(staff_referrals.router, prefix="/api/staff", tags=["staff"])

# Phase 1: User Management endpoints (migrated from Next.js)
app.include_router(users.router, prefix="/api", tags=["users"])

# Phase 1: Advanced Trading Orders endpoints (migrated from Next.js)
app.include_router(advanced_trading.router, prefix="/api", tags=["advanced-trading"])

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )