"""
Staff Referral Management Schemas
Staff access to their referral codes and analytics
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ReferralStatus(str, Enum):
    """Status của referral code"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


class StaffInfo(BaseModel):
    """Thông tin staff"""
    staffId: str = Field(..., description="Staff ID duy nhất")
    displayName: str = Field(..., description="Tên hiển thị của staff")
    email: str = Field(..., description="Email của staff")


class ReferralCode(BaseModel):
    """Mã giới thiệu của staff"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str = Field(..., description="Mã giới thiệu duy nhất")
    status: ReferralStatus = Field(default=ReferralStatus.ACTIVE)
    usageCount: int = Field(default=0, description="Số lần sử dụng")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    staffId: str = Field(..., description="ID của staff tạo mã")


class ReferralAnalytics(BaseModel):
    """Analytics của referral"""
    totalReferrals: int = Field(default=0, description="Tổng số lượt giới thiệu")
    successfulReferrals: int = Field(default=0, description="Số lượt giới thiệu thành công")
    conversionRate: float = Field(default=0.0, description="Tỷ lệ chuyển đổi")
    totalRewards: float = Field(default=0.0, description="Tổng phần thưởng")
    thisMonth: int = Field(default=0, description="Số lượt giới thiệu tháng này")
    last30Days: int = Field(default=0, description="Số lượt giới thiệu 30 ngày gần đây")


class ReferralLink(BaseModel):
    """Link giới thiệu được tạo"""
    url: str = Field(..., description="URL của link giới thiệu")
    code: str = Field(..., description="Mã giới thiệu")
    expiresAt: datetime = Field(..., description="Thời hạn hết hạn")


class GenerateLinkRequest(BaseModel):
    """Request để tạo link giới thiệu"""
    expiryDays: int = Field(default=30, ge=1, le=365, description="Số ngày hết hạn")


class StaffReferralsResponse(BaseModel):
    """Response cho staff referrals"""
    analytics: ReferralAnalytics
    referralCodes: List[ReferralCode]
    staffInfo: StaffInfo


class GenerateLinkResponse(BaseModel):
    """Response cho tạo link"""
    message: str = Field(..., description="Thông báo thành công")
    data: ReferralLink


# Mock data functions for development
def get_mock_staff_info() -> StaffInfo:
    """Tạo mock staff info"""
    return StaffInfo(
        staffId="STAFF001",
        displayName="Staff Member",
        email="staff@example.com"
    )


def get_mock_referral_codes() -> List[ReferralCode]:
    """Tạo mock referral codes"""
    return [
        ReferralCode(
            id="ref_001",
            code="DUABC123",
            status=ReferralStatus.ACTIVE,
            usageCount=15
        )
    ]


def get_mock_referral_analytics() -> ReferralAnalytics:
    """Tạo mock referral analytics"""
    return ReferralAnalytics(
        totalReferrals=25,
        successfulReferrals=18,
        conversionRate=72.0,
        totalRewards=180.0,
        thisMonth=8,
        last30Days=12
    )