# Compliance Module Schemas
# Author: MiniMax Agent
# Date: 2025-12-05
# Purpose: Pydantic models for compliance module API requests/responses

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Enums for compliance module
class ComplianceStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class AMLScreeningStatus(str, Enum):
    CLEAN = "clean"
    FLAGGED = "flagged"
    INVESTIGATING = "investigating"
    REPORTED = "reported"

class AMLRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MonitoringType(str, Enum):
    REAL_TIME = "real_time"
    ENHANCED = "enhanced"
    PERIODIC = "periodic"

class RuleCategory(str, Enum):
    AML = "aml"
    KYC = "kyc"
    TRANSACTION_MONITORING = "transaction_monitoring"
    SANCTIONS = "sanctions"
    MARKET_ABUSE = "market_abuse"

class RuleOperator(str, Enum):
    EQUALS = "equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    REGEX = "regex"
    IN_RANGE = "in_range"

class RuleActionType(str, Enum):
    ALERT = "alert"
    FLAG = "flag"
    BLOCK = "block"
    REPORT = "report"
    FREEZE_ACCOUNT = "freeze_account"

class ReportType(str, Enum):
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    LARGE_TRANSACTION = "large_transaction"
    KYC_DATA = "kyc_data"
    COMPLIANCE_SUMMARY = "compliance_summary"
    RISK_ASSESSMENT = "risk_assessment"

class ReportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class ScreeningStatus(str, Enum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    CLEARED = "cleared"
    FLAGGED = "flagged"
    ESCALATED = "escalated"

# KYC Schemas
class PersonalInfo(BaseModel):
    firstName: str = Field(..., min_length=1, description="Họ")
    lastName: str = Field(..., min_length=1, description="Tên")
    dateOfBirth: str = Field(..., description="Ngày sinh (YYYY-MM-DD)")
    placeOfBirth: str = Field(..., description="Nơi sinh")
    nationality: str = Field(..., min_length=2, max_length=2, description="Quốc tịch (2 ký tự)")
    phoneNumber: str = Field(..., description="Số điện thoại")
    email: str = Field(..., description="Email")

class AddressInfo(BaseModel):
    street: str = Field(..., description="Địa chỉ đường")
    city: str = Field(..., description="Thành phố")
    state: str = Field(..., description="Tỉnh/Thành")
    postalCode: str = Field(..., description="Mã bưu điện")
    country: str = Field(..., min_length=2, max_length=2, description="Quốc gia (2 ký tự)")

class IdentityDocument(BaseModel):
    id: str
    type: str = Field(..., description="Loại giấy tờ")
    documentNumber: str = Field(..., description="Số giấy tờ")
    issueDate: str = Field(..., description="Ngày cấp")
    expiryDate: str = Field(..., description="Ngày hết hạn")
    issuingAuthority: str = Field(..., description="Cơ quan cấp")
    fileUrl: str = Field(..., description="URL file")
    fileHash: str = Field(..., description="Hash của file")
    status: str = Field(..., description="Trạng thái")
    verifiedAt: Optional[str] = None
    rejectionReason: Optional[str] = None

class VerificationHistory(BaseModel):
    id: str
    action: str
    performedBy: str
    reason: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str

class KYCProfile(BaseModel):
    id: str
    userId: str
    status: ComplianceStatus
    verificationLevel: str = Field(default="basic")
    personalInfo: Optional[PersonalInfo] = None
    addressInfo: Optional[AddressInfo] = None
    identityDocuments: List[IdentityDocument] = Field(default_factory=list)
    verificationHistory: List[VerificationHistory] = Field(default_factory=list)
    createdAt: str
    updatedAt: str
    expiresAt: Optional[str] = None

class KYCSubmitRequest(BaseModel):
    personalInfo: PersonalInfo
    addressInfo: AddressInfo
    documents: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class KYCUpdateRequest(BaseModel):
    targetUserId: str
    status: ComplianceStatus
    verificationLevel: Optional[str] = None
    reviewNotes: Optional[str] = None

# AML Schemas
class AMLFinding(BaseModel):
    category: str = Field(..., description="Loại phát hiện")
    source: str = Field(..., description="Nguồn phát hiện")
    description: str = Field(..., description="Mô tả")
    severity: Severity
    confidence: int = Field(..., ge=0, le=100, description="Độ tin cậy (0-100)")
    actionTaken: str = Field(..., description="Hành động đã thực hiện")
    timestamp: str

class AMLScreening(BaseModel):
    id: str
    userId: str
    screeningType: str = Field(..., description="Loại sàng lọc")
    status: AMLScreeningStatus
    riskLevel: AMLRiskLevel
    findings: List[AMLFinding] = Field(default_factory=list)
    lastChecked: str
    nextReview: str
    reportedAt: Optional[str] = None
    reportReference: Optional[str] = None

class AMLScreeningRequest(BaseModel):
    screeningType: str = Field(default="initial")
    personalInfo: Optional[Dict[str, Any]] = None
    transactionData: Optional[Dict[str, Any]] = None
    enhancedDueDiligence: bool = Field(default=False)

class AMLMonitoringRequest(BaseModel):
    transactionId: str
    amount: float = Field(..., gt=0)
    frequency: Optional[int] = Field(default=0, ge=0)
    originCountry: Optional[str] = Field(default="US")
    destinationCountry: Optional[str] = Field(default="US")
    structuringPattern: Optional[bool] = Field(default=False)

class AMLUpdateRequest(BaseModel):
    targetUserId: str
    status: AMLScreeningStatus
    riskLevel: Optional[AMLRiskLevel] = None
    additionalFindings: Optional[List[AMLFinding]] = None

# Monitoring Schemas
class MonitoringFlag(BaseModel):
    id: str
    flagType: str = Field(..., description="Loại cờ")
    severity: Severity
    description: str = Field(..., description="Mô tả")
    rule: str = Field(..., description="Luật áp dụng")
    threshold: Optional[float] = None
    actualValue: Optional[Union[float, str]] = None
    confidence: int = Field(..., ge=0, le=100)

class TransactionMonitoring(BaseModel):
    id: str
    transactionId: str
    userId: str
    monitoringType: MonitoringType
    status: str
    riskScore: int = Field(..., ge=0, le=100)
    flags: List[MonitoringFlag] = Field(default_factory=list)
    reviewed: bool = Field(default=False)
    reviewedBy: Optional[str] = None
    reviewedAt: Optional[str] = None
    createdAt: str

class SuspiciousActivity(BaseModel):
    id: str
    userId: str
    activityType: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    riskLevel: Severity
    status: str
    reportedBy: str
    reportedAt: str
    investigationNotes: Optional[str] = None
    assignedTo: Optional[str] = None

# Compliance Rules Engine Schemas
class RuleCondition(BaseModel):
    field: str = Field(..., description="Trường dữ liệu")
    operator: RuleOperator
    value: Union[str, float, int, List[Union[str, float, int]]]
    threshold: Optional[float] = None

class RuleAction(BaseModel):
    type: RuleActionType
    severity: str = Field(default="warning")
    message: str = Field(..., description="Thông điệp")
    autoExecute: bool = Field(default=False)

class ComplianceRule(BaseModel):
    id: str
    name: str
    description: str
    category: RuleCategory
    severity: Severity
    isActive: bool
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    triggerCount: int = Field(default=0)
    lastTriggered: Optional[str] = None
    createdAt: str
    updatedAt: str

class ComplianceRuleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: RuleCategory
    severity: Severity
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    isActive: bool = Field(default=True)

class ComplianceRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RuleCategory] = None
    severity: Optional[Severity] = None
    conditions: Optional[List[RuleCondition]] = None
    actions: Optional[List[RuleAction]] = None
    isActive: Optional[bool] = None

class RuleEvaluationRequest(BaseModel):
    triggerData: Dict[str, Any]

class RuleExecutionResult(BaseModel):
    id: str
    ruleId: str
    timestamp: str
    triggerData: Dict[str, Any]
    conditionsMet: List[bool]
    actionsExecuted: List[Dict[str, Any]]
    executionTime: int
    result: str

# Regulatory Reports Schemas
class SARReport(BaseModel):
    id: str
    reportType: str = Field(default="suspicious_activity")
    jurisdiction: str = Field(default="US")
    status: ReportStatus
    data: Dict[str, Any]
    submittedBy: str
    dueDate: str
    sarNumber: Optional[str] = None
    suspiciousActivity: Optional[Dict[str, Any]] = None
    narrative: Optional[str] = None
    recommendedAction: Optional[str] = None
    createdAt: Optional[str] = None
    submittedAt: Optional[str] = None
    referenceNumber: Optional[str] = None
    rejectionReason: Optional[str] = None

class CTRReport(BaseModel):
    id: str
    reportType: str = Field(default="large_transaction")
    jurisdiction: str = Field(default="US")
    status: ReportStatus
    data: Dict[str, Any]
    submittedBy: str
    dueDate: str
    transactionDetails: Optional[Dict[str, Any]] = None
    customerDetails: Optional[Dict[str, Any]] = None
    createdAt: Optional[str] = None
    submittedAt: Optional[str] = None
    referenceNumber: Optional[str] = None
    rejectionReason: Optional[str] = None

RegulatoryReport = Union[SARReport, CTRReport]

class RegulatoryReportCreate(BaseModel):
    reportType: ReportType
    data: Optional[Dict[str, Any]] = None
    jurisdiction: str = Field(default="US")

class RegulatoryReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    referenceNumber: Optional[str] = None
    rejectionReason: Optional[str] = None
    notes: Optional[str] = None

class AutoGenerateRequest(BaseModel):
    # Body có thể để trống vì auto-generate không cần tham số
    pass

# Sanctions Screening Schemas
class SanctionsEntry(BaseModel):
    id: str
    name: str
    aliases: Optional[List[str]] = None
    dateOfBirth: Optional[str] = None
    nationality: Optional[str] = None
    country: Optional[str] = None
    program: str
    listType: str
    entityType: str
    lastUpdated: str
    riskLevel: Severity
    address: Optional[str] = None
    identification: Optional[str] = None
    remarks: Optional[str] = None

class PEPEntry(BaseModel):
    id: str
    name: str
    aliases: Optional[List[str]] = None
    position: str
    organization: str
    country: str
    region: str
    pepType: str
    riskLevel: Severity
    lastUpdated: str
    source: str
    verificationStatus: str
    familyMembers: Optional[List[str]] = None
    closeAssociates: Optional[List[str]] = None

class WatchlistEntry(BaseModel):
    id: str
    name: str
    listType: str
    jurisdiction: str
    severity: Severity
    description: str
    lastUpdated: str

class FuzzyMatch(BaseModel):
    entry: Dict[str, Any]
    score: int = Field(..., ge=0, le=100)

class SanctionsSearchResult(BaseModel):
    exactMatches: List[SanctionsEntry]
    fuzzyMatches: List[FuzzyMatch]
    searchQuery: str
    totalMatches: int

class ScreeningResult(BaseModel):
    id: str
    timestamp: str
    queryName: str
    queryType: str
    results: Dict[str, Any]
    overallRisk: str
    requiresReview: bool
    reviewerNotes: Optional[str] = None
    reviewedBy: Optional[str] = None
    reviewedAt: Optional[str] = None
    status: str
    findings: Optional[List[AMLFinding]] = None

class SanctionsScreeningRequest(BaseModel):
    name: str = Field(..., min_length=1)
    aliases: Optional[List[str]] = Field(default_factory=list)
    dateOfBirth: Optional[str] = None
    nationality: Optional[str] = None
    country: Optional[str] = None
    queryType: str = Field(default="individual")

class SanctionsUpdateRequest(BaseModel):
    status: Optional[ScreeningStatus] = None
    reviewerNotes: Optional[str] = None

# Dashboard and Audit Schemas
class ComplianceMetrics(BaseModel):
    totalReports: int
    reportsByType: Dict[str, int]
    reportsByStatus: Dict[str, int]
    averageProcessingTime: float
    complianceScore: float
    riskMetrics: Dict[str, Any]
    auditFindings: List[Any]
    calculatedAt: str

class ComplianceAlert(BaseModel):
    id: str
    userId: str
    alertType: str
    severity: Severity
    title: str
    description: str
    actionRequired: bool
    status: str
    assignedTo: Optional[str] = None
    createdAt: str
    resolvedAt: Optional[str] = None
    notes: Optional[str] = None

class RiskAlert(BaseModel):
    id: str
    alertType: str
    severity: Severity
    title: str
    description: str
    riskLevel: str
    isRead: bool = Field(default=False)
    isResolved: bool = Field(default=False)
    createdAt: str
    resolvedAt: Optional[str] = None

class RiskLimit(BaseModel):
    id: str
    userId: str
    limitType: str
    limitValue: float
    currentValue: float
    status: str
    createdAt: str

class ComplianceDashboardResponse(BaseModel):
    overview: Dict[str, Any]
    risks: Dict[str, Any]
    alerts: Dict[str, Any]
    reports: Dict[str, Any]

class DashboardAlertRequest(BaseModel):
    alertType: str
    severity: Severity
    title: str
    description: str
    targetUserId: Optional[str] = None

class DashboardMetricsRequest(BaseModel):
    period: str = Field(default="30d")
    reportType: Optional[str] = None

class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    userId: str
    userRole: Optional[str] = None
    action: str
    resource: str
    resourceId: Optional[str] = None
    details: Dict[str, Any]
    ipAddress: str
    userAgent: str
    sessionId: Optional[str] = None
    result: str
    severity: Severity
    category: str
    previousValue: Optional[Any] = None
    newValue: Optional[Any] = None
    riskScore: Optional[int] = None

class SecurityEvent(BaseModel):
    id: str
    timestamp: str
    eventType: str
    userId: Optional[str] = None
    ipAddress: str
    severity: Severity
    description: str
    details: Dict[str, Any]
    mitigated: bool = Field(default=False)
    mitigationActions: Optional[List[str]] = None
    resolvedAt: Optional[str] = None

class ComplianceEvent(BaseModel):
    id: str
    timestamp: str
    eventType: str
    userId: Optional[str] = None
    adminId: Optional[str] = None
    details: Dict[str, Any]
    jurisdiction: Optional[str] = None
    regulatoryImpact: str
    requiresAction: bool
    actionCompleted: bool = Field(default=False)
    completedAt: Optional[str] = None

class AuditLogCreate(BaseModel):
    action: str
    resource: str
    details: Dict[str, Any]
    severity: Severity = Field(default=Severity.MEDIUM)
    category: str = Field(default="system")
    previousValue: Optional[Any] = None
    newValue: Optional[Any] = None
    resourceId: Optional[str] = None

class SecurityEventCreate(BaseModel):
    eventType: str
    details: Dict[str, Any]
    severity: Severity = Field(default=Severity.MEDIUM)
    targetUserId: Optional[str] = None

class ComplianceEventCreate(BaseModel):
    eventType: str
    details: Dict[str, Any]
    jurisdiction: str = Field(default="US")
    regulatoryImpact: str = Field(default="medium")
    targetUserId: Optional[str] = None

class SecurityEventUpdate(BaseModel):
    mitigated: Optional[bool] = None
    mitigationActions: Optional[List[str]] = None
    notes: Optional[str] = None