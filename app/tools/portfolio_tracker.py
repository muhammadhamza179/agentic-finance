# app/tools/portfolio_tracker.py

import json
from datetime import datetime
from app.database import get_pool
from app.tools.stock_price import stock_price_tool

class PortfolioTrackerTool:
    
    async def add_holding(
        self, user_id: int, symbol: str,
        shares: float, buy_price: float
    ) -> dict:
        """Add or update a stock holding for a user."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Upsert — update if symbol exists, insert if not
            await conn.execute("""
                INSERT INTO portfolio (user_id, symbol, shares, buy_price, added_at)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (user_id, symbol)
                DO UPDATE SET shares = $3, buy_price = $4
            """, user_id, symbol.upper(), shares, buy_price)
        
        return {
            "status": "success",
            "tool": "portfolio_tracker",
            "data": {
                "action": "added",
                "symbol": symbol.upper(),
                "shares": shares,
                "buy_price": buy_price,
                "total_cost": round(shares * buy_price, 2)
            },
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_portfolio(self, user_id: int) -> dict:
        """Get all holdings with current value and P&L."""
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT symbol, shares, buy_price FROM portfolio WHERE user_id = $1",
                user_id
            )
        
        if not rows:
            return {
                "status": "success", "tool": "portfolio_tracker",
                "data": {"holdings": [], "total_value": 0, "total_pnl": 0},
                "error": None, "timestamp": datetime.utcnow().isoformat()
            }
        
        holdings = []
        total_value = 0
        total_cost = 0
        
        for row in rows:
            # Get live price for each holding
            price_result = await stock_price_tool.get_quote(row["symbol"])
            
            if price_result["status"] == "success":
                current_price = price_result["data"]["price"]
            else:
                current_price = row["buy_price"]  # Fallback to buy price
            
            current_value = row["shares"] * current_price
            cost_basis = row["shares"] * row["buy_price"]
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            holdings.append({
                "symbol": row["symbol"],
                "shares": float(row["shares"]),
                "buy_price": float(row["buy_price"]),
                "current_price": current_price,
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnl_percent": round(pnl_pct, 2)
            })
            
            total_value += current_value
            total_cost += cost_basis
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "status": "success",
            "tool": "portfolio_tracker",
            "data": {
                "holdings": holdings,
                "total_value": round(total_value, 2),
                "total_cost": round(total_cost, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percent": round(total_pnl_pct, 2)
            },
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }

portfolio_tracker_tool = PortfolioTrackerTool()