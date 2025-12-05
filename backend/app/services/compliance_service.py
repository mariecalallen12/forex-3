"""
Compliance Service
Digital Utopia Platform

Business logic cho Compliance operations (KYC, AML, Risk)
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
import logging

from ..models.compliance import KYCDocument, ComplianceEvent, RiskAssessment, AMLScreening
from ..models.user import User
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)

# =============== Constants ===============
REQUIRED_KYC_DOCUMENT_TYPES = ["id_card", "selfie"]
DEFAULT_AML_SOURCES = ["sanctions_list", "pep_list", "adverse_media"]
RISK_ASSESSMENT_REVIEW_DAYS = 90


class ComplianceService:
    """
    Service class cho Compliance operations
    
    Cung cấp business logic cho:
    - KYC verification
    - AML screening
    - Risk assessment
    - Compliance events
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo ComplianceService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== KYC Management ===============
    
    def create_kyc_document(
        self,
        user_id: int,
        document_type: str,
        document_number: Optional[str] = None,
        document_file_url: Optional[str] = None,
        expiry_date: Optional[datetime] = None
    ) -> KYCDocument:
        """
        Tạo KYC document mới
        
        Args:
            user_id: User ID
            document_type: Loại tài liệu (id_card, passport, etc.)
            document_number: Số tài liệu
            document_file_url: URL file tài liệu
            expiry_date: Ngày hết hạn
            
        Returns:
            KYCDocument mới
        """
        document = KYCDocument(
            user_id=user_id,
            document_type=document_type,
            document_number=document_number,
            document_file_url=document_file_url,
            expiry_date=expiry_date,
            verification_status="pending"
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"KYC document created: {document.id} for user {user_id}")
        return document
    
    def get_user_kyc_documents(self, user_id: int) -> List[KYCDocument]:
        """Lấy tất cả KYC documents của user"""
        return self.db.query(KYCDocument).filter(
            KYCDocument.user_id == user_id
        ).order_by(desc(KYCDocument.created_at)).all()
    
    def verify_kyc_document(
        self,
        document_id: int,
        verified_by: int,
        status: str = "verified",
        rejection_reason: Optional[str] = None
    ) -> Optional[KYCDocument]:
        """
        Xác minh KYC document
        
        Args:
            document_id: Document ID
            verified_by: User ID của người xác minh
            status: Trạng thái mới (verified/rejected)
            rejection_reason: Lý do từ chối (nếu rejected)
            
        Returns:
            KYCDocument đã cập nhật
        """
        document = self.db.query(KYCDocument).filter(
            KYCDocument.id == document_id
        ).first()
        
        if not document:
            return None
        
        document.verification_status = status
        document.verified_by = verified_by
        document.verification_date = datetime.utcnow()
        
        if status == "rejected" and rejection_reason:
            document.rejection_reason = rejection_reason
        
        self.db.commit()
        self.db.refresh(document)
        
        # Update user KYC status if all documents verified
        if status == "verified":
            self._update_user_kyc_status(document.user_id)
        
        logger.info(f"KYC document {document_id} verified as {status}")
        return document
    
    def _update_user_kyc_status(self, user_id: int):
        """Cập nhật KYC status của user dựa trên documents"""
        # Check if all required documents are verified
        documents = self.get_user_kyc_documents(user_id)
        
        verified_types = [d.document_type for d in documents if d.verification_status == "verified"]
        
        all_verified = all(t in verified_types for t in REQUIRED_KYC_DOCUMENT_TYPES)
        
        if all_verified:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.kyc_status = "verified"
                self.db.commit()
                logger.info(f"User {user_id} KYC status updated to verified")
    
    # =============== AML Screening ===============
    
    def create_aml_screening(
        self,
        user_id: int,
        screening_type: str = "initial"
    ) -> AMLScreening:
        """
        Tạo AML screening mới
        
        Args:
            user_id: User ID
            screening_type: Loại screening (initial, periodic, transaction)
            
        Returns:
            AMLScreening mới
        """
        screening = AMLScreening(
            user_id=user_id,
            screening_type=screening_type,
            status="clean",
            risk_level="low",
            sources_checked=DEFAULT_AML_SOURCES,
            last_checked=datetime.utcnow()
        )
        
        self.db.add(screening)
        self.db.commit()
        self.db.refresh(screening)
        
        logger.info(f"AML screening created: {screening.id} for user {user_id}")
        return screening
    
    def get_user_aml_screenings(self, user_id: int) -> List[AMLScreening]:
        """Lấy tất cả AML screenings của user"""
        return self.db.query(AMLScreening).filter(
            AMLScreening.user_id == user_id
        ).order_by(desc(AMLScreening.created_at)).all()
    
    def update_aml_status(
        self,
        screening_id: int,
        status: str,
        risk_level: str,
        findings: Optional[List[Dict]] = None,
        reviewer_notes: Optional[str] = None
    ) -> Optional[AMLScreening]:
        """
        Cập nhật kết quả AML screening
        
        Args:
            screening_id: Screening ID
            status: Trạng thái (clean, flagged, investigating, reported)
            risk_level: Mức rủi ro (low, medium, high, critical)
            findings: Các phát hiện
            reviewer_notes: Ghi chú của reviewer
            
        Returns:
            AMLScreening đã cập nhật
        """
        screening = self.db.query(AMLScreening).filter(
            AMLScreening.id == screening_id
        ).first()
        
        if not screening:
            return None
        
        screening.status = status
        screening.risk_level = risk_level
        screening.reviewed_at = datetime.utcnow()
        
        if findings:
            screening.findings = findings
        if reviewer_notes:
            screening.reviewer_notes = reviewer_notes
        
        self.db.commit()
        self.db.refresh(screening)
        
        logger.info(f"AML screening {screening_id} updated to {status}")
        return screening
    
    # =============== Risk Assessment ===============
    
    def create_risk_assessment(
        self,
        user_id: int,
        assessment_type: str = "initial",
        assessed_by: Optional[int] = None
    ) -> RiskAssessment:
        """
        Tạo risk assessment mới
        
        Args:
            user_id: User ID
            assessment_type: Loại assessment (initial, periodic, triggered)
            assessed_by: User ID của người đánh giá
            
        Returns:
            RiskAssessment mới
        """
        # Calculate risk score
        risk_data = self._calculate_risk_score(user_id)
        
        assessment = RiskAssessment(
            user_id=user_id,
            assessment_type=assessment_type,
            risk_level=risk_data["level"],
            risk_score=risk_data["score"],
            assessment_data=risk_data["data"],
            factors_considered=risk_data["factors"],
            recommendations=risk_data["recommendations"],
            assessed_by=assessed_by,
            assessment_method="automated" if not assessed_by else "manual",
            next_review_date=datetime.utcnow().date() + timedelta(days=RISK_ASSESSMENT_REVIEW_DAYS)
        )
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        logger.info(f"Risk assessment created: {assessment.id} for user {user_id}")
        return assessment
    
    def _calculate_risk_score(self, user_id: int) -> Dict[str, Any]:
        """Tính toán risk score cho user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        score = 0
        factors = []
        
        # KYC status
        if user and user.kyc_status == "verified":
            score += 10
            factors.append("KYC verified")
        else:
            score += 30
            factors.append("KYC not verified")
        
        # Email verification
        if user and user.email_verified:
            score += 5
            factors.append("Email verified")
        else:
            score += 15
            factors.append("Email not verified")
        
        # Phone verification
        if user and user.phone_verified:
            score += 5
            factors.append("Phone verified")
        else:
            score += 10
            factors.append("Phone not verified")
        
        # Determine risk level
        if score <= 20:
            level = "low"
            recommendations = "Continue monitoring với standard procedures"
        elif score <= 40:
            level = "medium"
            recommendations = "Enhanced monitoring recommended"
        elif score <= 60:
            level = "high"
            recommendations = "Manual review required"
        else:
            level = "critical"
            recommendations = "Immediate action required"
        
        return {
            "score": score,
            "level": level,
            "factors": factors,
            "recommendations": recommendations,
            "data": {
                "kyc_status": user.kyc_status if user else "unknown",
                "email_verified": user.email_verified if user else False,
                "phone_verified": user.phone_verified if user else False,
                "calculation_date": datetime.utcnow().isoformat()
            }
        }
    
    def get_user_risk_assessments(self, user_id: int) -> List[RiskAssessment]:
        """Lấy tất cả risk assessments của user"""
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.user_id == user_id
        ).order_by(desc(RiskAssessment.created_at)).all()
    
    # =============== Compliance Events ===============
    
    def create_compliance_event(
        self,
        user_id: Optional[int],
        event_type: str,
        description: str,
        severity: str = "medium",
        related_transaction_id: Optional[int] = None
    ) -> ComplianceEvent:
        """
        Tạo compliance event mới
        
        Args:
            user_id: User ID (có thể None cho system events)
            event_type: Loại sự kiện
            description: Mô tả
            severity: Mức độ (low, medium, high, critical)
            related_transaction_id: Transaction ID liên quan
            
        Returns:
            ComplianceEvent mới
        """
        event = ComplianceEvent(
            user_id=user_id,
            event_type=event_type,
            description=description,
            severity=severity,
            status="open",
            related_transaction_id=related_transaction_id
        )
        
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(f"Compliance event created: {event.id} type={event_type}")
        return event
    
    def get_open_events(
        self,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[ComplianceEvent]:
        """Lấy danh sách compliance events đang mở"""
        query = self.db.query(ComplianceEvent).filter(
            ComplianceEvent.status == "open"
        )
        
        if severity:
            query = query.filter(ComplianceEvent.severity == severity)
        
        return query.order_by(desc(ComplianceEvent.created_at)).limit(limit).all()
    
    def resolve_event(
        self,
        event_id: int,
        resolved_by: int,
        resolution_notes: str,
        resolution_action: str
    ) -> Optional[ComplianceEvent]:
        """
        Giải quyết compliance event
        
        Args:
            event_id: Event ID
            resolved_by: User ID của người giải quyết
            resolution_notes: Ghi chú giải quyết
            resolution_action: Hành động đã thực hiện
            
        Returns:
            ComplianceEvent đã cập nhật
        """
        event = self.db.query(ComplianceEvent).filter(
            ComplianceEvent.id == event_id
        ).first()
        
        if not event:
            return None
        
        event.status = "resolved"
        event.resolved_by = resolved_by
        event.resolved_at = datetime.utcnow()
        event.resolution_notes = resolution_notes
        event.resolution_action = resolution_action
        
        self.db.commit()
        self.db.refresh(event)
        
        logger.info(f"Compliance event {event_id} resolved")
        return event
    
    # =============== Dashboard Stats ===============
    
    def get_compliance_stats(self) -> Dict[str, Any]:
        """Lấy thống kê compliance"""
        open_events = self.db.query(ComplianceEvent).filter(
            ComplianceEvent.status == "open"
        ).count()
        
        pending_kyc = self.db.query(KYCDocument).filter(
            KYCDocument.verification_status == "pending"
        ).count()
        
        flagged_aml = self.db.query(AMLScreening).filter(
            AMLScreening.status == "flagged"
        ).count()
        
        high_risk_users = self.db.query(RiskAssessment).filter(
            and_(
                RiskAssessment.risk_level.in_(["high", "critical"]),
                RiskAssessment.status == "active"
            )
        ).count()
        
        return {
            "open_events": open_events,
            "pending_kyc": pending_kyc,
            "flagged_aml": flagged_aml,
            "high_risk_users": high_risk_users,
            "timestamp": datetime.utcnow().isoformat()
        }
