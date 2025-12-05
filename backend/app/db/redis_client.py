"""
Redis Client Module
Digital Utopia Platform

Quản lý kết nối Redis cho caching, session, và rate limiting
"""

import redis
import json
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import timedelta

from ..core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis Cache Client
    
    Cung cấp các phương thức để:
    - Cache dữ liệu với TTL
    - Quản lý session
    - Rate limiting
    - Publish/Subscribe cho real-time updates
    """
    
    def __init__(self):
        """Khởi tạo Redis connection"""
        self._client: Optional[redis.Redis] = None
        self._connected: bool = False
    
    def connect(self) -> bool:
        """
        Kết nối đến Redis server
        
        Returns:
            True nếu kết nối thành công
        """
        try:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,  # Auto decode bytes to string
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Could not connect to Redis: {e}. Running in memory-only mode.")
            self._connected = False
            return False
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            self._connected = False
            return False
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Lấy Redis client"""
        return self._client if self._connected else None
    
    @property
    def is_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối"""
        return self._connected
    
    # =============== Basic Operations ===============
    
    def get(self, key: str) -> Optional[str]:
        """
        Lấy giá trị từ cache
        
        Args:
            key: Cache key
            
        Returns:
            Giá trị hoặc None nếu không tồn tại
        """
        if not self._connected:
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu giá trị vào cache
        
        Args:
            key: Cache key
            value: Giá trị cần lưu
            ttl: Time to live (seconds)
            
        Returns:
            True nếu thành công
        """
        if not self._connected:
            return False
        try:
            if ttl:
                return self._client.setex(key, ttl, value)
            return self._client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Xóa key khỏi cache
        
        Args:
            key: Cache key
            
        Returns:
            True nếu xóa thành công
        """
        if not self._connected:
            return False
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Kiểm tra key có tồn tại không
        
        Args:
            key: Cache key
            
        Returns:
            True nếu tồn tại
        """
        if not self._connected:
            return False
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    # =============== JSON Operations ===============
    
    def get_json(self, key: str) -> Optional[Any]:
        """
        Lấy và parse JSON từ cache
        
        Args:
            key: Cache key
            
        Returns:
            Object Python hoặc None
        """
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_json(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Serialize và lưu JSON vào cache
        
        Args:
            key: Cache key
            value: Object Python
            ttl: Time to live (seconds)
            
        Returns:
            True nếu thành công
        """
        try:
            json_value = json.dumps(value, default=str)
            return self.set(key, json_value, ttl)
        except Exception as e:
            logger.error(f"Redis SET_JSON error: {e}")
            return False
    
    # =============== Session Management ===============
    
    def set_session(
        self, 
        session_id: str, 
        user_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu session user
        
        Args:
            session_id: Session ID
            user_data: Dữ liệu user
            ttl: Time to live (mặc định: 24h)
            
        Returns:
            True nếu thành công
        """
        key = f"session:{session_id}"
        ttl = ttl or settings.REDIS_SESSION_TTL
        return self.set_json(key, user_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Lấy session user
        
        Args:
            session_id: Session ID
            
        Returns:
            Dữ liệu user hoặc None
        """
        key = f"session:{session_id}"
        return self.get_json(key)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Xóa session user
        
        Args:
            session_id: Session ID
            
        Returns:
            True nếu xóa thành công
        """
        key = f"session:{session_id}"
        return self.delete(key)
    
    # =============== Rate Limiting ===============
    
    def check_rate_limit(
        self, 
        identifier: str, 
        limit: int, 
        window: int
    ) -> tuple[bool, int]:
        """
        Kiểm tra rate limit
        
        Args:
            identifier: ID để rate limit (IP, user_id, etc.)
            limit: Số request tối đa
            window: Thời gian window (seconds)
            
        Returns:
            (allowed: bool, remaining: int)
        """
        if not self._connected:
            return True, limit
        
        key = f"rate_limit:{identifier}"
        try:
            current = self._client.get(key)
            if current is None:
                self._client.setex(key, window, 1)
                return True, limit - 1
            
            current_count = int(current)
            if current_count >= limit:
                return False, 0
            
            self._client.incr(key)
            return True, limit - current_count - 1
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True, limit
    
    # =============== Market Data Caching ===============
    
    def cache_market_price(
        self, 
        symbol: str, 
        price_data: Dict[str, Any]
    ) -> bool:
        """
        Cache giá thị trường
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            price_data: Dữ liệu giá
            
        Returns:
            True nếu thành công
        """
        key = f"market:price:{symbol}"
        return self.set_json(key, price_data, settings.REDIS_MARKET_DATA_TTL)
    
    def get_market_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Lấy giá thị trường từ cache
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dữ liệu giá hoặc None
        """
        key = f"market:price:{symbol}"
        return self.get_json(key)
    
    def cache_order_book(
        self, 
        symbol: str, 
        order_book: Dict[str, Any]
    ) -> bool:
        """
        Cache order book
        
        Args:
            symbol: Trading symbol
            order_book: Dữ liệu order book
            
        Returns:
            True nếu thành công
        """
        key = f"market:orderbook:{symbol}"
        return self.set_json(key, order_book, settings.REDIS_MARKET_DATA_TTL)
    
    def get_order_book(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Lấy order book từ cache
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Order book hoặc None
        """
        key = f"market:orderbook:{symbol}"
        return self.get_json(key)
    
    # =============== User Cache ===============
    
    def cache_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        Cache user data
        
        Args:
            user_id: User ID
            user_data: Dữ liệu user
            
        Returns:
            True nếu thành công
        """
        key = f"user:{user_id}"
        return self.set_json(key, user_data, settings.REDIS_CACHE_TTL)
    
    def get_cached_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Lấy user data từ cache
        
        Args:
            user_id: User ID
            
        Returns:
            User data hoặc None
        """
        key = f"user:{user_id}"
        return self.get_json(key)
    
    def invalidate_user_cache(self, user_id: int) -> bool:
        """
        Xóa user khỏi cache
        
        Args:
            user_id: User ID
            
        Returns:
            True nếu xóa thành công
        """
        key = f"user:{user_id}"
        return self.delete(key)
    
    # =============== Portfolio Cache ===============
    
    def cache_portfolio(
        self, 
        user_id: int, 
        portfolio_data: Dict[str, Any]
    ) -> bool:
        """
        Cache portfolio data
        
        Args:
            user_id: User ID
            portfolio_data: Dữ liệu portfolio
            
        Returns:
            True nếu thành công
        """
        key = f"portfolio:{user_id}"
        return self.set_json(key, portfolio_data, settings.REDIS_CACHE_TTL)
    
    def get_cached_portfolio(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Lấy portfolio từ cache
        
        Args:
            user_id: User ID
            
        Returns:
            Portfolio data hoặc None
        """
        key = f"portfolio:{user_id}"
        return self.get_json(key)
    
    # =============== Cleanup ===============
    
    def flush_all(self) -> bool:
        """
        Xóa tất cả dữ liệu trong Redis
        CHỈ SỬ DỤNG TRONG TESTING!
        
        Returns:
            True nếu thành công
        """
        if not self._connected:
            return False
        try:
            self._client.flushdb()
            logger.warning("Redis database flushed!")
            return True
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False
    
    def close(self):
        """Đóng kết nối Redis"""
        if self._client:
            self._client.close()
            self._connected = False
            logger.info("Redis connection closed")


# =============== Global Redis Client ===============
redis_client = RedisCache()


def get_redis() -> RedisCache:
    """
    Dependency injection cho Redis client
    
    Sử dụng:
        @router.get("/data")
        def get_data(cache: RedisCache = Depends(get_redis)):
            return cache.get("key")
    """
    return redis_client


def init_redis() -> bool:
    """
    Khởi tạo Redis connection
    Gọi trong startup của ứng dụng
    
    Returns:
        True nếu kết nối thành công
    """
    return redis_client.connect()
