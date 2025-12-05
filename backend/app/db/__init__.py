"""
Database Module
Digital Utopia Platform

Quản lý kết nối PostgreSQL và Redis
"""

from .session import (
    engine,
    SessionLocal,
    get_db,
    Base,
    init_db,
    check_db_connection
)
from .redis_client import (
    redis_client,
    get_redis,
    RedisCache,
    init_redis
)
from .utils import (
    create_tables,
    drop_tables,
    seed_all,
    seed_roles,
    seed_permissions,
    seed_exchange_rates,
    seed_admin_user,
    check_database_health
)

__all__ = [
    # Session
    "engine",
    "SessionLocal", 
    "get_db",
    "Base",
    "init_db",
    "check_db_connection",
    
    # Redis
    "redis_client",
    "get_redis",
    "RedisCache",
    "init_redis",
    
    # Utils
    "create_tables",
    "drop_tables",
    "seed_all",
    "seed_roles",
    "seed_permissions",
    "seed_exchange_rates",
    "seed_admin_user",
    "check_database_health"
]
