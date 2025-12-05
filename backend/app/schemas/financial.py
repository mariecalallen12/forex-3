"""
Financial Module Schemas - Migration từ Next.js
Bao gồm: deposits, withdrawals với đầy đủ validation logic
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

# ========== DEPOSIT SCHEMAS ==========

class Currency(str, Enum):
    """Supported currencies"""
    USDT = "usdt"
    BTC = "btc"
    ETH = "eth"


class PaymentMethod(str, Enum):
    """Payment methods"""
    BANK_TRANSFER = "bank_transfer"
    CRYPTO_DEPOSIT = "crypto_deposit"
    CARD = "card"


class BankAccount(BaseModel):
    """Bank account details"""
    accountNumber: str = Field(..., description="Account number")
    accountName: str = Field(..., description="Account holder name")
    bankName: str = Field(..., description="Bank name")


class CreateDepositRequest(BaseModel):
    """Schema for creating deposit request"""
    amount: float = Field(..., gt=0, description="Deposit amount")
    currency: Currency = Field(..., description="Deposit currency")
    method: PaymentMethod = Field(..., description="Payment method")
    bankAccount: Optional[BankAccount] = Field(None, description="Bank account details")
    walletAddress: Optional[str] = Field(None, description="Crypto wallet address")
    transactionId: Optional[str] = Field(None, description="Transaction ID")
    notes: Optional[str] = Field(None, description="Additional notes")


class DepositRecord(BaseModel):
    """Schema for deposit record"""
    id: str = Field(..., description="Deposit ID")
    userId: str = Field(..., description="User ID")
    userEmail: str = Field(..., description="User email")
    amount: float = Field(..., description="Deposit amount")
    currency: str = Field(..., description="Currency")
    method: str = Field(..., description="Payment method")
    status: str = Field(..., description="Deposit status")
    fees: float = Field(default=0, description="Processing fees")
    netAmount: float = Field(..., description="Net amount after fees")
    bankAccount: Optional[Dict[str, str]] = Field(None, description="Bank account details")
    walletAddress: Optional[str] = Field(None, description="Crypto wallet address")
    transactionId: Optional[str] = Field(None, description="Transaction ID")
    notes: Optional[str] = Field(None, description="Additional notes")
    processedBy: Optional[str] = Field(None, description="Admin who processed")
    processedAt: Optional[datetime] = Field(None, description="Processing time")
    rejectReason: Optional[str] = Field(None, description="Rejection reason")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    updatedAt: datetime = Field(default_factory=datetime.now, description="Last update time")


class Invoice(BaseModel):
    """Schema for invoice record"""
    id: str = Field(..., description="Invoice ID")
    userId: str = Field(..., description="User ID")
    userEmail: str = Field(..., description="User email")
    type: str = Field(..., description="Invoice type")
    status: str = Field(..., description="Invoice status")
    amount: float = Field(..., description="Invoice amount")
    currency: str = Field(..., description="Currency")
    description: str = Field(..., description="Invoice description")
    depositId: Optional[str] = Field(None, description="Related deposit ID")
    withdrawalId: Optional[str] = Field(None, description="Related withdrawal ID")
    dueDate: Optional[datetime] = Field(None, description="Due date")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    updatedAt: datetime = Field(default_factory=datetime.now, description="Last update time")


class DepositResponse(BaseModel):
    """Schema for deposit response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Dict[str, Any] = Field(..., description="Response data")


class DepositsListResponse(BaseModel):
    """Schema for deposits list response"""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Response data")


# ========== WITHDRAWAL SCHEMAS ==========

class CreateWithdrawalRequest(BaseModel):
    """Schema for creating withdrawal request"""
    amount: float = Field(..., gt=0, description="Withdrawal amount")
    currency: Currency = Field(..., description="Withdrawal currency")
    method: PaymentMethod = Field(..., description="Withdrawal method")
    bankAccount: Optional[BankAccount] = Field(None, description="Bank account details")
    walletAddress: Optional[str] = Field(None, description="Crypto wallet address")
    notes: Optional[str] = Field(None, description="Additional notes")


class WithdrawalLimits(BaseModel):
    """Schema for withdrawal limits"""
    daily: float = Field(default=10000, description="Daily withdrawal limit")
    monthly: float = Field(default=100000, description="Monthly withdrawal limit")


class WithdrawalRecord(BaseModel):
    """Schema for withdrawal record"""
    id: str = Field(..., description="Withdrawal ID")
    userId: str = Field(..., description="User ID")
    userEmail: str = Field(..., description="User email")
    amount: float = Field(..., description="Withdrawal amount")
    currency: str = Field(..., description="Currency")
    method: str = Field(..., description="Withdrawal method")
    fee: float = Field(default=0, description="Processing fee")
    netAmount: float = Field(..., description="Net amount after fees")
    status: str = Field(..., description="Withdrawal status")
    bankAccount: Optional[Dict[str, str]] = Field(None, description="Bank account details")
    walletAddress: Optional[str] = Field(None, description="Crypto wallet address")
    notes: Optional[str] = Field(None, description="Additional notes")
    processedBy: Optional[str] = Field(None, description="Admin who processed")
    processedAt: Optional[datetime] = Field(None, description="Processing time")
    rejectReason: Optional[str] = Field(None, description="Rejection reason")
    createdAt: datetime = Field(default_factory=datetime.now, description="Creation time")
    updatedAt: datetime = Field(default_factory=datetime.now, description="Last update time")


class WithdrawalResponse(BaseModel):
    """Schema for withdrawal response"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Dict[str, Any] = Field(..., description="Response data")


class WithdrawalsListResponse(BaseModel):
    """Schema for withdrawals list response"""
    success: bool = Field(..., description="Operation success status")
    data: Dict[str, Any] = Field(..., description="Response data")


# ========== FINANCIAL ERROR SCHEMAS ==========

class FinancialErrorResponse(BaseModel):
    """Schema for financial error responses"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")
    code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class FinancialValidationErrorResponse(BaseModel):
    """Schema for financial validation errors"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: List[Dict[str, Any]] = Field(..., description="Validation error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")