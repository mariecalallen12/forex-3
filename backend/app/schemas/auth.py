from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# ========== AUTH REQUEST SCHEMAS ==========

class LoginRequest(BaseModel):
    """Schema cho request đăng nhập - tương tự Next.js loginSchema"""
    email: str = Field(..., description="Email đăng nhập")
    password: str = Field(min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")


class RegisterRequest(BaseModel):
    """Schema cho request đăng ký - tương tự Next.js registerSchema"""
    email: str = Field(..., description="Email đăng ký")
    password: str = Field(min_length=6, description="Mật khẩu (tối thiểu 6 ký tự)")
    displayName: str = Field(min_length=2, description="Tên hiển thị (tối thiểu 2 ký tự)")
    phoneNumber: Optional[str] = Field(None, description="Số điện thoại")
    agreeToTerms: bool = Field(..., description="Đồng ý điều khoản sử dụng")
    referralCode: Optional[str] = Field(None, description="Mã giới thiệu")


class RefreshTokenRequest(BaseModel):
    """Schema cho request làm mới token"""
    pass


# ========== AUTH RESPONSE SCHEMAS ==========

class UserData(BaseModel):
    """Schema cho dữ liệu người dùng - tương tự Next.js userData"""
    uid: str = Field(..., description="User ID từ Firebase")
    email: str = Field(..., description="Email người dùng")
    emailVerified: bool = Field(..., description="Email đã được xác thực")
    displayName: Optional[str] = Field(None, description="Tên hiển thị")
    photoURL: Optional[str] = Field(None, description="URL avatar")
    disabled: bool = Field(..., description="Tài khoản bị vô hiệu hóa")


class LoginResponse(BaseModel):
    """Schema cho response đăng nhập - tương tự Next.js response"""
    success: bool = Field(..., description="Trạng thái thành công")
    message: str = Field(..., description="Thông báo")
    data: Dict[str, Any] = Field(..., description="Dữ liệu trả về")


class RegisterResponse(BaseModel):
    """Schema cho response đăng ký - tương tự Next.js response"""
    success: bool = Field(..., description="Trạng thái thành công")
    message: str = Field(..., description="Thông báo")
    data: Dict[str, Any] = Field(..., description="Dữ liệu trả về")
    needsApproval: bool = Field(..., description="Cần phê duyệt")


class VerifyTokenResponse(BaseModel):
    """Schema cho response xác thực token"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: Dict[str, Any] = Field(..., description="Dữ liệu trả về")


class RefreshTokenResponse(BaseModel):
    """Schema cho response làm mới token"""
    success: bool = Field(..., description="Trạng thái thành công")
    message: str = Field(..., description="Thông báo")
    data: Dict[str, Any] = Field(..., description="Dữ liệu trả về")


class LogoutResponse(BaseModel):
    """Schema cho response đăng xuất"""
    success: bool = Field(..., description="Trạng thái thành công")
    message: str = Field(..., description="Thông báo")


# ========== ERROR RESPONSE SCHEMAS ==========

class AuthErrorResponse(BaseModel):
    """Schema cho response lỗi authentication"""
    success: bool = Field(False, description="Trạng thái thất bại")
    error: str = Field(..., description="Thông báo lỗi")
    details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi")


class ValidationErrorResponse(BaseModel):
    """Schema cho response lỗi validation"""
    success: bool = Field(False, description="Trạng thái thất bại")
    error: str = Field(..., description="Thông báo lỗi")
    details: Optional[Dict[str, Any]] = Field(None, description="Chi tiết lỗi")


class ReferralErrorResponse(BaseModel):
    """Schema cho response lỗi referral"""
    success: bool = Field(False, description="Trạng thái thất bại")
    error: str = Field(..., description="Thông báo lỗi")
    requiresReferral: bool = Field(True, description="Cần mã giới thiệu")
    referralError: bool = Field(True, description="Lỗi referral")


# ========== ADDITIONAL DATA SCHEMAS ==========

class TradingSettings(BaseModel):
    """Schema cho cài đặt giao dịch - tương tự Next.js tradingSettings"""
    preferredLanguage: str = Field(default="vi", description="Ngôn ngữ ưa thích")
    theme: str = Field(default="dark", description="Giao diện")
    notifications: Dict[str, bool] = Field(..., description="Cài đặt thông báo")


class Balance(BaseModel):
    """Schema cho số dư ví - tương tự Next.js balance"""
    usdt: float = Field(default=0.0, description="Số dư USDT")
    btc: float = Field(default=0.0, description="Số dư BTC")
    eth: float = Field(default=0.0, description="Số dư ETH")


class Statistics(BaseModel):
    """Schema cho thống kê - tương tự Next.js statistics"""
    totalDeposit: float = Field(default=0.0, description="Tổng nạp tiền")
    totalWithdraw: float = Field(default=0.0, description="Tổng rút tiền")
    totalTradingVolume: float = Field(default=0.0, description="Tổng khối lượng giao dịch")
    totalTrades: int = Field(default=0, description="Tổng số giao dịch")
    winRate: float = Field(default=0.0, description="Tỷ lệ thắng")
    profitLoss: float = Field(default=0.0, description="Lợi nhuận/thua lỗ")


class ReferralData(BaseModel):
    """Schema cho dữ liệu giới thiệu - tương tự Next.js referralData"""
    sourceRefType: str = Field(..., description="Loại giới thiệu")
    sourceRefCode: Optional[str] = Field(None, description="Mã giới thiệu")
    sourceRefStaffId: Optional[str] = Field(None, description="ID nhân viên")
    sourceRefStaffName: Optional[str] = Field(None, description="Tên nhân viên")


class UserProfile(BaseModel):
    """Schema cho profile người dùng đầy đủ - tương tự Next.js userData"""
    uid: str = Field(..., description="User ID")
    email: str = Field(..., description="Email")
    displayName: str = Field(..., description="Tên hiển thị")
    phoneNumber: Optional[str] = Field(None, description="Số điện thoại")
    avatar: Optional[str] = Field(None, description="URL avatar")
    role: str = Field(default="customer", description="Vai trò")
    status: str = Field(default="active", description="Trạng thái")
    isActive: bool = Field(default=True, description="Hoạt động")
    isEmailVerified: bool = Field(default=False, description="Email đã xác thực")
    isPhoneVerified: bool = Field(default=False, description="SĐT đã xác thực")
    kycStatus: str = Field(default="pending", description="Trạng thái KYC")
    approvalStatus: str = Field(default="pending", description="Trạng thái phê duyệt")
    registrationId: Optional[str] = Field(None, description="ID đăng ký")
    referralData: Optional[ReferralData] = Field(None, description="Dữ liệu giới thiệu")
    balance: Balance = Field(default_factory=Balance, description="Số dư ví")
    tradingSettings: TradingSettings = Field(default_factory=TradingSettings, description="Cài đặt giao dịch")
    statistics: Statistics = Field(default_factory=Statistics, description="Thống kê")
    lastLogin: Optional[datetime] = Field(None, description="Lần đăng nhập cuối")
    createdAt: datetime = Field(..., description="Ngày tạo")
    updatedAt: datetime = Field(..., description="Ngày cập nhật")


# ========== RATE LIMITING SCHEMAS ==========

class RateLimitInfo(BaseModel):
    """Schema cho thông tin rate limiting"""
    client_ip: str = Field(..., description="IP client")
    endpoint: str = Field(..., description="Endpoint")
    current_requests: int = Field(..., description="Số request hiện tại")
    max_requests: int = Field(..., description="Số request tối đa")
    window_seconds: int = Field(..., description="Thời gian cửa sổ (giây)")


# ========== EMAIL SCHEMAS ==========

class EmailData(BaseModel):
    """Schema cho dữ liệu email - tương tự Next.js sendEmail"""
    to: str = Field(..., description="Email nhận")
    template: str = Field(..., description="Template email")
    subject: str = Field(..., description="Tiêu đề email")
    data: Dict[str, Any] = Field(..., description="Dữ liệu email")


# ========== REQUEST HEADERS ==========

class AuthHeaders(BaseModel):
    """Schema cho headers xác thực"""
    authorization: Optional[str] = Field(None, description="Authorization header")
    x_forwarded_for: Optional[str] = Field(None, description="Client IP")


# ========== HEALTH CHECK ==========

class HealthCheckResponse(BaseModel):
    """Schema cho response health check - tương tự Next.js"""
    status: str = Field(..., description="Trạng thái")
    service: str = Field(..., description="Tên service")
    version: str = Field(..., description="Phiên bản")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Thời gian kiểm tra")
