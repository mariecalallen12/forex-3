"""
Database Session Management
Digital Utopia Platform

Quản lý SQLAlchemy engine, session, và kết nối PostgreSQL
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

# =============== Tạo SQLAlchemy Engine ===============
# Sử dụng connection pooling để tối ưu hiệu suất

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Số kết nối cơ bản trong pool
    max_overflow=20,  # Số kết nối tối đa có thể tạo thêm
    pool_timeout=30,  # Thời gian chờ kết nối (giây)
    pool_recycle=1800,  # Tái tạo kết nối sau 30 phút
    pool_pre_ping=True,  # Kiểm tra kết nối trước khi sử dụng
    echo=settings.DEBUG,  # Log SQL queries trong debug mode
)

# =============== Tạo Session Factory ===============
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# =============== Base class cho models ===============
Base = declarative_base()


# =============== Event Listeners ===============
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Cấu hình connection khi kết nối mới được tạo
    """
    logger.debug("New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """
    Log khi connection được lấy từ pool
    """
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """
    Log khi connection được trả về pool
    """
    logger.debug("Connection returned to pool")


# =============== Dependency Injection ===============
def get_db() -> Generator[Session, None, None]:
    """
    Dependency để inject database session vào endpoints
    
    Sử dụng:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Khởi tạo database - tạo tất cả các bảng
    Sử dụng trong startup của ứng dụng
    """
    # Import tất cả models để đảm bảo chúng được đăng ký với Base
    from ..models import (
        user, trading, financial, compliance, 
        portfolio, referral, audit
    )
    
    # Tạo tất cả bảng
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_db():
    """
    Xóa tất cả bảng trong database
    CHỈ SỬ DỤNG TRONG TESTING!
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")


# =============== Health Check ===============
def check_db_connection() -> bool:
    """
    Kiểm tra kết nối database
    
    Returns:
        True nếu kết nối thành công
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
