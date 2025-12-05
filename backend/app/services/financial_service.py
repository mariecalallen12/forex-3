"""
Financial Service
Digital Utopia Platform

Business logic cho Financial operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from decimal import Decimal
import logging
from datetime import datetime
import uuid

from ..models.financial import Transaction, WalletBalance, ExchangeRate
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)


class FinancialService:
    """
    Service class cho Financial operations
    
    Cung cấp business logic cho:
    - Transaction management
    - Wallet balance management
    - Exchange rates
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo FinancialService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== Wallet Balance ===============
    
    def get_balance(self, user_id: int, asset: str) -> Optional[WalletBalance]:
        """
        Lấy số dư của một asset
        
        Args:
            user_id: User ID
            asset: Asset code (USD, VND, BTC, etc.)
            
        Returns:
            WalletBalance hoặc None
        """
        return self.db.query(WalletBalance).filter(
            and_(
                WalletBalance.user_id == user_id,
                WalletBalance.asset == asset.upper()
            )
        ).first()
    
    def get_all_balances(self, user_id: int) -> List[WalletBalance]:
        """
        Lấy tất cả số dư của user
        
        Args:
            user_id: User ID
            
        Returns:
            Danh sách WalletBalance
        """
        return self.db.query(WalletBalance).filter(
            WalletBalance.user_id == user_id
        ).all()
    
    def create_or_update_balance(
        self,
        user_id: int,
        asset: str,
        available_delta: Decimal = Decimal("0"),
        locked_delta: Decimal = Decimal("0")
    ) -> WalletBalance:
        """
        Tạo hoặc cập nhật balance
        
        Args:
            user_id: User ID
            asset: Asset code
            available_delta: Thay đổi available balance
            locked_delta: Thay đổi locked balance
            
        Returns:
            WalletBalance
        """
        balance = self.get_balance(user_id, asset)
        
        if balance:
            balance.available_balance = (balance.available_balance or 0) + available_delta
            balance.locked_balance = (balance.locked_balance or 0) + locked_delta
        else:
            balance = WalletBalance(
                user_id=user_id,
                asset=asset.upper(),
                available_balance=max(Decimal("0"), available_delta),
                locked_balance=max(Decimal("0"), locked_delta)
            )
            self.db.add(balance)
        
        self.db.commit()
        self.db.refresh(balance)
        
        return balance
    
    def lock_balance(
        self,
        user_id: int,
        asset: str,
        amount: Decimal
    ) -> bool:
        """
        Lock balance (chuyển từ available sang locked)
        
        Args:
            user_id: User ID
            asset: Asset code
            amount: Số tiền lock
            
        Returns:
            True nếu thành công
        """
        balance = self.get_balance(user_id, asset)
        if not balance:
            return False
        
        if balance.available_balance < amount:
            return False
        
        balance.available_balance -= amount
        balance.locked_balance += amount
        self.db.commit()
        
        return True
    
    def unlock_balance(
        self,
        user_id: int,
        asset: str,
        amount: Decimal
    ) -> bool:
        """
        Unlock balance (chuyển từ locked về available)
        
        Args:
            user_id: User ID
            asset: Asset code
            amount: Số tiền unlock
            
        Returns:
            True nếu thành công
        """
        balance = self.get_balance(user_id, asset)
        if not balance:
            return False
        
        if balance.locked_balance < amount:
            return False
        
        balance.locked_balance -= amount
        balance.available_balance += amount
        self.db.commit()
        
        return True
    
    # =============== Transactions ===============
    
    def create_transaction(
        self,
        user_id: int,
        transaction_type: str,
        asset: str,
        amount: Decimal,
        fee: Decimal = Decimal("0"),
        category: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Transaction:
        """
        Tạo transaction mới
        
        Args:
            user_id: User ID
            transaction_type: deposit/withdrawal/transfer/fee/trading
            asset: Asset code
            amount: Số tiền
            fee: Phí
            category: Phân loại chi tiết
            description: Mô tả
            metadata: Thông tin bổ sung
            
        Returns:
            Transaction mới
        """
        # Get current balance
        balance = self.get_balance(user_id, asset)
        balance_before = balance.total_balance if balance else Decimal("0")
        
        net_amount = amount - fee
        
        transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            category=category,
            asset=asset.upper(),
            amount=amount,
            fee=fee,
            net_amount=net_amount,
            balance_before=balance_before,
            status="pending",
            description=description,
            reference_id=str(uuid.uuid4())[:12].upper(),
            metadata=metadata or {}
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Transaction created: {transaction.id} ({transaction_type} {amount} {asset})")
        return transaction
    
    def complete_transaction(
        self,
        transaction_id: int,
        external_id: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Hoàn thành transaction
        
        Args:
            transaction_id: Transaction ID
            external_id: ID từ hệ thống bên ngoài
            
        Returns:
            Transaction đã hoàn thành
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return None
        
        if transaction.status != "pending":
            return transaction
        
        # Update balance based on transaction type
        if transaction.transaction_type == "deposit":
            self.create_or_update_balance(
                transaction.user_id,
                transaction.asset,
                available_delta=transaction.net_amount
            )
        elif transaction.transaction_type == "withdrawal":
            # Withdrawal: reduce locked balance
            balance = self.get_balance(transaction.user_id, transaction.asset)
            if balance:
                balance.locked_balance -= transaction.amount
                self.db.commit()
        
        # Update transaction
        transaction.status = "completed"
        transaction.completed_at = datetime.utcnow()
        if external_id:
            transaction.external_id = external_id
        
        # Update balance_after
        balance = self.get_balance(transaction.user_id, transaction.asset)
        transaction.balance_after = balance.total_balance if balance else Decimal("0")
        
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Transaction completed: {transaction_id}")
        return transaction
    
    def cancel_transaction(
        self,
        transaction_id: int,
        reason: Optional[str] = None
    ) -> Optional[Transaction]:
        """
        Hủy transaction
        
        Args:
            transaction_id: Transaction ID
            reason: Lý do hủy
            
        Returns:
            Transaction đã hủy
        """
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
        
        if not transaction:
            return None
        
        if transaction.status != "pending":
            return transaction
        
        # Refund locked balance for withdrawals
        if transaction.transaction_type == "withdrawal":
            self.unlock_balance(
                transaction.user_id,
                transaction.asset,
                transaction.amount
            )
        
        transaction.status = "cancelled"
        transaction.cancelled_at = datetime.utcnow()
        if reason:
            transaction.failed_reason = reason
        
        self.db.commit()
        self.db.refresh(transaction)
        
        logger.info(f"Transaction cancelled: {transaction_id}")
        return transaction
    
    def get_user_transactions(
        self,
        user_id: int,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        asset: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """
        Lấy danh sách transactions của user
        
        Args:
            user_id: User ID
            transaction_type: Filter theo type
            status: Filter theo status
            asset: Filter theo asset
            limit: Số transactions tối đa
            
        Returns:
            Danh sách transactions
        """
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        if status:
            query = query.filter(Transaction.status == status)
        if asset:
            query = query.filter(Transaction.asset == asset.upper())
        
        return query.order_by(desc(Transaction.created_at)).limit(limit).all()
    
    # =============== Exchange Rates ===============
    
    def get_exchange_rate(self, base: str, target: str) -> Optional[ExchangeRate]:
        """
        Lấy tỷ giá
        
        Args:
            base: Base asset
            target: Target asset
            
        Returns:
            ExchangeRate hoặc None
        """
        # Check cache first
        if self.cache:
            cache_key = f"exchange_rate:{base}:{target}"
            cached = self.cache.get_json(cache_key)
            if cached:
                return ExchangeRate(**cached)
        
        rate = self.db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.base_asset == base.upper(),
                ExchangeRate.target_asset == target.upper(),
                ExchangeRate.is_active == True
            )
        ).first()
        
        # Cache result
        if rate and self.cache:
            self.cache.set_json(
                f"exchange_rate:{base}:{target}",
                {
                    "base_asset": rate.base_asset,
                    "target_asset": rate.target_asset,
                    "rate": float(rate.rate)
                },
                ttl=300  # 5 minutes
            )
        
        return rate
    
    def get_all_exchange_rates(self) -> List[ExchangeRate]:
        """Lấy tất cả tỷ giá"""
        return self.db.query(ExchangeRate).filter(
            ExchangeRate.is_active == True
        ).order_by(ExchangeRate.priority).all()
    
    def update_exchange_rate(
        self,
        base: str,
        target: str,
        rate: Decimal,
        source: str = "internal"
    ) -> ExchangeRate:
        """
        Cập nhật hoặc tạo tỷ giá
        
        Args:
            base: Base asset
            target: Target asset
            rate: Tỷ giá mới
            source: Nguồn dữ liệu
            
        Returns:
            ExchangeRate
        """
        exchange_rate = self.db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.base_asset == base.upper(),
                ExchangeRate.target_asset == target.upper()
            )
        ).first()
        
        if exchange_rate:
            exchange_rate.rate = rate
            exchange_rate.inverse_rate = Decimal("1") / rate if rate > 0 else None
            exchange_rate.source = source
        else:
            exchange_rate = ExchangeRate(
                base_asset=base.upper(),
                target_asset=target.upper(),
                rate=rate,
                inverse_rate=Decimal("1") / rate if rate > 0 else None,
                source=source,
                is_active=True
            )
            self.db.add(exchange_rate)
        
        self.db.commit()
        self.db.refresh(exchange_rate)
        
        # Invalidate cache
        if self.cache:
            self.cache.delete(f"exchange_rate:{base}:{target}")
        
        return exchange_rate
    
    def convert_amount(
        self,
        amount: Decimal,
        from_asset: str,
        to_asset: str
    ) -> Optional[Decimal]:
        """
        Chuyển đổi tiền tệ
        
        Args:
            amount: Số tiền
            from_asset: Từ asset
            to_asset: Sang asset
            
        Returns:
            Số tiền đã chuyển đổi hoặc None nếu không có tỷ giá
        """
        if from_asset.upper() == to_asset.upper():
            return amount
        
        rate = self.get_exchange_rate(from_asset, to_asset)
        if rate:
            return amount * rate.rate
        
        # Try inverse
        rate = self.get_exchange_rate(to_asset, from_asset)
        if rate and rate.rate > 0:
            return amount / rate.rate
        
        return None
