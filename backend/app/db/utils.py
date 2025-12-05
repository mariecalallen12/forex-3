"""
Database Utilities
Digital Utopia Platform

Các tiện ích cho database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import logging

from .session import engine, SessionLocal, Base
from ..models import (
    User, UserProfile, Role, Permission, RolePermission,
    TradingOrder, PortfolioPosition,
    Transaction, WalletBalance, ExchangeRate,
    KYCDocument, ComplianceEvent, RiskAssessment, AMLScreening,
    TradingBot, Watchlist,
    ReferralCode, ReferralRegistration,
    AuditLog, AnalyticsEvent
)
from ..core.security import get_password_hash

logger = logging.getLogger(__name__)


def create_tables():
    """
    Tạo tất cả bảng trong database
    """
    Base.metadata.create_all(bind=engine)
    logger.info("All database tables created successfully")


def drop_tables():
    """
    Xóa tất cả bảng trong database
    WARNING: Chỉ sử dụng trong development/testing
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")


def seed_roles(db: Session) -> List[Role]:
    """
    Seed default roles
    
    Returns:
        List[Role]: Danh sách roles đã tạo
    """
    default_roles = [
        {"name": "owner", "description": "Chủ sở hữu hệ thống với toàn quyền", "is_system_role": True},
        {"name": "admin", "description": "Quản trị viên với quyền quản lý", "is_system_role": True},
        {"name": "staff", "description": "Nhân viên với quyền hạn chế", "is_system_role": True},
        {"name": "customer", "description": "Khách hàng", "is_system_role": True}
    ]
    
    roles = []
    for role_data in default_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
            roles.append(role)
            logger.info(f"Created role: {role_data['name']}")
        else:
            roles.append(existing)
    
    db.commit()
    return roles


def seed_permissions(db: Session) -> List[Permission]:
    """
    Seed default permissions
    
    Returns:
        List[Permission]: Danh sách permissions đã tạo
    """
    default_permissions = [
        # User permissions
        {"name": "user.create", "description": "Tạo user mới", "resource": "users", "action": "create"},
        {"name": "user.read", "description": "Xem thông tin user", "resource": "users", "action": "read"},
        {"name": "user.update", "description": "Cập nhật user", "resource": "users", "action": "update"},
        {"name": "user.delete", "description": "Xóa user", "resource": "users", "action": "delete"},
        
        # Trading permissions
        {"name": "trading.place_order", "description": "Đặt lệnh giao dịch", "resource": "trading", "action": "create"},
        {"name": "trading.view_positions", "description": "Xem vị thế", "resource": "trading", "action": "read"},
        {"name": "trading.cancel_order", "description": "Hủy lệnh", "resource": "trading", "action": "delete"},
        
        # Financial permissions
        {"name": "financial.deposit", "description": "Nạp tiền", "resource": "financial", "action": "create"},
        {"name": "financial.withdraw", "description": "Rút tiền", "resource": "financial", "action": "create"},
        {"name": "financial.view_transactions", "description": "Xem giao dịch", "resource": "financial", "action": "read"},
        
        # Admin permissions
        {"name": "admin.dashboard", "description": "Truy cập admin dashboard", "resource": "admin", "action": "read"},
        {"name": "admin.manage_users", "description": "Quản lý users", "resource": "admin", "action": "manage"},
        {"name": "admin.view_reports", "description": "Xem báo cáo", "resource": "admin", "action": "read"},
        
        # Compliance permissions
        {"name": "compliance.view_kyc", "description": "Xem KYC", "resource": "compliance", "action": "read"},
        {"name": "compliance.verify_kyc", "description": "Xác minh KYC", "resource": "compliance", "action": "update"},
        {"name": "compliance.view_aml", "description": "Xem AML", "resource": "compliance", "action": "read"},
        {"name": "compliance.manage_events", "description": "Quản lý compliance events", "resource": "compliance", "action": "manage"},
    ]
    
    permissions = []
    for perm_data in default_permissions:
        existing = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
        if not existing:
            perm = Permission(**perm_data)
            db.add(perm)
            permissions.append(perm)
            logger.info(f"Created permission: {perm_data['name']}")
        else:
            permissions.append(existing)
    
    db.commit()
    return permissions


def seed_role_permissions(db: Session):
    """
    Seed role-permission mappings
    """
    # Get roles
    owner = db.query(Role).filter(Role.name == "owner").first()
    admin = db.query(Role).filter(Role.name == "admin").first()
    staff = db.query(Role).filter(Role.name == "staff").first()
    customer = db.query(Role).filter(Role.name == "customer").first()
    
    # Get all permissions
    all_permissions = db.query(Permission).all()
    
    # Owner gets all permissions
    if owner:
        for perm in all_permissions:
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == owner.id,
                RolePermission.permission_id == perm.id
            ).first()
            if not existing:
                db.add(RolePermission(role_id=owner.id, permission_id=perm.id))
    
    # Admin gets most permissions except owner-specific
    if admin:
        admin_permissions = [p for p in all_permissions if not p.name.startswith("owner.")]
        for perm in admin_permissions:
            existing = db.query(RolePermission).filter(
                RolePermission.role_id == admin.id,
                RolePermission.permission_id == perm.id
            ).first()
            if not existing:
                db.add(RolePermission(role_id=admin.id, permission_id=perm.id))
    
    # Staff gets limited permissions
    if staff:
        staff_permission_names = [
            "user.read", "trading.view_positions", "financial.view_transactions",
            "compliance.view_kyc", "compliance.view_aml"
        ]
        for perm in all_permissions:
            if perm.name in staff_permission_names:
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == staff.id,
                    RolePermission.permission_id == perm.id
                ).first()
                if not existing:
                    db.add(RolePermission(role_id=staff.id, permission_id=perm.id))
    
    # Customer gets basic permissions
    if customer:
        customer_permission_names = [
            "user.read", "trading.place_order", "trading.view_positions",
            "trading.cancel_order", "financial.deposit", "financial.withdraw",
            "financial.view_transactions"
        ]
        for perm in all_permissions:
            if perm.name in customer_permission_names:
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == customer.id,
                    RolePermission.permission_id == perm.id
                ).first()
                if not existing:
                    db.add(RolePermission(role_id=customer.id, permission_id=perm.id))
    
    db.commit()
    logger.info("Role-permission mappings seeded successfully")


def seed_exchange_rates(db: Session) -> List[ExchangeRate]:
    """
    Seed default exchange rates
    
    Returns:
        List[ExchangeRate]: Danh sách exchange rates đã tạo
    """
    from decimal import Decimal
    
    default_rates = [
        {"base_asset": "USD", "target_asset": "VND", "rate": Decimal("24250"), "priority": 1},
        {"base_asset": "VND", "target_asset": "USD", "rate": Decimal("0.0000412"), "priority": 2},
        {"base_asset": "USD", "target_asset": "EUR", "rate": Decimal("0.92"), "priority": 3},
        {"base_asset": "EUR", "target_asset": "USD", "rate": Decimal("1.087"), "priority": 4},
        {"base_asset": "USD", "target_asset": "GBP", "rate": Decimal("0.79"), "priority": 5},
        {"base_asset": "GBP", "target_asset": "USD", "rate": Decimal("1.266"), "priority": 6},
        {"base_asset": "USD", "target_asset": "CNY", "rate": Decimal("7.23"), "priority": 7},
        {"base_asset": "CNY", "target_asset": "USD", "rate": Decimal("0.138"), "priority": 8},
    ]
    
    rates = []
    for rate_data in default_rates:
        existing = db.query(ExchangeRate).filter(
            ExchangeRate.base_asset == rate_data["base_asset"],
            ExchangeRate.target_asset == rate_data["target_asset"]
        ).first()
        if not existing:
            rate = ExchangeRate(**rate_data, is_active=True, source="internal")
            db.add(rate)
            rates.append(rate)
            logger.info(f"Created exchange rate: {rate_data['base_asset']}/{rate_data['target_asset']}")
        else:
            rates.append(existing)
    
    db.commit()
    return rates


def seed_admin_user(db: Session, email: str = "admin@digitalutopia.com", password: str = "Admin@123") -> User:
    """
    Seed admin user
    
    Args:
        db: Database session
        email: Admin email
        password: Admin password
        
    Returns:
        User: Admin user
    """
    # Check if admin exists
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        logger.info(f"Admin user already exists: {email}")
        return existing
    
    # Get admin role
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    
    # Create admin user
    admin_user = User(
        email=email,
        password_hash=get_password_hash(password),
        role_id=admin_role.id if admin_role else None,
        status="active",
        email_verified=True,
        kyc_status="verified"
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Create admin profile
    admin_profile = UserProfile(
        user_id=admin_user.id,
        full_name="System Administrator",
        display_name="Admin"
    )
    db.add(admin_profile)
    db.commit()
    
    logger.info(f"Admin user created: {email}")
    return admin_user


def seed_all(db: Session = None):
    """
    Seed tất cả dữ liệu mặc định
    """
    if db is None:
        db = SessionLocal()
    
    try:
        logger.info("Starting database seeding...")
        
        # Create tables
        create_tables()
        
        # Seed data
        seed_roles(db)
        seed_permissions(db)
        seed_role_permissions(db)
        seed_exchange_rates(db)
        seed_admin_user(db)
        
        logger.info("Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        if db:
            db.close()


def check_database_health() -> Dict[str, Any]:
    """
    Kiểm tra health của database
    
    Returns:
        Dict với thông tin health check
    """
    result = {
        "status": "unknown",
        "connected": False,
        "tables_count": 0,
        "error": None
    }
    
    try:
        with engine.connect() as conn:
            # Test connection
            conn.execute(text("SELECT 1"))
            result["connected"] = True
            
            # Count tables
            tables_query = text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_count = conn.execute(tables_query).scalar()
            result["tables_count"] = tables_count
            
            result["status"] = "healthy"
            
    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    return result
