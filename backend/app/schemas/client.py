"""
Client Module Schemas - Migration từ Next.js
Bao gồm tất cả schemas cho client endpoints: dashboard, wallet, transactions, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# ========== DASHBOARD SCHEMAS ==========

class WalletBalance(BaseModel):
    """Schema cho số dư ví - tương tự Next.js WalletBalance"""
    userId: str = Field(..., description="User ID")
    asset: str = Field(..., description="Loại tài sản (VND, USD, BTC, etc.)")
    totalBalance: float = Field(default=0, description="Tổng số dư")
    availableBalance: float = Field(default=0, description="Số dư khả dụng")
    lockedBalance: float = Field(default=0, description="Số dư bị khóa")
    pendingBalance: float = Field(default=0, description="Số dư đang xử lý")
    reservedBalance: float = Field(default=0, description="Số dư được dành riêng")
    lastUpdated: datetime = Field(default_factory=datetime.now, description="Lần cập nhật cuối")
    isActive: bool = Field(default=True, description="Trạng thái hoạt động")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")


class TransactionHistory(BaseModel):
    """Schema cho lịch sử giao dịch - tương tự Next.js TransactionHistory"""
    id: str = Field(..., description="Transaction ID")
    userId: str = Field(..., description="User ID")
    type: str = Field(..., description="Loại giao dịch (deposit, withdrawal, trading)")
    category: str = Field(..., description="Danh mục giao dịch")
    status: str = Field(..., description="Trạng thái (pending, completed, failed)")
    amount: float = Field(..., description="Số lượng")
    currency: str = Field(..., description="Đơn vị tiền tệ")
    fee: float = Field(default=0, description="Phí giao dịch")
    netAmount: float = Field(..., description="Số tiền thực nhận")
    description: Optional[str] = Field(None, description="Mô tả giao dịch")
    reference: Optional[str] = Field(None, description="Mã tham chiếu")
    externalReference: Optional[str] = Field(None, description="Mã tham chiếu bên ngoài")
    paymentMethod: Optional[str] = Field(None, description="Phương thức thanh toán")
    fromAddress: Optional[str] = Field(None, description="Địa chỉ gửi")
    toAddress: Optional[str] = Field(None, description="Địa chỉ nhận")
    bankDetails: Optional[Dict[str, Any]] = Field(None, description="Thông tin ngân hàng")
    blockchainNetwork: Optional[str] = Field(None, description="Mạng blockchain")
    confirmations: Optional[int] = Field(None, description="Số xác nhận")
    requiredConfirmations: Optional[int] = Field(None, description="Số xác nhận cần thiết")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")
    relatedId: Optional[str] = Field(None, description="ID liên quan")
    adminNotes: Optional[str] = Field(None, description="Ghi chú từ admin")
    createdAt: datetime = Field(default_factory=datetime.now, description="Thời gian tạo")
    updatedAt: Optional[datetime] = Field(None, description="Thời gian cập nhật")
    completedAt: Optional[datetime] = Field(None, description="Thời gian hoàn thành")


class DashboardOverview(BaseModel):
    """Schema cho tổng quan dashboard"""
    totalBalance: float = Field(..., description="Tổng số dư (USD)")
    availableBalance: float = Field(..., description="Số dư khả dụng (USD)")
    lockedBalance: float = Field(..., description="Số dư bị khóa (USD)")
    pendingDeposits: float = Field(default=0, description="Tiền nạp đang chờ")
    pendingWithdrawals: float = Field(default=0, description="Tiền rút đang chờ")
    recentActivity: List[TransactionHistory] = Field(default_factory=list, description="Hoạt động gần đây")


class DashboardStats(BaseModel):
    """Schema cho thống kê dashboard"""
    totalDeposits: float = Field(..., description="Tổng tiền nạp")
    totalWithdrawals: float = Field(..., description="Tổng tiền rút")
    netFlow: float = Field(..., description="Dòng tiền ròng")
    activeAssets: int = Field(..., description="Số tài sản hoạt động")
    largestDeposit: float = Field(..., description="Giao dịch nạp lớn nhất")
    largestWithdrawal: float = Field(..., description="Giao dịch rút lớn nhất")
    averageDeposit: float = Field(..., description="Giao dịch nạp trung bình")
    averageWithdrawal: float = Field(..., description="Giao dịch rút trung bình")
    depositCount: int = Field(..., description="Số giao dịch nạp")
    withdrawalCount: int = Field(..., description="Số giao dịch rút")
    lastDepositAt: Optional[datetime] = Field(None, description="Giao dịch nạp cuối cùng")
    lastWithdrawalAt: Optional[datetime] = Field(None, description="Giao dịch rút cuối cùng")


class FinancialDashboardData(BaseModel):
    """Schema cho dữ liệu dashboard tài chính - tương tự Next.js FinancialDashboardData"""
    userId: str = Field(..., description="User ID")
    overview: DashboardOverview = Field(..., description="Tổng quan dashboard")
    balances: List[WalletBalance] = Field(default_factory=list, description="Danh sách số dư")
    recentTransactions: List[TransactionHistory] = Field(default_factory=list, description="Giao dịch gần đây")
    stats: DashboardStats = Field(..., description="Thống kê chi tiết")
    riskScore: int = Field(..., description="Điểm rủi ro (0-100)")
    complianceStatus: str = Field(..., description="Trạng thái tuân thủ")
    lastUpdated: datetime = Field(default_factory=datetime.now, description="Lần cập nhật cuối")


class DashboardResponse(BaseModel):
    """Schema cho response dashboard"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: FinancialDashboardData = Field(..., description="Dữ liệu dashboard")
    exchangeRates: Dict[str, float] = Field(default_factory=dict, description="Tỷ giá hối đoái")


# ========== WALLET SCHEMAS ==========

class WalletBalancesRequest(BaseModel):
    """Schema cho request lấy số dư ví"""
    userId: Optional[str] = Field(None, description="User ID (nếu không cung cấp sẽ lấy từ token)")


class WalletBalanceResponse(BaseModel):
    """Schema cho response số dư ví"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: List[WalletBalance] = Field(..., description="Danh sách số dư ví")


# ========== TRANSACTIONS SCHEMAS ==========

class TransactionsRequest(BaseModel):
    """Schema cho request lấy danh sách giao dịch"""
    page: int = Field(default=1, ge=1, description="Trang hiện tại")
    limit: int = Field(default=20, ge=1, le=100, description="Số lượng mỗi trang")
    type: Optional[str] = Field(None, description="Lọc theo loại giao dịch")
    status: Optional[str] = Field(None, description="Lọc theo trạng thái")
    currency: Optional[str] = Field(None, description="Lọc theo đơn vị tiền tệ")
    startDate: Optional[datetime] = Field(None, description="Ngày bắt đầu")
    endDate: Optional[datetime] = Field(None, description="Ngày kết thúc")


class TransactionsResponse(BaseModel):
    """Schema cho response danh sách giao dịch"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: List[TransactionHistory] = Field(..., description="Danh sách giao dịch")
    pagination: Dict[str, Any] = Field(..., description="Thông tin phân trang")


# ========== EXCHANGE RATES SCHEMAS ==========

class ExchangeRate(BaseModel):
    """Schema cho tỷ giá hối đoái"""
    id: str = Field(..., description="Exchange Rate ID")
    baseAsset: str = Field(..., description="Tài sản gốc")
    targetAsset: str = Field(..., description="Tài sản đích")
    rate: float = Field(..., description="Tỷ giá")
    isActive: bool = Field(default=True, description="Trạng thái hoạt động")
    priority: int = Field(default=0, description="Độ ưu tiên hiển thị")
    lastUpdated: datetime = Field(default_factory=datetime.now, description="Lần cập nhật cuối")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata bổ sung")


class ExchangeRatesResponse(BaseModel):
    """Schema cho response tỷ giá hối đoái"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: List[ExchangeRate] = Field(..., description="Danh sách tỷ giá")


# ========== CRYPTO DEPOSIT SCHEMAS ==========

class CryptoDepositAddressRequest(BaseModel):
    """Schema cho request tạo địa chỉ nạp crypto"""
    currency: str = Field(..., description="Loại tiền crypto")
    network: Optional[str] = Field(None, description="Mạng blockchain")


class CryptoDepositAddress(BaseModel):
    """Schema cho địa chỉ nạp crypto"""
    address: str = Field(..., description="Địa chỉ nạp")
    currency: str = Field(..., description="Loại tiền crypto")
    network: str = Field(..., description="Mạng blockchain")
    qrCode: Optional[str] = Field(None, description="QR Code (base64)")
    memo: Optional[str] = Field(None, description="Memo/Tag (nếu có)")
    createdAt: datetime = Field(default_factory=datetime.now, description="Thời gian tạo")
    expiresAt: datetime = Field(..., description="Thời gian hết hạn")


class CryptoDepositAddressResponse(BaseModel):
    """Schema cho response địa chỉ nạp crypto"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: CryptoDepositAddress = Field(..., description="Dữ liệu địa chỉ nạp")


# ========== VIETQR SCHEMAS ==========

class GenerateVietQRRequest(BaseModel):
    """Schema cho request tạo VietQR"""
    amount: float = Field(..., gt=0, description="Số tiền thanh toán")
    description: str = Field(..., description="Mô tả thanh toán")
    orderId: Optional[str] = Field(None, description="Mã đơn hàng")


class VietQRResponse(BaseModel):
    """Schema cho response VietQR"""
    success: bool = Field(..., description="Trạng thái thành công")
    data: Dict[str, Any] = Field(..., description="Dữ liệu VietQR")
    qrCode: str = Field(..., description="QR Code (base64)")
    paymentUrl: str = Field(..., description="URL thanh toán")


# ========== ERROR SCHEMAS ==========

class ClientErrorResponse(BaseModel):
    """Schema cho response lỗi client endpoints"""
    success: bool = Field(default=False, description="Trạng thái thành công")
    error: str = Field(..., description="Thông báo lỗi")
    code: Optional[str] = Field(None, description="Mã lỗi")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian lỗi")


class ValidationErrorResponse(BaseModel):
    """Schema cho response lỗi validation"""
    success: bool = Field(default=False, description="Trạng thái thành công")
    error: str = Field(..., description="Thông báo lỗi")
    validationErrors: List[Dict[str, Any]] = Field(..., description="Chi tiết lỗi validation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Thời gian lỗi")