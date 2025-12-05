"""
Cache Service
Digital Utopia Platform

Service cho caching operations với Redis
"""

from typing import Optional, Any, Dict, List, Callable
from datetime import timedelta
import logging
import json
import hashlib

from ..db.redis_client import RedisCache, redis_client
from ..core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service class cho caching operations
    
    Cung cấp:
    - Cache decorator
    - Cache invalidation
    - Cache warming
    - Cache statistics
    """
    
    def __init__(self, cache: Optional[RedisCache] = None):
        """
        Khởi tạo CacheService
        
        Args:
            cache: Redis cache client
        """
        self.cache = cache or redis_client
    
    # =============== Cache Operations ===============
    
    def get(self, key: str) -> Optional[Any]:
        """
        Lấy giá trị từ cache
        
        Args:
            key: Cache key
            
        Returns:
            Giá trị hoặc None
        """
        return self.cache.get_json(key)
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Lưu giá trị vào cache
        
        Args:
            key: Cache key
            value: Giá trị
            ttl: Time to live (seconds)
            
        Returns:
            True nếu thành công
        """
        return self.cache.set_json(key, value, ttl or settings.REDIS_CACHE_TTL)
    
    def delete(self, key: str) -> bool:
        """
        Xóa giá trị từ cache
        
        Args:
            key: Cache key
            
        Returns:
            True nếu thành công
        """
        return self.cache.delete(key)
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Xóa tất cả keys matching pattern
        
        Args:
            pattern: Pattern to match (e.g., "user:*")
            
        Returns:
            Số keys đã xóa
        """
        if not self.cache.is_connected:
            return 0
        
        try:
            keys = self.cache.client.keys(pattern)
            if keys:
                return self.cache.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Delete pattern error: {e}")
            return 0
    
    # =============== User Cache ===============
    
    def cache_user(self, user_id: int, user_data: Dict) -> bool:
        """Cache user data"""
        return self.cache.cache_user(user_id, user_data)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get cached user"""
        return self.cache.get_cached_user(user_id)
    
    def invalidate_user(self, user_id: int) -> bool:
        """Invalidate user cache"""
        return self.cache.invalidate_user_cache(user_id)
    
    # =============== Portfolio Cache ===============
    
    def cache_portfolio(self, user_id: int, portfolio_data: Dict) -> bool:
        """Cache portfolio data"""
        return self.cache.cache_portfolio(user_id, portfolio_data)
    
    def get_portfolio(self, user_id: int) -> Optional[Dict]:
        """Get cached portfolio"""
        return self.cache.get_cached_portfolio(user_id)
    
    def invalidate_portfolio(self, user_id: int) -> bool:
        """Invalidate portfolio cache"""
        return self.cache.delete(f"portfolio:{user_id}")
    
    # =============== Market Data Cache ===============
    
    def cache_price(self, symbol: str, price_data: Dict) -> bool:
        """Cache market price"""
        return self.cache.cache_market_price(symbol, price_data)
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """Get cached price"""
        return self.cache.get_market_price(symbol)
    
    def cache_orderbook(self, symbol: str, orderbook: Dict) -> bool:
        """Cache orderbook"""
        return self.cache.cache_order_book(symbol, orderbook)
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """Get cached orderbook"""
        return self.cache.get_order_book(symbol)
    
    # =============== Session Management ===============
    
    def create_session(
        self,
        session_id: str,
        user_data: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Create user session"""
        return self.cache.set_session(session_id, user_data, ttl)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get user session"""
        return self.cache.get_session(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        return self.cache.delete_session(session_id)
    
    # =============== Rate Limiting ===============
    
    def check_rate_limit(
        self,
        identifier: str,
        limit: int = 60,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check rate limit
        
        Args:
            identifier: Unique identifier (IP, user_id)
            limit: Max requests per window
            window: Time window in seconds
            
        Returns:
            (allowed, remaining)
        """
        return self.cache.check_rate_limit(identifier, limit, window)
    
    # =============== Cache Decorator Helper ===============
    
    @staticmethod
    def generate_cache_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key từ arguments
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        key_parts = [prefix]
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = ":".join(key_parts)
        
        # Hash if too long
        if len(key_string) > 200:
            hash_part = hashlib.md5(key_string.encode()).hexdigest()[:16]
            return f"{prefix}:{hash_part}"
        
        return key_string
    
    # =============== Cache Warming ===============
    
    def warm_user_cache(self, user_ids: List[int], get_user_fn: Callable) -> int:
        """
        Warm cache cho nhiều users
        
        Args:
            user_ids: Danh sách user IDs
            get_user_fn: Function để lấy user data
            
        Returns:
            Số users đã cache
        """
        count = 0
        for user_id in user_ids:
            try:
                user_data = get_user_fn(user_id)
                if user_data:
                    self.cache_user(user_id, user_data)
                    count += 1
            except Exception as e:
                logger.error(f"Error warming cache for user {user_id}: {e}")
        
        logger.info(f"Cache warmed for {count} users")
        return count
    
    # =============== Statistics ===============
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thống kê cache
        
        Returns:
            Dict với cache statistics
        """
        if not self.cache.is_connected:
            return {"connected": False}
        
        try:
            info = self.cache.client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": True, "error": str(e)}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> str:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return "N/A"
        return f"{(hits / total) * 100:.2f}%"
