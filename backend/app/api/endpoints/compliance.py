# Compliance Module API Endpoints
# Author: MiniMax Agent
# Date: 2025-12-05
# Purpose: FastAPI endpoints for compliance module

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import string
import uuid

# Import schemas và dependencies
from app.schemas.compliance import (
    # KYC Schemas
    KYCProfile, KYCSubmitRequest, KYCUpdateRequest,
    PersonalInfo, AddressInfo, IdentityDocument, VerificationHistory,
    
    # AML Schemas
    AMLScreening, AMLScreeningRequest, AMLMonitoringRequest, AMLUpdateRequest, AMLFinding,
    
    # Monitoring Schemas
    TransactionMonitoring, SuspiciousActivity, MonitoringFlag,
    
    # Rules Engine Schemas
    ComplianceRule, ComplianceRuleCreate, ComplianceRuleUpdate, RuleEvaluationRequest, RuleExecutionResult,
    
    # Reports Schemas
    RegulatoryReport, RegulatoryReportCreate, RegulatoryReportUpdate, AutoGenerateRequest,
    
    # Sanctions Schemas
    SanctionsEntry, SanctionsSearchResult, SanctionsScreeningRequest, ScreeningResult,
    PEPEntry, WatchlistEntry, FuzzyMatch, SanctionsUpdateRequest,
    
    # Dashboard & Audit Schemas
    ComplianceMetrics, ComplianceDashboardResponse, DashboardAlertRequest, DashboardMetricsRequest,
    AuditLogEntry, SecurityEvent, ComplianceEvent, AuditLogCreate, SecurityEventCreate,
    ComplianceEventCreate, SecurityEventUpdate, ComplianceAlert, RiskAlert, RiskLimit,
    
    # Enums
    ComplianceStatus, AMLScreeningStatus, AMLRiskLevel, Severity, MonitoringType,
    RuleCategory, RuleOperator, RuleActionType, ReportType, ReportStatus, ScreeningStatus
)

# Import dependencies
from app.middleware.auth import get_current_user

router = APIRouter()

# In-memory storage (in production, use database)
# KYC Data
kyc_profiles: List[KYCProfile] = []
kyc_documents: List[IdentityDocument] = []
kyc_verification_history: List[VerificationHistory] = []

# AML Data
aml_screenings: List[AMLScreening] = []
transaction_monitorings: List[TransactionMonitoring] = []
suspicious_activities: List[SuspiciousActivity] = []

# Compliance Rules
compliance_rules: List[ComplianceRule] = []
rule_execution_results: List[RuleExecutionResult] = []

# Reports
regulatory_reports: List[RegulatoryReport] = []

# Sanctions
sanctions_lists: List[SanctionsEntry] = []
pep_database: List[PEPEntry] = []
watchlists: List[WatchlistEntry] = []
screening_results: List[ScreeningResult] = []

# Dashboard
risk_alerts: List[RiskAlert] = []
compliance_alerts: List[ComplianceAlert] = []
risk_limits: List[RiskLimit] = []

# Audit
audit_logs: List[AuditLogEntry] = []
security_events: List[SecurityEvent] = []
compliance_events: List[ComplianceEvent] = []

# Helper functions
def generate_id() -> str:
    """Generate unique ID"""
    return f"{datetime.now().timestamp()}-{''.join(random.choices(string.ascii_letters + string.digits, k=9))}"

def initialize_default_data():
    """Initialize with default data"""
    # Initialize sanctions lists
    global sanctions_lists, pep_database, watchlists
    
    sanctions_lists = [
        SanctionsEntry(
            id="san-001",
            name="John Smith",
            aliases=["J. Smith", "Johnny Smith"],
            nationality="US",
            country="US",
            program="OFAC SDN",
            listType="sanctions",
            entityType="individual",
            lastUpdated="2025-01-15T00:00:00Z",
            riskLevel="critical",
            remarks="Specially Designated National"
        ),
        SanctionsEntry(
            id="san-002",
            name="ABC Corporation",
            aliases=["ABC Corp", "American Business Co"],
            country="RU",
            program="OFAC SDN",
            listType="sanctions",
            entityType="entity",
            lastUpdated="2025-01-10T00:00:00Z",
            riskLevel="high",
            remarks="Owned by sanctioned entity"
        )
    ]
    
    pep_database = [
        PEPEntry(
            id="pep-001",
            name="Minister John Government",
            position="Minister of Finance",
            organization="Government of CountryX",
            country="CountryX",
            region="Asia",
            pepType="foreign",
            riskLevel="high",
            lastUpdated="2025-01-01T00:00:00Z",
            source="Government Database",
            verificationStatus="verified"
        )
    ]
    
    watchlists = [
        WatchlistEntry(
            id="watch-001",
            name="Fraudster Frank",
            listType="fraud",
            jurisdiction="US",
            severity="high",
            description="Wanted for securities fraud",
            lastUpdated="2025-01-12T00:00:00Z"
        )
    ]
    
    # Initialize default compliance rules
    compliance_rules = [
        ComplianceRule(
            id="rule-001",
            name="Large Transaction Detection",
            description="Flag transactions above $50,000 for enhanced monitoring",
            category="transaction_monitoring",
            severity="high",
            isActive=True,
            conditions=[],
            actions=[],
            triggerCount=0,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
    ]

# Initialize data on module load
initialize_default_data()

# ==================== AML ENDPOINTS ====================

@router.get("/aml", response_model=Dict[str, Any])
async def get_aml_screening():
    """Get AML screening status for authenticated user"""
    try:
        user_id = current_user["id"]
        
        # Find latest AML screening for user
        aml_screening = None
        for screening in aml_screenings:
            if screening.userId == user_id:
                if aml_screening is None or screening.lastChecked > aml_screening.lastChecked:
                    aml_screening = screening
        
        if not aml_screening:
            # Create initial AML screening
            aml_screening = AMLScreening(
                id=generate_id(),
                userId=user_id,
                screeningType="initial",
                status="clean",
                riskLevel="low",
                findings=[],
                lastChecked=datetime.now().isoformat(),
                nextReview=(datetime.now() + timedelta(days=30)).isoformat()
            )
            aml_screenings.append(aml_screening)
        
        return {
            "success": True,
            "data": aml_screening.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve AML screening: {str(e)}")

@router.post("/aml", response_model=Dict[str, Any])
async def perform_aml_screening(
    request: AMLScreeningRequest
):
    """Perform AML screening"""
    try:
        user_id = current_user["id"]
        
        if not request.personalInfo or not request.personalInfo.get("name"):
            raise HTTPException(status_code=400, detail="Personal information with name is required for AML screening")
        
        all_findings: List[AMLFinding] = []
        name = request.personalInfo["name"]
        
        # Simulate sanctions screening
        if any(name.lower() == entry.name.lower() for entry in sanctions_lists):
            all_findings.append(AMLFinding(
                category="sanctions",
                source="OFAC Sanctions List",
                description=f"Name match found in sanctions list: {name}",
                severity="high",
                confidence=85,
                actionTaken="Flagged for review",
                timestamp=datetime.now().isoformat()
            ))
        
        # Determine overall risk level and status
        risk_level = "low"
        status = "clean"
        
        high_severity_findings = [f for f in all_findings if f.severity in ["high", "critical"]]
        
        if high_severity_findings:
            risk_level = "high"
            status = "flagged"
        elif all_findings:
            risk_level = "medium"
            status = "flagged"
        
        # Create or update AML screening record
        aml_screening = next((s for s in aml_screenings if s.userId == user_id), None)
        
        if not aml_screening:
            aml_screening = AMLScreening(
                id=generate_id(),
                userId=user_id,
                screeningType=request.screeningType,
                status=status,
                riskLevel=risk_level,
                findings=all_findings,
                lastChecked=datetime.now().isoformat(),
                nextReview=(datetime.now() + timedelta(days=90 if risk_level == "low" else 30)).isoformat()
            )
            aml_screenings.append(aml_screening)
        else:
            aml_screening.screeningType = request.screeningType
            aml_screening.status = status
            aml_screening.riskLevel = risk_level
            aml_screening.findings = all_findings
            aml_screening.lastChecked = datetime.now().isoformat()
            aml_screening.nextReview = (datetime.now() + timedelta(days=90 if risk_level == "low" else 30)).isoformat()
        
        return {
            "success": True,
            "data": aml_screening.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform AML screening: {str(e)}")

@router.post("/aml/monitor", response_model=Dict[str, Any])
async def monitor_transaction_aml(
    request: AMLMonitoringRequest,
    current_user: dict = Depends(get_current_user)
):
    """Monitor transaction for AML compliance"""
    try:
        user_id = current_user["id"]
        
        # Assess transaction risk
        flags: List[MonitoringFlag] = []
        
        # Large amount flag
        if request.amount > 100000:
            flags.append(MonitoringFlag(
                id=generate_id(),
                flagType="large_amount",
                severity="high",
                description="Transaction amount exceeds $100,000 threshold",
                rule="LARGE_TRANSACTION_THRESHOLD",
                threshold=100000,
                actualValue=request.amount,
                confidence=95
            ))
        
        # High-risk jurisdiction
        high_risk_countries = ['IR', 'KP', 'SY', 'CU', 'RU']
        if request.originCountry in high_risk_countries or request.destinationCountry in high_risk_countries:
            flags.append(MonitoringFlag(
                id=generate_id(),
                flagType="high_risk_jurisdiction",
                severity="high",
                description=f"Transaction from high-risk jurisdiction: {request.originCountry}",
                rule="HIGH_RISK_JURISDICTION",
                actualValue=request.originCountry,
                confidence=100
            ))
        
        # Create monitoring record
        monitoring = TransactionMonitoring(
            id=generate_id(),
            transactionId=request.transactionId,
            userId=user_id,
            monitoringType="enhanced" if any(f.severity == "critical" for f in flags) else "real_time",
            status="flagged" if flags else "clean",
            riskScore=sum(25 if f.severity == "critical" else 15 if f.severity == "high" else 10 if f.severity == "medium" else 5 for f in flags),
            flags=flags,
            reviewed=False,
            createdAt=datetime.now().isoformat()
        )
        
        transaction_monitorings.append(monitoring)
        
        # Create suspicious activity if critical flags found
        critical_flags = [f for f in flags if f.severity == "critical"]
        if critical_flags:
            suspicious_activity = SuspiciousActivity(
                id=generate_id(),
                userId=user_id,
                activityType="money_laundering",
                description=f"Suspicious transaction patterns detected: {', '.join(f.flagType for f in critical_flags)}",
                evidence={"transactionId": request.transactionId, "flags": critical_flags},
                riskLevel="critical",
                status="reported",
                reportedBy="AML System",
                reportedAt=datetime.now().isoformat(),
                investigationNotes="Auto-generated suspicious activity report based on AML rules"
            )
            suspicious_activities.append(suspicious_activity)
            
            # Update screening status
            user_screening = next((s for s in aml_screenings if s.userId == user_id), None)
            if user_screening:
                user_screening.status = "reported"
                user_screening.riskLevel = "critical"
        
        return {
            "success": True,
            "data": monitoring.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to monitor transaction: {str(e)}")

@router.patch("/aml", response_model=Dict[str, Any])
async def update_aml_screening(
    request: AMLUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update AML screening (admin only)"""
    try:
        # Check admin privileges
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for AML status updates")
        
        aml_screening = next((s for s in aml_screenings if s.userId == request.targetUserId), None)
        
        if not aml_screening:
            raise HTTPException(status_code=404, detail="AML screening record not found")
        
        # Update screening
        aml_screening.status = request.status
        
        if request.riskLevel:
            if request.riskLevel in ["low", "medium", "high", "critical"]:
                aml_screening.riskLevel = request.riskLevel
        
        if request.additionalFindings:
            aml_screening.findings.extend(request.additionalFindings)
        
        aml_screening.lastChecked = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": aml_screening.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update AML screening: {str(e)}")

@router.get("/aml/metrics", response_model=Dict[str, Any])
async def get_aml_metrics(current_user: dict = Depends(get_current_user)):
    """Get compliance metrics (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for compliance metrics")
        
        # Calculate metrics
        total_screenings = len(aml_screenings)
        flagged_screenings = len([s for s in aml_screenings if s.status == "flagged"])
        reported_screenings = len([s for s in aml_screenings if s.status == "reported"])
        high_risk_screenings = len([s for s in aml_screenings if s.riskLevel in ["high", "critical"]])
        flagged_transactions = len([m for m in transaction_monitorings if m.status == "flagged"])
        suspicious_activity_count = len(suspicious_activities)
        
        # Calculate compliance score
        compliance_score = max(0, 100 - (flagged_screenings + reported_screenings) * 2 - high_risk_screenings * 5)
        
        metrics = ComplianceMetrics(
            totalReports=total_screenings,
            reportsByType={
                "initial": len([s for s in aml_screenings if s.screeningType == "initial"]),
                "periodic": len([s for s in aml_screenings if s.screeningType == "periodic"]),
                "transaction": len([s for s in aml_screenings if s.screeningType == "transaction"]),
                "enhanced_due_diligence": len([s for s in aml_screenings if s.screeningType == "enhanced_due_diligence"])
            },
            reportsByStatus={
                "clean": len([s for s in aml_screenings if s.status == "clean"]),
                "flagged": flagged_screenings,
                "investigating": len([s for s in aml_screenings if s.status == "investigating"]),
                "reported": reported_screenings
            },
            averageProcessingTime=2.5,
            complianceScore=compliance_score,
            riskMetrics={
                "highRiskUsers": high_risk_screenings,
                "flaggedTransactions": flagged_transactions,
                "suspiciousActivities": suspicious_activity_count,
                "kycCompletionRate": 95
            },
            auditFindings=[],
            calculatedAt=datetime.now().isoformat()
        )
        
        return {
            "success": True,
            "data": metrics.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve compliance metrics: {str(e)}")

# ==================== AUDIT & LOGGING ENDPOINTS ====================

@router.get("/audit", response_model=Dict[str, Any])
async def get_audit_logs(
    userId: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get audit logs"""
    try:
        user_id = current_user["id"]
        admin_role = getattr(current_user, 'admin_role', None)
        
        filtered_logs = audit_logs.copy()
        
        # Apply user permissions
        if admin_role not in ['compliance_officer', 'admin']:
            # Regular users can only see their own logs
            filtered_logs = [log for log in filtered_logs if log.userId == user_id]
        elif userId:
            # Admins can filter by specific user
            filtered_logs = [log for log in filtered_logs if log.userId == userId]
        
        # Apply filters
        if category:
            filtered_logs = [log for log in filtered_logs if log.category == category]
        
        if severity:
            filtered_logs = [log for log in filtered_logs if log.severity == severity]
        
        if result:
            filtered_logs = [log for log in filtered_logs if log.result == result]
        
        if startDate:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= startDate]
        
        if endDate:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= endDate]
        
        # Sort by timestamp, newest first
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_logs = filtered_logs[start_index:end_index]
        
        response = {
            "data": [log.dict() for log in paginated_logs],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_logs),
                "totalPages": (len(filtered_logs) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_logs),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit logs: {str(e)}")

@router.post("/audit", response_model=Dict[str, Any])
async def create_audit_log(
    request: AuditLogCreate,
    current_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create audit log entry"""
    try:
        user_id = current_user["id"]
        
        audit_log = AuditLogEntry(
            id=generate_id(),
            timestamp=datetime.now().isoformat(),
            userId=user_id,
            userRole=getattr(current_user, 'admin_role', 'user'),
            action=request.action,
            resource=request.resource,
            details=request.details,
            ipAddress=current_request.client.host if current_request.client else "unknown",
            userAgent=current_request.headers.get("user-agent", "unknown"),
            result="success",
            severity=request.severity,
            category=request.category,
            previousValue=request.previousValue,
            newValue=request.newValue
        )
        
        audit_logs.append(audit_log)
        
        return {
            "success": True,
            "data": audit_log.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create audit log: {str(e)}")

@router.get("/audit/security", response_model=Dict[str, Any])
async def get_security_events(
    eventType: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    mitigated: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get security events (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for security events")
        
        filtered_events = security_events.copy()
        
        # Apply filters
        if eventType:
            filtered_events = [e for e in filtered_events if e.eventType == eventType]
        
        if severity:
            filtered_events = [e for e in filtered_events if e.severity == severity]
        
        if mitigated is not None:
            filtered_events = [e for e in filtered_events if e.mitigated == mitigated]
        
        # Sort by timestamp, newest first
        filtered_events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_events = filtered_events[start_index:end_index]
        
        response = {
            "data": [event.dict() for event in paginated_events],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_events),
                "totalPages": (len(filtered_events) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_events),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security events: {str(e)}")

@router.post("/audit/security", response_model=Dict[str, Any])
async def create_security_event(
    request: SecurityEventCreate,
    current_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create security event"""
    try:
        user_id = current_user["id"]
        
        security_event = SecurityEvent(
            id=generate_id(),
            timestamp=datetime.now().isoformat(),
            eventType=request.eventType,
            userId=request.targetUserId,
            ipAddress=current_request.client.host if current_request.client else "unknown",
            severity=request.severity,
            description=f"Security event: {request.eventType}",
            details={"createdBy": user_id, **request.details},
            mitigated=False
        )
        
        security_events.append(security_event)
        
        # Also create audit log
        audit_log = AuditLogEntry(
            id=generate_id(),
            timestamp=datetime.now().isoformat(),
            userId=user_id,
            action=f"SECURITY_EVENT_{request.eventType.upper()}",
            resource="security",
            details=security_event.dict(),
            ipAddress=current_request.client.host if current_request.client else "unknown",
            userAgent=current_request.headers.get("user-agent", "unknown"),
            result="success",
            severity=request.severity,
            category="security"
        )
        audit_logs.append(audit_log)
        
        return {
            "success": True,
            "data": security_event.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create security event: {str(e)}")

@router.patch("/audit/security/{event_id}", response_model=Dict[str, Any])
async def update_security_event(
    event_id: str,
    request: SecurityEventUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update security event (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating security events")
        
        security_event = next((e for e in security_events if e.id == event_id), None)
        
        if not security_event:
            raise HTTPException(status_code=404, detail="Security event not found")
        
        # Update security event
        if request.mitigated is not None:
            security_event.mitigated = request.mitigated
        
        if request.mitigationActions:
            security_event.mitigationActions = request.mitigationActions
        
        if request.mitigated:
            security_event.resolvedAt = datetime.now().isoformat()
        
        # Add notes
        if request.notes:
            security_event.details["notes"] = request.notes
            security_event.details["lastUpdatedBy"] = current_user["id"]
            security_event.details["lastUpdatedAt"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": security_event.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update security event: {str(e)}")

# ==================== KYC ENDPOINTS ====================

@router.get("/kyc", response_model=Dict[str, Any])
async def get_kyc_status(current_user: dict = Depends(get_current_user)):
    """Get KYC status for authenticated user"""
    try:
        user_id = current_user["id"]
        
        # Find existing KYC profile
        kyc_profile = next((p for p in kyc_profiles if p.userId == user_id), None)
        
        if not kyc_profile:
            # Create initial KYC profile if doesn't exist
            kyc_profile = KYCProfile(
                id=generate_id(),
                userId=user_id,
                status="pending",
                verificationLevel="basic",
                personalInfo=None,
                addressInfo=None,
                identityDocuments=[],
                verificationHistory=[],
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            kyc_profiles.append(kyc_profile)
            
            # Add verification history
            history = VerificationHistory(
                id=generate_id(),
                action="submitted",
                performedBy="system",
                reason="Initial profile created",
                timestamp=datetime.now().isoformat()
            )
            kyc_profile.verificationHistory.append(history)
        
        return {
            "success": True,
            "data": kyc_profile.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve KYC information: {str(e)}")

@router.post("/kyc", response_model=Dict[str, Any])
async def submit_kyc_application(
    request: KYCSubmitRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit KYC application"""
    try:
        user_id = current_user["id"]
        
        # Find or create KYC profile
        kyc_profile = next((p for p in kyc_profiles if p.userId == user_id), None)
        
        if not kyc_profile:
            kyc_profile = KYCProfile(
                id=generate_id(),
                userId=user_id,
                status="pending",
                verificationLevel="basic",
                personalInfo=request.personalInfo,
                addressInfo=request.addressInfo,
                identityDocuments=[],
                verificationHistory=[],
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            kyc_profiles.append(kyc_profile)
        else:
            # Update existing profile
            kyc_profile.personalInfo = request.personalInfo
            kyc_profile.addressInfo = request.addressInfo
            kyc_profile.updatedAt = datetime.now().isoformat()
        
        # Process uploaded documents
        if request.documents:
            for doc_data in request.documents:
                document = IdentityDocument(
                    id=generate_id(),
                    type=doc_data.get("type"),
                    documentNumber=doc_data.get("documentNumber"),
                    issueDate=doc_data.get("issueDate"),
                    expiryDate=doc_data.get("expiryDate"),
                    issuingAuthority=doc_data.get("issuingAuthority"),
                    fileUrl=doc_data.get("fileUrl"),
                    fileHash=doc_data.get("fileHash") or generate_id(),
                    status="pending",
                    verifiedAt=None,
                    rejectionReason=None
                )
                
                kyc_profile.identityDocuments.append(document)
        
        # Add verification history
        history = VerificationHistory(
            id=generate_id(),
            action="submitted",
            performedBy=user_id,
            reason="KYC application submitted",
            timestamp=datetime.now().isoformat()
        )
        kyc_profile.verificationHistory.append(history)
        
        # Auto-advance status based on completeness
        if len(kyc_profile.identityDocuments) >= 2:
            kyc_profile.status = "in_review"
            history = VerificationHistory(
                id=generate_id(),
                action="review_started",
                performedBy="system",
                reason="Auto-review started after document submission",
                timestamp=datetime.now().isoformat()
            )
            kyc_profile.verificationHistory.append(history)
        
        kyc_profile.updatedAt = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": kyc_profile.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit KYC application: {str(e)}")

@router.patch("/kyc", response_model=Dict[str, Any])
async def update_kyc_status(
    request: KYCUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update KYC status (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for status updates")
        
        kyc_profile = next((p for p in kyc_profiles if p.userId == request.targetUserId), None)
        
        if not kyc_profile:
            raise HTTPException(status_code=404, detail="KYC profile not found")
        
        # Update KYC profile
        old_status = kyc_profile.status
        kyc_profile.status = request.status
        
        if request.verificationLevel:
            if request.verificationLevel in ["basic", "intermediate", "advanced"]:
                kyc_profile.verificationLevel = request.verificationLevel
        
        kyc_profile.updatedAt = datetime.now().isoformat()
        
        # Set expiry date for approved profiles
        if request.status == "approved":
            expiry_date = datetime.now()
            expiry_date = expiry_date.replace(year=expiry_date.year + 1)  # 1 year validity
            kyc_profile.expiresAt = expiry_date.isoformat()
        
        # Add verification history
        history = VerificationHistory(
            id=generate_id(),
            action=request.status,
            performedBy=current_user["id"],
            reason=request.reviewNotes,
            timestamp=datetime.now().isoformat()
        )
        kyc_profile.verificationHistory.append(history)
        
        return {
            "success": True,
            "data": kyc_profile.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update KYC status: {str(e)}")

@router.delete("/kyc", response_model=Dict[str, Any])
async def delete_kyc_profile(
    userId: str = Query(..., description="User ID to delete"),
    current_user: dict = Depends(get_current_user)
):
    """Delete KYC profile (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for deletion")
        
        # Find and remove KYC profile
        profile_index = next((i for i, p in enumerate(kyc_profiles) if p.userId == userId), None)
        
        if profile_index is None:
            raise HTTPException(status_code=404, detail="KYC profile not found")
        
        kyc_profiles.pop(profile_index)
        
        return {
            "success": True,
            "data": None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete KYC profile: {str(e)}")

# ==================== COMPLIANCE DASHBOARD ENDPOINTS ====================

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_compliance_dashboard(
    section: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get compliance dashboard overview"""
    try:
        user_id = current_user["id"]
        admin_role = getattr(current_user, 'admin_role', None)
        
        if section == "overview":
            # Calculate overview statistics
            total_users = len(kyc_profiles)
            approved_kyc = len([k for k in kyc_profiles if k.status == "approved"])
            pending_kyc = len([k for k in kyc_profiles if k.status in ["pending", "in_review"]])
            
            total_aml = len(aml_screenings)
            clean_aml = len([a for a in aml_screenings if a.status == "clean"])
            flagged_aml = len([a for a in aml_screenings if a.status == "flagged"])
            reported_aml = len([a for a in aml_screenings if a.status == "reported"])
            
            overall_score = 95  # Simulated
            
            dashboard_data = {
                "totalUsers": total_users,
                "kycStats": {
                    "approved": approved_kyc,
                    "pending": pending_kyc,
                    "completionRate": (approved_kyc / total_users * 100) if total_users > 0 else 0
                },
                "amlStats": {
                    "total": total_aml,
                    "clean": clean_aml,
                    "flagged": flagged_aml,
                    "reported": reported_aml
                },
                "overallComplianceScore": overall_score
            }
            
        elif section == "alerts":
            recent_alerts = compliance_alerts[-10:] if len(compliance_alerts) > 10 else compliance_alerts
            dashboard_data = {
                "alerts": [alert.dict() for alert in recent_alerts],
                "summary": {
                    "total": len(compliance_alerts),
                    "open": len([a for a in compliance_alerts if a.status == "open"]),
                    "critical": len([a for a in compliance_alerts if a.severity == "critical"])
                }
            }
            
        else:
            # Return full dashboard data
            dashboard_data = {
                "overview": {
                    "totalUsers": len(kyc_profiles),
                    "overallComplianceScore": 95
                },
                "alerts": {
                    "recent": [alert.dict() for alert in compliance_alerts[-5:]]
                }
            }
        
        return {
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard data: {str(e)}")

@router.get("/dashboard/metrics", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    period: str = Query("30d"),
    reportType: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed compliance metrics (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for detailed metrics")
        
        metrics = {
            "period": period,
            "generatedAt": datetime.now().isoformat(),
            "overview": {
                "totalUsers": len(kyc_profiles),
                "approvedUsers": len([k for k in kyc_profiles if k.status == "approved"]),
                "complianceScore": 95
            }
        }
        
        return {
            "success": True,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve compliance metrics: {str(e)}")

@router.post("/dashboard/alerts", response_model=Dict[str, Any])
async def create_dashboard_alert(
    request: DashboardAlertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create custom dashboard alert (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for creating alerts")
        
        alert = ComplianceAlert(
            id=generate_id(),
            userId=request.targetUserId or "system",
            alertType=request.alertType,
            severity=request.severity,
            title=request.title,
            description=request.description,
            actionRequired=request.severity in ["critical", "high"],
            status="open",
            createdAt=datetime.now().isoformat()
        )
        
        compliance_alerts.append(alert)
        
        return {
            "success": True,
            "data": alert.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard alert: {str(e)}")

@router.patch("/dashboard/alerts/{alert_id}", response_model=Dict[str, Any])
async def update_dashboard_alert(
    alert_id: str,
    status: Optional[str] = Query(None),
    assignedTo: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Update alert status (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating alerts")
        
        alert = next((a for a in compliance_alerts if a.id == alert_id), None)
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # Update alert
        if status and status in ["open", "in_progress", "resolved", "closed"]:
            alert.status = status
        
        if assignedTo:
            alert.assignedTo = assignedTo
        
        if status in ["resolved", "closed"]:
            alert.resolvedAt = datetime.now().isoformat()
        
        if notes:
            alert.notes = notes
            setattr(alert, "lastUpdatedBy", current_user["id"])
            setattr(alert, "lastUpdatedAt", datetime.now().isoformat())
        
        return {
            "success": True,
            "data": alert.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update dashboard alert: {str(e)}")

# ==================== REGULATORY REPORTS ENDPOINTS ====================

@router.get("/reports", response_model=Dict[str, Any])
async def get_regulatory_reports(
    reportType: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get regulatory reports"""
    try:
        filtered_reports = regulatory_reports.copy()
        
        # Apply filters
        if reportType:
            filtered_reports = [r for r in filtered_reports if r.reportType == reportType]
        
        if status:
            filtered_reports = [r for r in filtered_reports if r.status == status]
        
        if jurisdiction:
            filtered_reports = [r for r in filtered_reports if r.jurisdiction == jurisdiction]
        
        # Sort by creation date, newest first
        filtered_reports.sort(key=lambda x: x.createdAt, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_reports = filtered_reports[start_index:end_index]
        
        response = {
            "data": [report.dict() for report in paginated_reports],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_reports),
                "totalPages": (len(filtered_reports) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_reports),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve regulatory reports: {str(e)}")

@router.post("/reports", response_model=Dict[str, Any])
async def generate_regulatory_report(
    request: RegulatoryReportCreate,
    current_user: dict = Depends(get_current_user)
):
    """Generate new regulatory report"""
    try:
        user_id = current_user["id"]
        
        if request.reportType not in ["suspicious_activity", "large_transaction", "kyc_data", "compliance_summary", "risk_assessment"]:
            raise HTTPException(status_code=400, detail="Invalid report type")
        
        # Create basic report structure
        report_data = {
            "id": generate_id(),
            "reportType": request.reportType,
            "jurisdiction": request.jurisdiction,
            "status": "draft",
            "data": request.data or {},
            "submittedBy": user_id,
            "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
            "createdAt": datetime.now().isoformat()
        }
        
        regulatory_reports.append(report_data)
        
        return {
            "success": True,
            "data": report_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate regulatory report: {str(e)}")

@router.patch("/reports/{report_id}", response_model=Dict[str, Any])
async def update_regulatory_report(
    report_id: str,
    request: RegulatoryReportUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update report status (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating reports")
        
        report = next((r for r in regulatory_reports if r.id == report_id), None)
        
        if not report:
            raise HTTPException(status_code=404, detail="Regulatory report not found")
        
        # Update report
        if request.status and request.status in ["draft", "submitted", "accepted", "rejected"]:
            report["status"] = request.status
        
        if request.referenceNumber:
            report["referenceNumber"] = request.referenceNumber
        
        if request.rejectionReason:
            report["rejectionReason"] = request.rejectionReason
        
        # Set submission timestamp when moving to submitted status
        if request.status == "submitted" and not report.get("submittedAt"):
            report["submittedAt"] = datetime.now().isoformat()
        
        # Add notes if provided
        if request.notes:
            report["data"]["notes"] = request.notes
            report["data"]["lastUpdatedBy"] = current_user["id"]
            report["data"]["lastUpdatedAt"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": report,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update regulatory report: {str(e)}")

@router.post("/reports/auto-generate", response_model=Dict[str, Any])
async def auto_generate_reports(current_user: dict = Depends(get_current_user)):
    """Auto-generate reports (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for auto-generating reports")
        
        # Simulate auto-generation
        generated_count = 0
        
        # Generate SAR for critical suspicious activities
        critical_activities = [a for a in suspicious_activities if a.riskLevel == "critical" and a.status == "reported"]
        
        for activity in critical_activities:
            if not any(r.get("data", {}).get("relatedActivityId") == activity.id for r in regulatory_reports):
                sar_report = {
                    "id": generate_id(),
                    "reportType": "suspicious_activity",
                    "jurisdiction": "US",
                    "status": "draft",
                    "data": {"relatedActivityId": activity.id},
                    "submittedBy": "System",
                    "dueDate": (datetime.now() + timedelta(days=30)).isoformat(),
                    "createdAt": datetime.now().isoformat()
                }
                regulatory_reports.append(sar_report)
                generated_count += 1
        
        return {
            "success": True,
            "data": {"generatedCount": generated_count},
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to auto-generate reports: {str(e)}")

@router.get("/reports/metrics", response_model=Dict[str, Any])
async def get_reporting_metrics(current_user: dict = Depends(get_current_user)):
    """Get reporting metrics (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for reporting metrics")
        
        # Calculate metrics
        total_reports = len(regulatory_reports)
        reports_by_type = {}
        reports_by_status = {}
        
        for report in regulatory_reports:
            report_type = report.get("reportType", "unknown")
            status = report.get("status", "unknown")
            
            reports_by_type[report_type] = reports_by_type.get(report_type, 0) + 1
            reports_by_status[status] = reports_by_status.get(status, 0) + 1
        
        metrics = ComplianceMetrics(
            totalReports=total_reports,
            reportsByType=reports_by_type,
            reportsByStatus=reports_by_status,
            averageProcessingTime=2.5,
            complianceScore=95,
            riskMetrics={
                "highRiskUsers": len([a for a in suspicious_activities if a.riskLevel in ["high", "critical"]]),
                "flaggedTransactions": 0,
                "suspiciousActivities": len(suspicious_activities),
                "kycCompletionRate": 95
            },
            auditFindings=[],
            calculatedAt=datetime.now().isoformat()
        )
        
        return {
            "success": True,
            "data": metrics.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reporting metrics: {str(e)}")

# ==================== COMPLIANCE RULES ENGINE ENDPOINTS ====================

@router.get("/rules", response_model=Dict[str, Any])
async def get_compliance_rules(
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    isActive: Optional[bool] = Query(None),
    ruleId: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get compliance rules"""
    try:
        user_id = current_user["id"]
        admin_role = getattr(current_user, 'admin_role', None)
        
        filtered_rules = compliance_rules.copy()
        
        # Apply filters
        if ruleId:
            filtered_rules = [r for r in filtered_rules if r.id == ruleId]
        
        if category:
            filtered_rules = [r for r in filtered_rules if r.category == category]
        
        if severity:
            filtered_rules = [r for r in filtered_rules if r.severity == severity]
        
        if isActive is not None:
            filtered_rules = [r for r in filtered_rules if r.isActive == isActive]
        
        # Regular users can only see active rules
        if admin_role not in ['compliance_officer', 'admin']:
            filtered_rules = [r for r in filtered_rules if r.isActive]
        
        # Sort by name
        filtered_rules.sort(key=lambda x: x.name)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_rules = filtered_rules[start_index:end_index]
        
        response = {
            "data": [rule.dict() for rule in paginated_rules],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_rules),
                "totalPages": (len(filtered_rules) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_rules),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve compliance rules: {str(e)}")

@router.post("/rules", response_model=Dict[str, Any])
async def create_compliance_rule(
    request: ComplianceRuleCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new compliance rule (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for creating rules")
        
        # Validate category
        if request.category not in ["aml", "kyc", "transaction_monitoring", "sanctions", "market_abuse"]:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        # Validate severity
        if request.severity not in ["low", "medium", "high", "critical"]:
            raise HTTPException(status_code=400, detail="Invalid severity level")
        
        # Create new rule
        new_rule = ComplianceRule(
            id=generate_id(),
            name=request.name,
            description=request.description,
            category=request.category,
            severity=request.severity,
            isActive=request.isActive,
            conditions=request.conditions,
            actions=request.actions,
            triggerCount=0,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        compliance_rules.append(new_rule)
        
        return {
            "success": True,
            "data": new_rule.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create compliance rule: {str(e)}")

@router.patch("/rules/{rule_id}", response_model=Dict[str, Any])
async def update_compliance_rule(
    rule_id: str,
    request: ComplianceRuleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update compliance rule (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating rules")
        
        rule = next((r for r in compliance_rules if r.id == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Compliance rule not found")
        
        # Update rule fields
        if request.name:
            rule.name = request.name
        if request.description:
            rule.description = request.description
        if request.category and request.category in ["aml", "kyc", "transaction_monitoring", "sanctions", "market_abuse"]:
            rule.category = request.category
        if request.severity and request.severity in ["low", "medium", "high", "critical"]:
            rule.severity = request.severity
        if request.conditions:
            rule.conditions = request.conditions
        if request.actions:
            rule.actions = request.actions
        if request.isActive is not None:
            rule.isActive = request.isActive
        
        rule.updatedAt = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": rule.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update compliance rule: {str(e)}")

@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_compliance_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete compliance rule (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for deleting rules")
        
        rule_index = next((i for i, r in enumerate(compliance_rules) if r.id == rule_id), None)
        
        if rule_index is None:
            raise HTTPException(status_code=404, detail="Compliance rule not found")
        
        compliance_rules.pop(rule_index)
        
        return {
            "success": True,
            "data": None,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete compliance rule: {str(e)}")

@router.post("/rules/{rule_id}/evaluate", response_model=Dict[str, Any])
async def evaluate_rule(
    rule_id: str,
    request: RuleEvaluationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Evaluate rule against data"""
    try:
        rule = next((r for r in compliance_rules if r.id == rule_id), None)
        
        if not rule:
            raise HTTPException(status_code=404, detail="Compliance rule not found")
        
        if not rule.isActive:
            raise HTTPException(status_code=400, detail="Rule is not active")
        
        evaluation_start_time = datetime.now()
        
        # Simple rule evaluation (in real implementation, this would be more sophisticated)
        conditions_met = [True] * len(rule.conditions)  # Simplified - assume all conditions met
        actions_executed = [{"action": action.dict(), "success": True} for action in rule.actions]
        
        evaluation_time = (datetime.now() - evaluation_start_time).total_seconds() * 1000
        
        # Update rule trigger count
        rule.triggerCount += 1
        rule.lastTriggered = datetime.now().isoformat()
        rule.updatedAt = datetime.now().isoformat()
        
        # Create execution result
        execution_result = RuleExecutionResult(
            id=generate_id(),
            ruleId=rule_id,
            timestamp=datetime.now().isoformat(),
            triggerData=request.triggerData,
            conditionsMet=conditions_met,
            actionsExecuted=actions_executed,
            executionTime=int(evaluation_time),
            result="success"
        )
        
        rule_execution_results.append(execution_result)
        
        return {
            "success": True,
            "data": execution_result.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate compliance rule: {str(e)}")

@router.get("/rules/{rule_id}/executions", response_model=Dict[str, Any])
async def get_rule_executions(
    rule_id: str,
    result: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get rule execution history"""
    try:
        filtered_executions = [r for r in rule_execution_results if r.ruleId == rule_id]
        
        # Apply filters
        if result:
            filtered_executions = [r for r in filtered_executions if r.result == result]
        
        # Sort by timestamp, newest first
        filtered_executions.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_executions = filtered_executions[start_index:end_index]
        
        response = {
            "data": [execution.dict() for execution in paginated_executions],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_executions),
                "totalPages": (len(filtered_executions) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_executions),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rule execution history: {str(e)}")

# ==================== SANCTIONS SCREENING ENDPOINTS ====================

@router.get("/sanctions", response_model=Dict[str, Any])
async def search_sanctions_lists(
    name: Optional[str] = Query(None),
    program: Optional[str] = Query(None),
    listType: Optional[str] = Query(None),
    riskLevel: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Search sanctions lists"""
    try:
        user_id = current_user["id"]
        
        if not name:
            # Return all sanctions if no name provided (for admin viewing)
            admin_role = getattr(current_user, 'admin_role', None)
            if admin_role not in ['compliance_officer', 'admin']:
                raise HTTPException(status_code=400, detail="Name parameter required for sanctions search")
            
            filtered_sanctions = sanctions_lists.copy()
            
            if program:
                filtered_sanctions = [s for s in filtered_sanctions if s.program == program]
            
            if listType:
                filtered_sanctions = [s for s in filtered_sanctions if s.listType == listType]
            
            if riskLevel:
                filtered_sanctions = [s for s in filtered_sanctions if s.riskLevel == riskLevel]
            
            # Sort by risk level and name
            filtered_sanctions.sort(key=lambda x: ({"critical": 4, "high": 3, "medium": 2, "low": 1}.get(x.riskLevel, 0), x.name))
            
            # Pagination
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_sanctions = filtered_sanctions[start_index:end_index]
            
            response = {
                "data": [sanction.dict() for sanction in paginated_sanctions],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(filtered_sanctions),
                    "totalPages": (len(filtered_sanctions) + limit - 1) // limit,
                    "hasNext": end_index < len(filtered_sanctions),
                    "hasPrevious": page > 1
                }
            }
            
            return {
                "success": True,
                "data": response,
                "timestamp": datetime.now().isoformat()
            }
        
        # Search for specific name
        exact_matches = [s for s in sanctions_lists if s.name.lower() == name.lower()]
        fuzzy_matches = [
            FuzzyMatch(entry=s.dict(), score=75) 
            for s in sanctions_lists 
            if s.name.lower() != name.lower() and name.lower() in s.name.lower()
        ][:5]  # Limit to 5 fuzzy matches
        
        results = {
            "exactMatches": [match.dict() for match in exact_matches],
            "fuzzyMatches": [match.dict() for match in fuzzy_matches],
            "searchQuery": name,
            "totalMatches": len(exact_matches) + len(fuzzy_matches)
        }
        
        return {
            "success": True,
            "data": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search sanctions lists: {str(e)}")

@router.post("/sanctions/screen", response_model=Dict[str, Any])
async def perform_sanctions_screening(
    request: SanctionsScreeningRequest,
    current_user: dict = Depends(get_current_user)
):
    """Perform comprehensive sanctions screening"""
    try:
        user_id = current_user["id"]
        
        # Search all databases
        sanctions_results = {
            "exactMatches": [s for s in sanctions_lists if s.name.lower() == request.name.lower()],
            "fuzzyMatches": [FuzzyMatch(entry=s.dict(), score=75) for s in sanctions_lists if s.name.lower() != request.name.lower() and request.name.lower() in s.name.lower()][:5]
        }
        
        pep_results = {
            "exactMatches": [p for p in pep_database if p.name.lower() == request.name.lower()],
            "fuzzyMatches": [FuzzyMatch(entry=p.dict(), score=70) for p in pep_database if p.name.lower() != request.name.lower() and request.name.lower() in p.name.lower()][:5]
        }
        
        watchlist_results = {
            "exactMatches": [w for w in watchlists if w.name.lower() == request.name.lower()],
            "fuzzyMatches": [FuzzyMatch(entry=w.dict(), score=70) for w in watchlists if w.name.lower() != request.name.lower() and request.name.lower() in w.name.lower()][:5]
        }
        
        # Determine overall risk
        overall_risk = "low"
        if sanctions_results["exactMatches"]:
            overall_risk = "critical" if any(s.riskLevel == "critical" for s in sanctions_results["exactMatches"]) else "high"
        elif pep_results["exactMatches"] or watchlist_results["exactMatches"]:
            overall_risk = "medium"
        
        # Create screening result
        screening_result = ScreeningResult(
            id=generate_id(),
            timestamp=datetime.now().isoformat(),
            queryName=request.name,
            queryType=request.queryType,
            results={
                "sanctionsMatches": sanctions_results["exactMatches"],
                "pepMatches": pep_results["exactMatches"],
                "watchlistMatches": watchlist_results["exactMatches"],
                "fuzzyMatches": {
                    "sanctions": sanctions_results["fuzzyMatches"],
                    "pep": pep_results["fuzzyMatches"],
                    "watchlist": watchlist_results["fuzzyMatches"]
                }
            },
            overallRisk=overall_risk,
            requiresReview=overall_risk in ["high", "critical"],
            status="escalated" if overall_risk == "critical" else "flagged" if overall_risk == "high" else "cleared"
        )
        
        screening_results.append(screening_result)
        
        # Create AML findings for matches
        findings = []
        for match in sanctions_results["exactMatches"]:
            findings.append(AMLFinding(
                category="sanctions",
                source=match.program,
                description=f"Sanctions match found: {match.name} ({match.program})",
                severity="high" if match.riskLevel == "critical" else match.riskLevel,
                confidence=95,
                actionTaken="Immediate escalation required" if match.riskLevel == "critical" else "Flagged for review",
                timestamp=datetime.now().isoformat()
            ))
        
        return {
            "success": True,
            "data": {**screening_result.dict(), "findings": [f.dict() for f in findings]},
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform sanctions screening: {str(e)}")

@router.get("/sanctions/screenings", response_model=Dict[str, Any])
async def get_screening_results(
    status: Optional[str] = Query(None),
    riskLevel: Optional[str] = Query(None),
    requiresReview: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get screening results"""
    try:
        filtered_results = screening_results.copy()
        
        # Apply filters
        if status:
            filtered_results = [r for r in filtered_results if r.status == status]
        
        if riskLevel:
            filtered_results = [r for r in filtered_results if r.overallRisk == riskLevel]
        
        if requiresReview is not None:
            filtered_results = [r for r in filtered_results if r.requiresReview == requiresReview]
        
        # Sort by timestamp, newest first
        filtered_results.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_results = filtered_results[start_index:end_index]
        
        response = {
            "data": [result.dict() for result in paginated_results],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_results),
                "totalPages": (len(filtered_results) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_results),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve screening results: {str(e)}")

@router.patch("/sanctions/screenings/{screening_id}", response_model=Dict[str, Any])
async def update_screening_result(
    screening_id: str,
    request: SanctionsUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update screening result (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating screening results")
        
        screening_result = next((r for r in screening_results if r.id == screening_id), None)
        
        if not screening_result:
            raise HTTPException(status_code=404, detail="Screening result not found")
        
        # Update screening result
        if request.status and request.status in ["pending", "reviewing", "cleared", "flagged", "escalated"]:
            screening_result.status = request.status
        
        if request.reviewerNotes:
            screening_result.reviewerNotes = request.reviewerNotes
        
        screening_result.reviewedBy = current_user["id"]
        screening_result.reviewedAt = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": screening_result.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update screening result: {str(e)}")

# ==================== TRANSACTION MONITORING ENDPOINTS ====================

@router.get("/transaction-monitoring", response_model=Dict[str, Any])
async def get_transaction_monitoring(
    transactionId: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get transaction monitoring status"""
    try:
        user_id = current_user["id"]
        
        if transactionId:
            monitorings = [m for m in transaction_monitorings if m.transactionId == transactionId]
        else:
            # Get user's transaction monitorings
            monitorings = [m for m in transaction_monitorings if m.userId == user_id]
        
        # Sort by creation date, newest first
        monitorings.sort(key=lambda x: x.createdAt, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_monitorings = monitorings[start_index:end_index]
        
        response = {
            "data": [monitoring.dict() for monitoring in paginated_monitorings],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(monitorings),
                "totalPages": (len(monitorings) + limit - 1) // limit,
                "hasNext": end_index < len(monitorings),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transaction monitoring data: {str(e)}")

@router.post("/transaction-monitoring", response_model=Dict[str, Any])
async def start_transaction_monitoring(
    transactionId: str,
    amount: float,
    transactionType: str,
    originCountry: Optional[str] = "US",
    destinationCountry: Optional[str] = "US",
    currency: Optional[str] = "USD",
    current_user: dict = Depends(get_current_user)
):
    """Start transaction monitoring"""
    try:
        user_id = current_user["id"]
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Transaction amount must be greater than zero")
        
        # Get user's transaction history for pattern analysis
        user_history = [
            {
                "userId": m.userId,
                "timestamp": m.createdAt,
                "amount": m.flags[0].actualValue if m.flags else 0
            }
            for m in transaction_monitorings if m.userId == user_id
        ]
        
        # Assess transaction risk
        flags: List[MonitoringFlag] = []
        
        # Large amount flag
        if amount >= 50000:
            flags.append(MonitoringFlag(
                id=generate_id(),
                flagType="large_amount",
                severity="critical" if amount >= 100000 else "high",
                description=f"Large transaction amount: ${amount:,.0f}",
                rule="LARGE_TRANSACTION_MONITORING",
                threshold=50000,
                actualValue=amount,
                confidence=90
            ))
        
        # Geographic risk flags
        high_risk_countries = ['IR', 'KP', 'SY', 'CU', 'RU', 'AF', 'IQ', 'LY', 'SO', 'SS', 'YE']
        if originCountry in high_risk_countries or destinationCountry in high_risk_countries:
            flags.append(MonitoringFlag(
                id=generate_id(),
                flagType="high_risk_jurisdiction",
                severity="critical",
                description=f"High-risk jurisdiction: {originCountry} → {destinationCountry}",
                rule="HIGH_RISK_JURISDICTION",
                actualValue=f"{originCountry}/{destinationCountry}",
                confidence=100
            ))
        
        # Create monitoring record
        monitoring = TransactionMonitoring(
            id=generate_id(),
            transactionId=transactionId,
            userId=user_id,
            monitoringType="enhanced" if any(f.severity == "critical" for f in flags) else "real_time",
            status="flagged" if flags else "clean",
            riskScore=min(100, sum(
                25 if f.severity == "critical" else 
                15 if f.severity == "high" else 
                10 if f.severity == "medium" else 5 
                for f in flags
            )),
            flags=flags,
            reviewed=False,
            createdAt=datetime.now().isoformat()
        )
        
        transaction_monitorings.append(monitoring)
        
        # Check if any flags warrant immediate investigation
        critical_flags = [f for f in flags if f.severity == "critical"]
        if critical_flags:
            suspicious_activity = SuspiciousActivity(
                id=generate_id(),
                userId=user_id,
                activityType="money_laundering",
                description=f"Critical risk indicators detected in transaction {transactionId}: {', '.join(f.flagType for f in critical_flags)}",
                evidence={
                    "transactionId": transactionId,
                    "amount": amount,
                    "flags": critical_flags,
                    "riskScore": monitoring.riskScore
                },
                riskLevel="critical",
                status="reported",
                reportedBy="AML System",
                reportedAt=datetime.now().isoformat(),
                investigationNotes="Auto-generated critical risk alert based on transaction monitoring rules"
            )
            suspicious_activities.append(suspicious_activity)
            
            # Update monitoring status
            monitoring.status = "reported"
            monitoring.reviewed = False
        
        return {
            "success": True,
            "data": monitoring.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process transaction monitoring: {str(e)}")

@router.patch("/transaction-monitoring", response_model=Dict[str, Any])
async def update_monitoring_status(
    monitoringId: str,
    reviewed: Optional[bool] = None,
    reviewedBy: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update monitoring status (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for updating monitoring status")
        
        monitoring = next((m for m in transaction_monitorings if m.id == monitoringId), None)
        
        if not monitoring:
            raise HTTPException(status_code=404, detail="Transaction monitoring record not found")
        
        # Update monitoring record
        if reviewed is not None:
            monitoring.reviewed = reviewed
        
        if reviewedBy:
            monitoring.reviewedBy = reviewedBy
        
        if reviewed:
            monitoring.reviewedAt = datetime.now().isoformat()
        
        # If reviewing suspicious activity, update the related suspicious activity record
        if monitoring.status == "reported" and reviewed:
            suspicious_activity = next((
                s for s in suspicious_activities 
                if s.evidence and s.evidence.get("transactionId") == monitoring.transactionId
            ), None)
            
            if suspicious_activity:
                suspicious_activity.status = "investigating"
                suspicious_activity.assignedTo = reviewedBy
                suspicious_activity.investigationNotes = notes
        
        return {
            "success": True,
            "data": monitoring.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update transaction monitoring: {str(e)}")

@router.get("/transaction-monitoring/suspicious-activities", response_model=Dict[str, Any])
async def get_suspicious_activities(
    status: Optional[str] = Query(None),
    riskLevel: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Get suspicious activities (admin only)"""
    try:
        admin_role = getattr(current_user, 'admin_role', None)
        if admin_role not in ['compliance_officer', 'admin']:
            raise HTTPException(status_code=403, detail="Admin privileges required for viewing suspicious activities")
        
        filtered_activities = suspicious_activities.copy()
        
        # Apply filters
        if status:
            filtered_activities = [a for a in filtered_activities if a.status == status]
        
        if riskLevel:
            filtered_activities = [a for a in filtered_activities if a.riskLevel == riskLevel]
        
        # Sort by reported date, newest first
        filtered_activities.sort(key=lambda x: x.reportedAt, reverse=True)
        
        # Pagination
        start_index = (page - 1) * limit
        end_index = start_index + limit
        paginated_activities = filtered_activities[start_index:end_index]
        
        response = {
            "data": [activity.dict() for activity in paginated_activities],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_activities),
                "totalPages": (len(filtered_activities) + limit - 1) // limit,
                "hasNext": end_index < len(filtered_activities),
                "hasPrevious": page > 1
            }
        }
        
        return {
            "success": True,
            "data": response,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve suspicious activities: {str(e)}")