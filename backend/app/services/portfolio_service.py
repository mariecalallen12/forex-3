"""
Portfolio Service
Digital Utopia Platform

Business logic cho Portfolio operations
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from decimal import Decimal
from datetime import datetime, timedelta
import logging

from ..models.trading import PortfolioPosition
from ..models.portfolio import TradingBot, Watchlist
from ..models.financial import WalletBalance
from ..db.redis_client import RedisCache

logger = logging.getLogger(__name__)


class PortfolioService:
    """
    Service class cho Portfolio operations
    
    Cung cấp business logic cho:
    - Portfolio analytics
    - Trading bots management
    - Watchlist management
    """
    
    def __init__(self, db: Session, cache: Optional[RedisCache] = None):
        """
        Khởi tạo PortfolioService
        
        Args:
            db: SQLAlchemy session
            cache: Redis cache client (optional)
        """
        self.db = db
        self.cache = cache
    
    # =============== Portfolio Analytics ===============
    
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy tổng quan portfolio của user
        
        Args:
            user_id: User ID
            
        Returns:
            Dict với portfolio summary
        """
        # Check cache first
        if self.cache:
            cached = self.cache.get_json(f"portfolio:summary:{user_id}")
            if cached:
                return cached
        
        # Get open positions
        positions = self.db.query(PortfolioPosition).filter(
            and_(
                PortfolioPosition.user_id == user_id,
                PortfolioPosition.is_closed == False
            )
        ).all()
        
        # Get balances
        balances = self.db.query(WalletBalance).filter(
            WalletBalance.user_id == user_id
        ).all()
        
        # Calculate totals
        total_market_value = sum(float(p.market_value or 0) for p in positions)
        total_unrealized_pnl = sum(float(p.unrealized_pnl or 0) for p in positions)
        total_realized_pnl = sum(float(p.realized_pnl or 0) for p in positions)
        
        total_balance = sum(float(b.available_balance or 0) + float(b.locked_balance or 0) for b in balances)
        
        # Position breakdown by symbol
        position_breakdown = {}
        for pos in positions:
            if pos.symbol not in position_breakdown:
                position_breakdown[pos.symbol] = {
                    "quantity": 0,
                    "market_value": 0,
                    "unrealized_pnl": 0
                }
            position_breakdown[pos.symbol]["quantity"] += float(pos.quantity or 0)
            position_breakdown[pos.symbol]["market_value"] += float(pos.market_value or 0)
            position_breakdown[pos.symbol]["unrealized_pnl"] += float(pos.unrealized_pnl or 0)
        
        summary = {
            "user_id": user_id,
            "total_balance": total_balance,
            "total_market_value": total_market_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_pnl": total_unrealized_pnl + total_realized_pnl,
            "positions_count": len(positions),
            "position_breakdown": position_breakdown,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache for 1 minute
        if self.cache:
            self.cache.set_json(f"portfolio:summary:{user_id}", summary, ttl=60)
        
        return summary
    
    def get_portfolio_metrics(self, user_id: int) -> Dict[str, Any]:
        """
        Lấy metrics chi tiết của portfolio
        
        Args:
            user_id: User ID
            
        Returns:
            Dict với portfolio metrics
        """
        positions = self.db.query(PortfolioPosition).filter(
            PortfolioPosition.user_id == user_id
        ).all()
        
        open_positions = [p for p in positions if not p.is_closed]
        closed_positions = [p for p in positions if p.is_closed]
        
        # Calculate win rate
        winning_trades = len([p for p in closed_positions if float(p.realized_pnl or 0) > 0])
        losing_trades = len([p for p in closed_positions if float(p.realized_pnl or 0) < 0])
        total_closed = len(closed_positions)
        win_rate = (winning_trades / total_closed * 100) if total_closed > 0 else 0
        
        # Calculate average P&L
        total_realized = sum(float(p.realized_pnl or 0) for p in closed_positions)
        avg_pnl = (total_realized / total_closed) if total_closed > 0 else 0
        
        # Calculate max drawdown (simplified)
        pnl_values = [float(p.realized_pnl or 0) for p in closed_positions]
        cumulative = 0
        peak = 0
        max_drawdown = 0
        for pnl in pnl_values:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "user_id": user_id,
            "open_positions": len(open_positions),
            "closed_positions": total_closed,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_realized_pnl": total_realized,
            "average_pnl": round(avg_pnl, 2),
            "max_drawdown": round(max_drawdown, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # =============== Trading Bots ===============
    
    def create_trading_bot(
        self,
        user_id: int,
        name: str,
        strategy_name: str,
        symbols: List[str],
        base_amount: Decimal,
        strategy_parameters: Optional[Dict] = None
    ) -> TradingBot:
        """
        Tạo trading bot mới
        
        Args:
            user_id: User ID
            name: Tên bot
            strategy_name: Tên chiến lược
            symbols: Danh sách symbols
            base_amount: Số tiền cơ bản
            strategy_parameters: Tham số chiến lược
            
        Returns:
            TradingBot mới
        """
        bot = TradingBot(
            user_id=user_id,
            name=name,
            strategy_name=strategy_name,
            symbols=symbols,
            base_amount=base_amount,
            strategy_parameters=strategy_parameters or {},
            status="PAUSED"
        )
        
        self.db.add(bot)
        self.db.commit()
        self.db.refresh(bot)
        
        logger.info(f"Trading bot created: {bot.id} for user {user_id}")
        return bot
    
    def get_user_bots(self, user_id: int) -> List[TradingBot]:
        """Lấy tất cả bots của user"""
        return self.db.query(TradingBot).filter(
            TradingBot.user_id == user_id
        ).all()
    
    def update_bot_status(
        self,
        bot_id: int,
        user_id: int,
        status: str
    ) -> Optional[TradingBot]:
        """
        Cập nhật status của bot
        
        Args:
            bot_id: Bot ID
            user_id: User ID (để verify ownership)
            status: Status mới (STARTED, PAUSED, STOPPED)
            
        Returns:
            TradingBot đã cập nhật
        """
        bot = self.db.query(TradingBot).filter(
            and_(
                TradingBot.id == bot_id,
                TradingBot.user_id == user_id
            )
        ).first()
        
        if not bot:
            return None
        
        bot.status = status
        if status == "STARTED":
            bot.last_run_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(bot)
        
        logger.info(f"Trading bot {bot_id} status updated to {status}")
        return bot
    
    def delete_bot(self, bot_id: int, user_id: int) -> bool:
        """
        Xóa trading bot
        
        Args:
            bot_id: Bot ID
            user_id: User ID
            
        Returns:
            True nếu xóa thành công
        """
        bot = self.db.query(TradingBot).filter(
            and_(
                TradingBot.id == bot_id,
                TradingBot.user_id == user_id
            )
        ).first()
        
        if not bot:
            return False
        
        self.db.delete(bot)
        self.db.commit()
        
        logger.info(f"Trading bot {bot_id} deleted")
        return True
    
    # =============== Watchlist ===============
    
    def get_user_watchlist(self, user_id: int) -> List[Watchlist]:
        """Lấy tất cả watchlists của user"""
        return self.db.query(Watchlist).filter(
            Watchlist.user_id == user_id
        ).order_by(Watchlist.sort_order).all()
    
    def create_watchlist(
        self,
        user_id: int,
        name: str = "Default",
        symbols: Optional[List[str]] = None
    ) -> Watchlist:
        """
        Tạo watchlist mới
        
        Args:
            user_id: User ID
            name: Tên watchlist
            symbols: Danh sách symbols
            
        Returns:
            Watchlist mới
        """
        # Check if default watchlist exists
        existing = self.db.query(Watchlist).filter(
            and_(
                Watchlist.user_id == user_id,
                Watchlist.name == name
            )
        ).first()
        
        if existing:
            # Update existing
            if symbols:
                existing.symbols = list(set((existing.symbols or []) + symbols))
            self.db.commit()
            return existing
        
        watchlist = Watchlist(
            user_id=user_id,
            name=name,
            symbols=symbols or [],
            is_default=(name == "Default")
        )
        
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        
        logger.info(f"Watchlist created: {watchlist.id} for user {user_id}")
        return watchlist
    
    def add_to_watchlist(
        self,
        user_id: int,
        symbol: str,
        watchlist_id: Optional[int] = None
    ) -> Optional[Watchlist]:
        """
        Thêm symbol vào watchlist
        
        Args:
            user_id: User ID
            symbol: Symbol cần thêm
            watchlist_id: Watchlist ID (nếu None, thêm vào default)
            
        Returns:
            Watchlist đã cập nhật
        """
        if watchlist_id:
            watchlist = self.db.query(Watchlist).filter(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id
                )
            ).first()
        else:
            # Get or create default watchlist
            watchlist = self.db.query(Watchlist).filter(
                and_(
                    Watchlist.user_id == user_id,
                    Watchlist.is_default == True
                )
            ).first()
            
            if not watchlist:
                watchlist = self.create_watchlist(user_id)
        
        if not watchlist:
            return None
        
        # Add symbol if not exists
        current_symbols = watchlist.symbols or []
        if symbol not in current_symbols:
            current_symbols.append(symbol)
            watchlist.symbols = current_symbols
            self.db.commit()
            self.db.refresh(watchlist)
        
        return watchlist
    
    def remove_from_watchlist(
        self,
        user_id: int,
        symbol: str,
        watchlist_id: Optional[int] = None
    ) -> Optional[Watchlist]:
        """
        Xóa symbol khỏi watchlist
        
        Args:
            user_id: User ID
            symbol: Symbol cần xóa
            watchlist_id: Watchlist ID
            
        Returns:
            Watchlist đã cập nhật
        """
        if watchlist_id:
            watchlist = self.db.query(Watchlist).filter(
                and_(
                    Watchlist.id == watchlist_id,
                    Watchlist.user_id == user_id
                )
            ).first()
        else:
            watchlist = self.db.query(Watchlist).filter(
                and_(
                    Watchlist.user_id == user_id,
                    Watchlist.is_default == True
                )
            ).first()
        
        if not watchlist:
            return None
        
        # Remove symbol
        current_symbols = watchlist.symbols or []
        if symbol in current_symbols:
            current_symbols.remove(symbol)
            watchlist.symbols = current_symbols
            self.db.commit()
            self.db.refresh(watchlist)
        
        return watchlist
