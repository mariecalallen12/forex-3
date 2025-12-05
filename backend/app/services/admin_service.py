"""
Admin Service
Digital Utopia Platform

Business logic cho Admin operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from datetime import datetime, timedelta
import logging

from ..models.user import User, UserProfile, Role
from ..models.trading import TradingOrder, PortfolioPosition
from ..models.financial import Transaction, WalletBalance
from ..models.compliance import ComplianceEvent
from ..models.audit import AuditLog
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)


class AdminService:
    """
    Service class cho Admin operations
    
    Cung cấp business logic cho:
    - User management
    - Platform statistics
    - System monitoring
    - Audit logs
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo AdminService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== User Management ===============
    
    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        role_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lấy danh sách users với pagination và filter
        
        Args:
            skip: Số records bỏ qua
            limit: Số records tối đa
            status: Filter theo status
            role_id: Filter theo role
            search: Tìm kiếm theo email
            
        Returns:
            Dict với users và pagination info
        """
        query = self.db.query(User)
        
        if status:
            query = query.filter(User.status == status)
        if role_id:
            query = query.filter(User.role_id == role_id)
        if search:
            query = query.filter(User.email.ilike(f"%{search}%"))
        
        total = query.count()
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        
        return {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    def update_user_status(
        self,
        user_id: int,
        status: str,
        admin_id: int,
        reason: Optional[str] = None
    ) -> Optional[User]:
        """
        Cập nhật status của user
        
        Args:
            user_id: User ID
            status: Status mới (active, suspended, deleted)
            admin_id: Admin user ID
            reason: Lý do thay đổi
            
        Returns:
            User đã cập nhật
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        old_status = user.status
        user.status = status
        
        # Create audit log
        self._create_audit_log(
            user_id=admin_id,
            action="user.status_update",
            resource_type="user",
            resource_id=str(user_id),
            old_values={"status": old_status},
            new_values={"status": status, "reason": reason}
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User {user_id} status updated to {status} by admin {admin_id}")
        return user
    
    def assign_role(
        self,
        user_id: int,
        role_id: int,
        admin_id: int
    ) -> Optional[User]:
        """
        Gán role cho user
        
        Args:
            user_id: User ID
            role_id: Role ID mới
            admin_id: Admin user ID
            
        Returns:
            User đã cập nhật
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        old_role_id = user.role_id
        user.role_id = role_id
        
        # Create audit log
        self._create_audit_log(
            user_id=admin_id,
            action="user.role_assign",
            resource_type="user",
            resource_id=str(user_id),
            old_values={"role_id": old_role_id},
            new_values={"role_id": role_id}
        )
        
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User {user_id} role updated to {role_id} by admin {admin_id}")
        return user
    
    # =============== Platform Statistics ===============
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê tổng quan platform
        
        Returns:
            Dict với các thống kê
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get_json("admin:platform_stats")
            if cached:
                return cached
        
        # User stats
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.status == "active").count()
        verified_users = self.db.query(User).filter(User.kyc_status == "verified").count()
        
        # Get users registered today
        today = datetime.utcnow().date()
        new_users_today = self.db.query(User).filter(
            func.date(User.created_at) == today
        ).count()
        
        # Trading stats
        total_orders = self.db.query(TradingOrder).count()
        pending_orders = self.db.query(TradingOrder).filter(
            TradingOrder.status == "pending"
        ).count()
        
        # Financial stats
        total_transactions = self.db.query(Transaction).count()
        pending_withdrawals = self.db.query(Transaction).filter(
            and_(
                Transaction.transaction_type == "withdrawal",
                Transaction.status == "pending"
            )
        ).count()
        
        # Compliance stats
        open_compliance_events = self.db.query(ComplianceEvent).filter(
            ComplianceEvent.status == "open"
        ).count()
        
        stats = {
            "users": {
                "total": total_users,
                "active": active_users,
                "verified": verified_users,
                "new_today": new_users_today
            },
            "trading": {
                "total_orders": total_orders,
                "pending_orders": pending_orders
            },
            "financial": {
                "total_transactions": total_transactions,
                "pending_withdrawals": pending_withdrawals
            },
            "compliance": {
                "open_events": open_compliance_events
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache for 5 minutes
        if self.cache:
            self.cache.set_json("admin:platform_stats", stats, ttl=300)
        
        return stats
    
    def get_user_performance(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy thống kê hiệu suất của một user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict với các thống kê
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Trading stats
        total_orders = self.db.query(TradingOrder).filter(
            TradingOrder.user_id == user_id
        ).count()
        
        filled_orders = self.db.query(TradingOrder).filter(
            and_(
                TradingOrder.user_id == user_id,
                TradingOrder.status == "filled"
            )
        ).count()
        
        # Position stats
        open_positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.user_id == user_id,
                PortfolioPosition.is_closed == False
            )
        ).count()
        
        # Balance stats
        balances = self.db.query(WalletBalance).filter(
            WalletBalance.user_id == user_id
        ).all()
        
        total_balance = sum(float(b.available_balance or 0) + float(b.locked_balance or 0) for b in balances)
        
        # Transaction stats
        deposits = self.db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "deposit",
                Transaction.status == "completed"
            )
        ).scalar() or 0
        
        withdrawals = self.db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_type == "withdrawal",
                Transaction.status == "completed"
            )
        ).scalar() or 0
        
        return {
            "user_id": user_id,
            "email": user.email,
            "status": user.status,
            "kyc_status": user.kyc_status,
            "trading": {
                "total_orders": total_orders,
                "filled_orders": filled_orders,
                "fill_rate": round(filled_orders / total_orders * 100, 2) if total_orders > 0 else 0,
                "open_positions": open_positions
            },
            "financial": {
                "total_balance": total_balance,
                "total_deposits": float(deposits),
                "total_withdrawals": float(withdrawals),
                "net_flow": float(deposits) - float(withdrawals)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # =============== Audit Logs ===============
    
    def _create_audit_log(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: str,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None
    ) -> AuditLog:
        """Tạo audit log"""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            result="success",
            category="admin"
        )
        
        self.db.add(audit_log)
        return audit_log
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Lấy danh sách audit logs
        
        Args:
            user_id: Filter theo user
            action: Filter theo action
            resource_type: Filter theo resource type
            skip: Số records bỏ qua
            limit: Số records tối đa
            
        Returns:
            Danh sách AuditLog
        """
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        return query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
    
    # =============== Role Management ===============
    
    def list_roles(self) -> List[Role]:
        """Lấy danh sách tất cả roles"""
        return self.db.query(Role).all()
    
    def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        admin_id: int = None
    ) -> Role:
        """
        Tạo role mới
        
        Args:
            name: Tên role
            description: Mô tả
            admin_id: Admin user ID
            
        Returns:
            Role mới
        """
        role = Role(
            name=name,
            description=description,
            is_system_role=False
        )
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        if admin_id:
            self._create_audit_log(
                user_id=admin_id,
                action="role.create",
                resource_type="role",
                resource_id=str(role.id),
                new_values={"name": name, "description": description}
            )
            self.db.commit()
        
        logger.info(f"Role created: {role.id} ({name})")
        return role
