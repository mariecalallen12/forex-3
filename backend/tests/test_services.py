"""
Unit Tests cho Services
Digital Utopia Platform

Test các business logic services
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

# Import services
import sys
sys.path.insert(0, '/home/runner/work/forex-3/forex-3/backend')

from app.services.user_service import UserService
from app.services.trading_service import TradingService
from app.services.financial_service import FinancialService
from app.services.cache_service import CacheService


class TestUserService:
    """Test cases cho UserService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_cache = Mock()
        self.service = UserService(self.mock_db, self.mock_cache)
    
    def test_get_by_id_from_cache(self):
        """Test lấy user từ cache"""
        # Setup
        cached_user = {
            "id": 1,
            "email": "test@example.com",
            "status": "active"
        }
        self.mock_cache.get_cached_user.return_value = cached_user
        
        # Execute
        result = self.service.get_by_id(1)
        
        # Verify
        self.mock_cache.get_cached_user.assert_called_once_with(1)
        assert result is not None
    
    def test_get_by_id_from_database(self):
        """Test lấy user từ database khi không có trong cache"""
        # Setup
        self.mock_cache.get_cached_user.return_value = None
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Execute
        result = self.service.get_by_id(1)
        
        # Verify
        assert result == mock_user
        self.mock_db.query.assert_called()
    
    def test_get_by_email(self):
        """Test lấy user theo email"""
        # Setup
        mock_user = Mock()
        mock_user.email = "test@example.com"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Execute
        result = self.service.get_by_email("test@example.com")
        
        # Verify
        assert result == mock_user
    
    def test_authenticate_success(self):
        """Test xác thực thành công"""
        # Setup
        mock_user = Mock()
        mock_user.password_hash = "$2b$12$test"
        mock_user.failed_login_attempts = 0
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.user_service.verify_password', return_value=True):
            # Execute
            result = self.service.authenticate("test@example.com", "password")
            
            # Verify
            assert result == mock_user
            assert mock_user.failed_login_attempts == 0
    
    def test_authenticate_wrong_password(self):
        """Test xác thực thất bại do sai mật khẩu"""
        # Setup
        mock_user = Mock()
        mock_user.password_hash = "$2b$12$test"
        mock_user.failed_login_attempts = 0
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.user_service.verify_password', return_value=False):
            # Execute
            result = self.service.authenticate("test@example.com", "wrongpassword")
            
            # Verify
            assert result is None
            assert mock_user.failed_login_attempts == 1


class TestTradingService:
    """Test cases cho TradingService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_cache = Mock()
        self.service = TradingService(self.mock_db, self.mock_cache)
    
    def test_create_order(self):
        """Test tạo order mới"""
        # Setup
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        # Execute
        result = self.service.create_order(
            user_id=1,
            symbol="BTCUSDT",
            side="buy",
            order_type="market",
            quantity=Decimal("0.1")
        )
        
        # Verify
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        assert result is not None
    
    def test_cancel_order_success(self):
        """Test hủy order thành công"""
        # Setup
        mock_order = Mock()
        mock_order.id = 1
        mock_order.user_id = 1
        mock_order.status = "pending"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_order
        
        # Execute
        result = self.service.cancel_order(1, 1)
        
        # Verify
        assert result == mock_order
        assert mock_order.status == "cancelled"
    
    def test_cancel_order_not_found(self):
        """Test hủy order không tồn tại"""
        # Setup
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Execute
        result = self.service.cancel_order(999, 1)
        
        # Verify
        assert result is None


class TestFinancialService:
    """Test cases cho FinancialService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_cache = Mock()
        self.service = FinancialService(self.mock_db, self.mock_cache)
    
    def test_get_balance(self):
        """Test lấy balance"""
        # Setup
        mock_balance = Mock()
        mock_balance.available_balance = Decimal("1000")
        mock_balance.locked_balance = Decimal("100")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        # Execute
        result = self.service.get_balance(1, "USD")
        
        # Verify
        assert result == mock_balance
    
    def test_create_transaction(self):
        """Test tạo transaction"""
        # Setup
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()
        
        mock_balance = Mock()
        mock_balance.total_balance = Decimal("1000")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        # Execute
        result = self.service.create_transaction(
            user_id=1,
            transaction_type="deposit",
            asset="USD",
            amount=Decimal("500"),
            description="Test deposit"
        )
        
        # Verify
        self.mock_db.add.assert_called_once()
        assert result is not None
    
    def test_lock_balance_success(self):
        """Test lock balance thành công"""
        # Setup
        mock_balance = Mock()
        mock_balance.available_balance = Decimal("1000")
        mock_balance.locked_balance = Decimal("0")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        # Execute
        result = self.service.lock_balance(1, "USD", Decimal("500"))
        
        # Verify
        assert result is True
        assert mock_balance.available_balance == Decimal("500")
        assert mock_balance.locked_balance == Decimal("500")
    
    def test_lock_balance_insufficient(self):
        """Test lock balance không đủ"""
        # Setup
        mock_balance = Mock()
        mock_balance.available_balance = Decimal("100")
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        # Execute
        result = self.service.lock_balance(1, "USD", Decimal("500"))
        
        # Verify
        assert result is False


class TestCacheService:
    """Test cases cho CacheService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_cache = Mock()
        self.mock_cache.is_connected = True
        self.service = CacheService(self.mock_cache)
    
    def test_cache_user(self):
        """Test cache user data"""
        # Setup
        user_data = {"id": 1, "email": "test@example.com"}
        self.mock_cache.cache_user.return_value = True
        
        # Execute
        result = self.service.cache_user(1, user_data)
        
        # Verify
        self.mock_cache.cache_user.assert_called_once_with(1, user_data)
        assert result is True
    
    def test_get_user_from_cache(self):
        """Test lấy user từ cache"""
        # Setup
        cached_data = {"id": 1, "email": "test@example.com"}
        self.mock_cache.get_cached_user.return_value = cached_data
        
        # Execute
        result = self.service.get_user(1)
        
        # Verify
        assert result == cached_data
    
    def test_check_rate_limit_allowed(self):
        """Test rate limit còn cho phép"""
        # Setup
        self.mock_cache.check_rate_limit.return_value = (True, 59)
        
        # Execute
        allowed, remaining = self.service.check_rate_limit("user:1", 60, 60)
        
        # Verify
        assert allowed is True
        assert remaining == 59
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit đã vượt quá"""
        # Setup
        self.mock_cache.check_rate_limit.return_value = (False, 0)
        
        # Execute
        allowed, remaining = self.service.check_rate_limit("user:1", 60, 60)
        
        # Verify
        assert allowed is False
        assert remaining == 0
    
    def test_generate_cache_key(self):
        """Test tạo cache key"""
        # Execute
        key = CacheService.generate_cache_key("user", 1, "profile")
        
        # Verify
        assert key == "user:1:profile"
    
    def test_generate_cache_key_with_kwargs(self):
        """Test tạo cache key với kwargs"""
        # Execute
        key = CacheService.generate_cache_key("orders", status="pending", limit=10)
        
        # Verify
        assert "orders" in key
        assert "status=pending" in key
        assert "limit=10" in key


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
