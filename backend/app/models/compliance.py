"""
Compliance Models
Digital Utopia Platform

Models cho KYC, AML, Compliance Events, và Risk Assessment
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    ForeignKey, DECIMAL, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from datetime import datetime

from .base import Base, TimestampMixin


class KYCDocument(Base, TimestampMixin):
    """
    Bảng kyc_documents - Tài liệu KYC
    
    Lưu trữ tài liệu xác minh danh tính người dùng
    """
    __tablename__ = "kyc_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Document info
    document_type = Column(String(50), nullable=False)  # id_card, passport, driver_license, bank_statement
    document_number = Column(String(100), nullable=True)
    document_file_url = Column(String(500), nullable=True)
    file_hash = Column(String(255), nullable=True)
    
    # Dates
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    issuing_authority = Column(String(255), nullable=True)
    issuing_country = Column(String(100), nullable=True)
    
    # Verification
    verification_status = Column(String(50), default="pending", index=True)  # pending, verified, rejected, expired
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # AI verification results
    ai_verification_score = Column(DECIMAL(5, 2), nullable=True)
    ai_verification_details = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="kyc_documents", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<KYCDocument(user_id={self.user_id}, type={self.document_type}, status={self.verification_status})>"


class ComplianceEvent(Base, TimestampMixin):
    """
    Bảng compliance_events - Sự kiện tuân thủ
    
    Theo dõi các sự kiện liên quan đến compliance và risk
    """
    __tablename__ = "compliance_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), default="medium", index=True)  # low, medium, high, critical
    status = Column(String(50), default="open", index=True)  # open, investigating, resolved, dismissed
    
    # Description
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    
    # Risk scoring
    risk_score = Column(Integer, default=0)
    risk_factors = Column(JSONB, default=[])
    
    # Assignment
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolution_action = Column(String(100), nullable=True)
    
    # Evidence
    evidence = Column(JSONB, default={})
    
    # Related entities
    related_transaction_id = Column(Integer, nullable=True)
    related_order_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<ComplianceEvent(id={self.id}, type={self.event_type}, status={self.status})>"


class RiskAssessment(Base, TimestampMixin):
    """
    Bảng risk_assessments - Đánh giá rủi ro
    
    Lưu trữ kết quả đánh giá rủi ro cho người dùng
    """
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Assessment type
    assessment_type = Column(String(50), nullable=False)  # initial, periodic, triggered
    
    # Risk level
    risk_level = Column(String(20), nullable=False, index=True)  # low, medium, high, very_high, critical
    risk_score = Column(Integer, nullable=False)  # 0-100
    
    # Assessment details
    assessment_data = Column(JSONB, default={})
    factors_considered = Column(ARRAY(String), default=[])
    recommendations = Column(Text, nullable=True)
    
    # Assessor
    assessed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assessment_method = Column(String(50), default="automated")  # automated, manual, hybrid
    
    # Review
    next_review_date = Column(Date, nullable=True)
    status = Column(String(50), default="active", index=True)  # active, superseded, archived
    
    # Previous assessment reference
    previous_assessment_id = Column(Integer, ForeignKey("risk_assessments.id"), nullable=True)
    
    def __repr__(self):
        return f"<RiskAssessment(user_id={self.user_id}, level={self.risk_level}, score={self.risk_score})>"


class AMLScreening(Base, TimestampMixin):
    """
    Bảng aml_screenings - Sàng lọc AML
    
    Kết quả sàng lọc chống rửa tiền
    """
    __tablename__ = "aml_screenings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Screening type
    screening_type = Column(String(50), nullable=False)  # initial, periodic, transaction, enhanced_due_diligence
    
    # Results
    status = Column(String(50), default="clean", index=True)  # clean, flagged, investigating, reported
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    
    # Findings
    findings = Column(JSONB, default=[])
    sanctions_match = Column(Boolean, default=False)
    pep_match = Column(Boolean, default=False)
    adverse_media_match = Column(Boolean, default=False)
    watchlist_match = Column(Boolean, default=False)
    
    # Screening sources
    sources_checked = Column(ARRAY(String), default=[])
    
    # Review
    last_checked = Column(DateTime(timezone=True), default=datetime.utcnow)
    next_review = Column(DateTime(timezone=True), nullable=True)
    
    # Reviewer
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    
    # Related transaction if triggered
    trigger_transaction_id = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<AMLScreening(user_id={self.user_id}, status={self.status}, risk={self.risk_level})>"
