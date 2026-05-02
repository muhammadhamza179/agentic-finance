# app/tools/company_fundamentals.py

import httpx
from datetime import datetime
from app.config import settings

class CompanyFundamentalsTool:
    """
    Fetches company overview and financial fundamentals.
    
    Key metrics explained:
    - P/E ratio:    Price / Earnings. High P/E = expensive or high-growth expected
    - EPS:          Earnings Per Share. Is the company actually profitable?
    - Revenue:      Total sales. Growing revenue = growing business
    - Profit Margin: How much profit per $1 of revenue
    - 52-week H/L:  Price context — where is it now vs its range?
    - Beta:         Volatility vs market. Beta >1 = more volatile than S&P 500
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    async def get_fundamentals(self, symbol: str) -> dict:
        symbol = symbol.upper().strip()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params={
                    "function": "OVERVIEW",
                    "symbol": symbol,
                    "apikey": settings.ALPHA_VANTAGE_API_KEY
                })
                response.raise_for_status()
                data = response.json()
            
            if not data or "Note" in data:
                return self._error(symbol, "Rate limited or no data")
            
            if "Symbol" not in data:
                return self._error(symbol, f"Symbol {symbol} not found")
            
            # Parse and normalize — Alpha Vantage returns strings, we want numbers
            def safe_float(val, default=None):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default
            
            pe = safe_float(data.get("PERatio"))
            eps = safe_float(data.get("EPS"))
            margin = safe_float(data.get("ProfitMargin"))
            beta = safe_float(data.get("Beta"))
            
            # Valuation signal — simple heuristic
            valuation = self._valuation_signal(pe, eps, margin)
            
            return {
                "status": "success",
                "tool": "company_fundamentals",
                "data": {
                    "symbol": symbol,
                    "company_name": data.get("Name", symbol),
                    "sector": data.get("Sector", "N/A"),
                    "industry": data.get("Industry", "N/A"),
                    "description": data.get("Description", "")[:200],
                    "fundamentals": {
                        "pe_ratio": pe,
                        "eps": eps,
                        "revenue_ttm": data.get("RevenueTTM", "N/A"),
                        "profit_margin": margin,
                        "return_on_equity": safe_float(data.get("ReturnOnEquityTTM")),
                        "debt_to_equity": safe_float(data.get("DebtToEquityRatio")),
                        "beta": beta,
                        "dividend_yield": safe_float(data.get("DividendYield")),
                        "market_cap": data.get("MarketCapitalization", "N/A"),
                    },
                    "price_context": {
                        "week_52_high": safe_float(data.get("52WeekHigh")),
                        "week_52_low": safe_float(data.get("52WeekLow")),
                        "moving_avg_50": safe_float(data.get("50DayMovingAverage")),
                        "moving_avg_200": safe_float(data.get("200DayMovingAverage")),
                        "analyst_target": safe_float(data.get("AnalystTargetPrice")),
                    },
                    "valuation_signal": valuation
                },
                "error": None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return self._error(symbol, str(e))
    
    def _valuation_signal(self, pe, eps, margin) -> str:
        if pe is None or eps is None:
            return "Insufficient data for valuation"
        
        if eps < 0:
            return "LOSS-MAKING — Company is currently unprofitable"
        
        if pe > 50:
            return "EXPENSIVE — High P/E requires significant growth to justify"
        if pe < 15:
            if margin and margin > 0.15:
                return "VALUE — Low P/E with healthy margins (potential undervalued)"
            return "CHEAP — Low P/E but check margins and growth rate"
        
        return "FAIR VALUE — P/E in normal range, check growth rate vs peers"
    
    def _error(self, symbol: str, msg: str) -> dict:
        return {
            "status": "error", "tool": "company_fundamentals",
            "data": None, "error": msg,
            "timestamp": datetime.utcnow().isoformat()
        }

fundamentals_tool = CompanyFundamentalsTool()