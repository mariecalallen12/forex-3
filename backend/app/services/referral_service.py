"""
Referral Service
Digital Utopia Platform

Business logic cho Staff Referral operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
import logging
import secrets
import string

from ..models.referral import ReferralCode, ReferralRegistration
from ..models.user import User
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)

# =============== Error Messages (Vietnamese) ===============
MSG_CODE_NOT_FOUND = "Mã giới thiệu không tồn tại"
MSG_CODE_INACTIVE = "Mã giới thiệu không còn hoạt động"
MSG_CODE_EXPIRED = "Mã giới thiệu đã hết hạn"
MSG_CODE_EXHAUSTED = "Mã giới thiệu đã hết lượt sử dụng"


class ReferralService:
    """
    Service class cho Referral operations
    
    Cung cấp business logic cho:
    - Referral code management
    - Registration tracking
    - Commission calculation
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo ReferralService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== Referral Code Management ===============
    
    def generate_code(self, length: int = 8) -> str:
        """Generate unique referral code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = ''.join(secrets.choice(chars) for _ in range(length))
            # Check if code exists
            existing = self.db.query(ReferralCode).filter(
                ReferralCode.code == code
            ).first()
            if not existing:
                return code
    
    def generate_token(self) -> str:
        """Generate unique referral token for URL"""
        return secrets.token_urlsafe(32)
    
    def create_referral_code(
        self,
        staff_id: int,
        max_uses: Optional[int] = None,
        expires_days: Optional[int] = None,
        commission_rate: int = 10
    ) -> ReferralCode:
        """
        Tạo referral code mới cho staff
        
        Args:
            staff_id: Staff user ID
            max_uses: Số lần sử dụng tối đa (None = unlimited)
            expires_days: Số ngày trước khi hết hạn (None = không hết hạn)
            commission_rate: Tỷ lệ hoa hồng (%)
            
        Returns:
            ReferralCode mới
        """
        code = self.generate_code()
        token = self.generate_token()
        
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        referral_code = ReferralCode(
            staff_id=staff_id,
            code=code,
            token=token,
            status="active",
            max_uses=max_uses,
            expires_at=expires_at,
            commission_rate=commission_rate,
            created_by=staff_id
        )
        
        self.db.add(referral_code)
        self.db.commit()
        self.db.refresh(referral_code)
        
        logger.info(f"Referral code created: {code} for staff {staff_id}")
        return referral_code
    
    def get_staff_codes(self, staff_id: int) -> List[ReferralCode]:
        """Lấy tất cả referral codes của staff"""
        return self.db.query(ReferralCode).filter(
            ReferralCode.staff_id == staff_id
        ).order_by(desc(ReferralCode.created_at)).all()
    
    def get_code_by_code(self, code: str) -> Optional[ReferralCode]:
        """Lấy referral code theo code string"""
        return self.db.query(ReferralCode).filter(
            ReferralCode.code == code
        ).first()
    
    def get_code_by_token(self, token: str) -> Optional[ReferralCode]:
        """Lấy referral code theo token"""
        return self.db.query(ReferralCode).filter(
            ReferralCode.token == token
        ).first()
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate referral code
        
        Args:
            code: Referral code
            
        Returns:
            Dict với validation result
        """
        referral_code = self.get_code_by_code(code)
        
        if not referral_code:
            return {"valid": False, "error": MSG_CODE_NOT_FOUND}
        
        if referral_code.status != "active":
            return {"valid": False, "error": MSG_CODE_INACTIVE}
        
        if referral_code.expires_at and referral_code.expires_at < datetime.utcnow():
            return {"valid": False, "error": MSG_CODE_EXPIRED}
        
        if referral_code.max_uses and referral_code.used_count >= referral_code.max_uses:
            return {"valid": False, "error": MSG_CODE_EXHAUSTED}
        
        return {
            "valid": True,
            "code_id": referral_code.id,
            "staff_id": referral_code.staff_id
        }
    
    def deactivate_code(self, code_id: int, staff_id: int) -> Optional[ReferralCode]:
        """
        Deactivate referral code
        
        Args:
            code_id: Referral code ID
            staff_id: Staff ID (để verify ownership)
            
        Returns:
            ReferralCode đã cập nhật
        """
        referral_code = self.db.query(ReferralCode).filter(
            and_(
                ReferralCode.id == code_id,
                ReferralCode.staff_id == staff_id
            )
        ).first()
        
        if not referral_code:
            return None
        
        referral_code.status = "inactive"
        self.db.commit()
        self.db.refresh(referral_code)
        
        logger.info(f"Referral code {code_id} deactivated")
        return referral_code
    
    # =============== Registration Tracking ===============
    
    def register_referral(
        self,
        referral_code_id: int,
        user_id: int,
        source_type: str = "code",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ReferralRegistration:
        """
        Ghi nhận đăng ký qua referral
        
        Args:
            referral_code_id: Referral code ID
            user_id: User ID mới đăng ký
            source_type: Loại nguồn (code, link)
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            ReferralRegistration mới
        """
        registration = ReferralRegistration(
            referral_code_id=referral_code_id,
            referred_user_id=user_id,
            source_type=source_type,
            ip_address=ip_address,
            user_agent=user_agent,
            status="pending"
        )
        
        self.db.add(registration)
        
        # Update used_count
        referral_code = self.db.query(ReferralCode).filter(
            ReferralCode.id == referral_code_id
        ).first()
        if referral_code:
            referral_code.used_count = (referral_code.used_count or 0) + 1
        
        self.db.commit()
        self.db.refresh(registration)
        
        logger.info(f"Referral registration created: {registration.id}")
        return registration
    
    def get_code_registrations(self, code_id: int) -> List[ReferralRegistration]:
        """Lấy tất cả registrations của một code"""
        return self.db.query(ReferralRegistration).filter(
            ReferralRegistration.referral_code_id == code_id
        ).order_by(desc(ReferralRegistration.created_at)).all()
    
    def get_staff_registrations(self, staff_id: int) -> List[ReferralRegistration]:
        """Lấy tất cả registrations của staff"""
        codes = self.get_staff_codes(staff_id)
        code_ids = [c.id for c in codes]
        
        return self.db.query(ReferralRegistration).filter(
            ReferralRegistration.referral_code_id.in_(code_ids)
        ).order_by(desc(ReferralRegistration.created_at)).all()
    
    def verify_registration(
        self,
        registration_id: int
    ) -> Optional[ReferralRegistration]:
        """
        Xác minh registration (khi user hoàn thành KYC)
        
        Args:
            registration_id: Registration ID
            
        Returns:
            ReferralRegistration đã cập nhật
        """
        registration = self.db.query(ReferralRegistration).filter(
            ReferralRegistration.id == registration_id
        ).first()
        
        if not registration:
            return None
        
        registration.status = "verified"
        registration.verified_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(registration)
        
        logger.info(f"Referral registration {registration_id} verified")
        return registration
    
    # =============== Commission Tracking ===============
    
    def mark_commission_paid(
        self,
        registration_id: int,
        amount: int
    ) -> Optional[ReferralRegistration]:
        """
        Đánh dấu hoa hồng đã trả
        
        Args:
            registration_id: Registration ID
            amount: Số tiền hoa hồng
            
        Returns:
            ReferralRegistration đã cập nhật
        """
        registration = self.db.query(ReferralRegistration).filter(
            ReferralRegistration.id == registration_id
        ).first()
        
        if not registration:
            return None
        
        registration.commission_paid = True
        registration.commission_amount = amount
        registration.commission_paid_at = datetime.utcnow()
        registration.status = "rewarded"
        
        self.db.commit()
        self.db.refresh(registration)
        
        logger.info(f"Commission paid for registration {registration_id}: {amount}")
        return registration
    
    # =============== Statistics ===============
    
    def get_staff_stats(self, staff_id: int) -> Dict[str, Any]:
        """
        Lấy thống kê referral của staff
        
        Args:
            staff_id: Staff user ID
            
        Returns:
            Dict với thống kê
        """
        codes = self.get_staff_codes(staff_id)
        registrations = self.get_staff_registrations(staff_id)
        
        total_codes = len(codes)
        active_codes = len([c for c in codes if c.status == "active"])
        total_registrations = len(registrations)
        verified_registrations = len([r for r in registrations if r.status == "verified"])
        total_commission = sum(r.commission_amount or 0 for r in registrations if r.commission_paid)
        
        return {
            "staff_id": staff_id,
            "total_codes": total_codes,
            "active_codes": active_codes,
            "total_registrations": total_registrations,
            "verified_registrations": verified_registrations,
            "pending_registrations": total_registrations - verified_registrations,
            "total_commission_earned": total_commission,
            "timestamp": datetime.utcnow().isoformat()
        }
