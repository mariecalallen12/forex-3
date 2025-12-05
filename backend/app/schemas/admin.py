"""
Admin Module Schemas - Migration từ Next.js
Bao gồm tất cả schemas cho admin endpoints: users, customers, deposits, platform stats, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ========== USER MANAGEMENT SCHEMAS ==========

class UserRole(str, Enum):
    """User roles"""
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class KYCStatus(str, Enum):
    """KYC verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class UserBalance(BaseModel):
    """User balance across different currencies"""
    usdt: Optional[float] = Field(default=0, description="USDT balance")
    btc: Optional[float] = Field(default=0, description="BTC balance")
    eth: Optional[float] = Field(default=0, description="ETH balance")
    vnd: Optional[float] = Field(default=0, description="VND balance")
    usd: Optional[float] = Field(default=0, description="USD balance")


class AdminUser(BaseModel):
    """Schema for admin user management"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    displayName: Optional[str] = Field(None, description="Display name")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Account status")
    kycStatus: KYCStatus = Field(default=KYCStatus.PENDING, description="KYC status")
    isActive: bool = Field(default=True, description="Account active status")
    phoneNumber: Optional[str] = Field(None, description="Phone number")
    emailVerified: bool = Field(default=False, description="Email verified status")
    phoneVerified: bool = Field(default=False, description="Phone verified status")
    balance: UserBalance = Field(default_factory=UserBalance, description="User balances")
    lastLoginAt: Optional[datetime] = Field(None, description="Last login time")
    createdAt: datetime = Field(default_factory=datetime.now, description="Registration time")
    updatedAt: Optional[datetime] = Field(None, description="Last update time")
    deletedAt: Optional[datetime] = Field(None, description="Deletion time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GetUsersRequest(BaseModel):
    """Schema for GET users request"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search by email")
    role: Optional[UserRole] = Field(None, description="Filter by role")
    status: Optional[UserStatus] = Field(None, description="Filter by status")
    kycStatus: Optional[KYCStatus] = Field(None, description="Filter by KYC status")
    sortBy: str = Field(default="createdAt", description="Sort field")
    sortOrder: str = Field(default="desc", description="Sort order")


class UpdateUserRequest(BaseModel):
    """Schema for PUT user update request"""
    role: Optional[UserRole] = Field(None, description="User role")
    status: Optional[UserStatus] = Field(None, description="Account status")
    kycStatus: Optional[KYCStatus] = Field(None, description="KYC status")
    isActive: Optional[bool] = Field(None, description="Account active status")
    balance: Optional[UserBalance] = Field(None, description="User balances")


class UsersResponse(BaseModel):
    """Schema for users response"""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Response data")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")


class UserResponse(BaseModel):
    """Schema for single user response"""
    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    updatedFields: Optional[List[str]] = Field(None, description="Updated fields")


# ========== CUSTOMER MANAGEMENT SCHEMAS ==========

class AdminCustomer(BaseModel):
    """Schema for admin customer management"""
    id: str = Field(..., description="Customer ID")
    userId: str = Field(..., description="Associated user ID")
    email: str = Field(..., description="Customer email")
    displayName: Optional[str] = Field(None, description="Display name")
    phoneNumber: Optional[str] = Field(None, description="Phone number")
    registrationDate: datetime = Field(default_factory=datetime.now, description="Registration date")
    totalDeposits: float = Field(default=0, description="Total deposit amount")
    totalWithdrawals: float = Field(default=0, description="Total withdrawal amount")
    kycStatus: KYCStatus = Field(default=KYCStatus.PENDING, description="KYC status")
    isActive: bool = Field(default=True, description="Account active status")
    referralSource: Optional[str] = Field(None, description="Referral source")
    lastActivity: Optional[datetime] = Field(None, description="Last activity time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class GetCustomersRequest(BaseModel):
    """Schema for GET customers request"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search by email or name")
    kycStatus: Optional[KYCStatus] = Field(None, description="Filter by KYC status")
    isActive: Optional[bool] = Field(None, description="Filter by active status")
    sortBy: str = Field(default="registrationDate", description="Sort field")
    sortOrder: str = Field(default="desc", description="Sort order")


class CustomersResponse(BaseModel):
    """Schema for customers response"""
    success: bool = Field(..., description="Operation success status")
    data: List[AdminCustomer] = Field(..., description="Customer list")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")


# ========== DEPOSIT MANAGEMENT SCHEMAS ==========

class AdminDeposit(BaseModel):
    """Schema for admin deposit management"""
    id: str = Field(..., description="Deposit ID")
    userId: str = Field(..., description="User ID")
    customerEmail: str = Field(..., description="Customer email")
    amount: float = Field(..., description="Deposit amount")
    currency: str = Field(..., description="Currency")
    status: str = Field(..., description="Deposit status")
    paymentMethod: str = Field(..., description="Payment method")
    transactionHash: Optional[str] = Field(None, description="Blockchain transaction hash")
    bankReference: Optional[str] = Field(None, description="Bank reference")
    adminNotes: Optional[str] = Field(None, description="Admin notes")
    processedAt: Optional[datetime] = Field(None, description="Processing time")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    updatedAt: Optional[datetime] = Field(None, description="Last update time")


class DepositDetailRequest(BaseModel):
    """Schema for deposit detail request"""
    depositId: str = Field(..., description="Deposit ID")


class DepositDetailResponse(BaseModel):
    """Schema for deposit detail response"""
    success: bool = Field(..., description="Operation success status")
    data: AdminDeposit = Field(..., description="Deposit details")


# ========== PLATFORM STATISTICS SCHEMAS ==========

class PlatformStats(BaseModel):
    """Schema for platform statistics"""
    totalUsers: int = Field(..., description="Total registered users")
    activeUsers: int = Field(..., description="Active users (last 30 days)")
    totalDeposits: float = Field(..., description="Total deposit amount")
    totalWithdrawals: float = Field(..., description="Total withdrawal amount")
    averageDeposit: float = Field(..., description="Average deposit amount")
    averageWithdrawal: float = Field(..., description="Average withdrawal amount")
    newUsersToday: int = Field(..., description="New users today")
    newUsersThisMonth: int = Field(..., description="New users this month")
    verifiedKycUsers: int = Field(..., description="KYC verified users")
    pendingKycUsers: int = Field(..., description="KYC pending users")
    totalRevenue: float = Field(..., description="Total platform revenue")
    transactionVolume: float = Field(..., description="Transaction volume")
    lastUpdated: datetime = Field(default_factory=datetime.now, description="Last update time")


class PlatformStatsResponse(BaseModel):
    """Schema for platform stats response"""
    success: bool = Field(..., description="Operation success status")
    data: PlatformStats = Field(..., description="Platform statistics")


# ========== REFERRAL MANAGEMENT SCHEMAS ==========

class ReferralRecord(BaseModel):
    """Schema for referral management"""
    id: str = Field(..., description="Referral ID")
    referrerUserId: str = Field(..., description="Referrer user ID")
    referrerEmail: str = Field(..., description="Referrer email")
    referredUserId: str = Field(..., description="Referred user ID")
    referredEmail: str = Field(..., description="Referred user email")
    referralCode: str = Field(..., description="Referral code used")
    staffId: Optional[str] = Field(None, description="Staff ID")
    staffName: Optional[str] = Field(None, description="Staff name")
    commission: float = Field(default=0, description="Commission amount")
    status: str = Field(default="pending", description="Referral status")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")


class GetReferralsRequest(BaseModel):
    """Schema for GET referrals request"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search by email")
    staffId: Optional[str] = Field(None, description="Filter by staff ID")
    status: Optional[str] = Field(None, description="Filter by status")
    sortBy: str = Field(default="createdAt", description="Sort field")
    sortOrder: str = Field(default="desc", description="Sort order")


class ReferralsResponse(BaseModel):
    """Schema for referrals response"""
    success: bool = Field(..., description="Operation success status")
    data: List[ReferralRecord] = Field(..., description="Referral records")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")


# ========== SUBACCOUNT MANAGEMENT SCHEMAS ==========

class Subaccount(BaseModel):
    """Schema for subaccount management"""
    id: str = Field(..., description="Subaccount ID")
    parentUserId: str = Field(..., description="Parent user ID")
    email: str = Field(..., description="Subaccount email")
    displayName: Optional[str] = Field(None, description="Display name")
    permissions: List[str] = Field(default_factory=list, description="Subaccount permissions")
    isActive: bool = Field(default=True, description="Active status")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    lastLogin: Optional[datetime] = Field(None, description="Last login time")


class GetSubaccountsRequest(BaseModel):
    """Schema for GET subaccounts request"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    parentUserId: Optional[str] = Field(None, description="Filter by parent user")
    isActive: Optional[bool] = Field(None, description="Filter by active status")
    sortBy: str = Field(default="createdAt", description="Sort field")
    sortOrder: str = Field(default="desc", description="Sort order")


class SubaccountsResponse(BaseModel):
    """Schema for subaccounts response"""
    success: bool = Field(..., description="Operation success status")
    data: List[Subaccount] = Field(..., description="Subaccount list")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")


# ========== TRADING ADJUSTMENTS SCHEMAS ==========

class TradingAdjustment(BaseModel):
    """Schema for trading adjustments"""
    id: str = Field(..., description="Adjustment ID")
    userId: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    adjustmentType: str = Field(..., description="Adjustment type")
    amount: float = Field(..., description="Adjustment amount")
    currency: str = Field(..., description="Currency")
    reason: str = Field(..., description="Adjustment reason")
    adminId: str = Field(..., description="Admin who made the adjustment")
    adminEmail: str = Field(..., description="Admin email")
    status: str = Field(default="pending", description="Adjustment status")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    processedAt: Optional[datetime] = Field(None, description="Processing time")


class GetTradingAdjustmentsRequest(BaseModel):
    """Schema for GET trading adjustments request"""
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    userId: Optional[str] = Field(None, description="Filter by user ID")
    adjustmentType: Optional[str] = Field(None, description="Filter by adjustment type")
    status: Optional[str] = Field(None, description="Filter by status")
    sortBy: str = Field(default="createdAt", description="Sort field")
    sortOrder: str = Field(default="desc", description="Sort order")


class TradingAdjustmentsResponse(BaseModel):
    """Schema for trading adjustments response"""
    success: bool = Field(..., description="Operation success status")
    data: List[TradingAdjustment] = Field(..., description="Adjustment list")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")


# ========== USER PERFORMANCE SCHEMAS ==========

class UserPerformance(BaseModel):
    """Schema for user performance metrics"""
    userId: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    totalTrades: int = Field(..., description="Total number of trades")
    successfulTrades: int = Field(..., description="Successful trades")
    failedTrades: int = Field(..., description="Failed trades")
    totalVolume: float = Field(..., description="Total trading volume")
    averageTradeSize: float = Field(..., description="Average trade size")
    profitLoss: float = Field(..., description="Total profit/loss")
    winRate: float = Field(..., description="Win rate percentage")
    bestTrade: Optional[float] = Field(None, description="Best individual trade")
    worstTrade: Optional[float] = Field(None, description="Worst individual trade")
    firstTradeAt: Optional[datetime] = Field(None, description="First trade time")
    lastTradeAt: Optional[datetime] = Field(None, description="Last trade time")


class UserPerformanceRequest(BaseModel):
    """Schema for user performance request"""
    userId: str = Field(..., description="User ID")


class UserPerformanceResponse(BaseModel):
    """Schema for user performance response"""
    success: bool = Field(..., description="Operation success status")
    data: UserPerformance = Field(..., description="User performance data")


# ========== ADMIN ERROR SCHEMAS ==========

class AdminErrorResponse(BaseModel):
    """Schema for admin error responses"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class AdminValidationErrorResponse(BaseModel):
    """Schema for admin validation errors"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: List[Dict[str, Any]] = Field(..., description="Validation error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")