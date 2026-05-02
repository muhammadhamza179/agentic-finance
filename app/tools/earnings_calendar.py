# app/tools/earnings_calendar.py

import httpx
from datetime import datetime
from app.config import settings

class EarningsCalendarTool:
    """
    Uses Alpha Vantage's EARNINGS endpoint.
    Returns the next earnings date and recent EPS history.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    async def get_earnings(self, symbol: str) -> dict:
        symbol = symbol.upper().strip()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params={
                    "function": "EARNINGS",
                    "symbol": symbol,
                    "apikey": settings.ALPHA_VANTAGE_API_KEY
                })
                response.raise_for_status()
                data = response.json()
            
            if "Note" in data:
                return self._error(symbol, "Rate limit hit")
            
            annual = data.get("annualEarnings", [])
            quarterly = data.get("quarterlyEarnings", [])
            
            # Find next earnings date from quarterly data
            upcoming = [
                q for q in quarterly
                if q.get("reportedDate", "") >= datetime.utcnow().strftime("%Y-%m-%d")
            ]
            
            # Last 4 quarters for EPS trend
            recent = quarterly[:4] if quarterly else []
            eps_trend = [
                {
                    "quarter": q.get("fiscalDateEnding", ""),
                    "reported_eps": q.get("reportedEPS", "N/A"),
                    "estimated_eps": q.get("estimatedEPS", "N/A"),
                    "surprise_pct": q.get("surprisePercentage", "N/A")
                }
                for q in recent
            ]
            
            return {
                "status": "success",
                "tool": "earnings_calendar",
                "data": {
                    "symbol": symbol,
                    "next_earnings_date": upcoming[0].get("reportedDate") if upcoming else "Not scheduled",
                    "recent_eps_trend": eps_trend,
                    "eps_beat_count": sum(
                        1 for q in recent
                        if q.get("surprisePercentage") and float(q.get("surprisePercentage", 0)) > 0
                    )
                },
                "error": None,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return self._error(symbol, str(e))
    
    def _error(self, symbol: str, msg: str) -> dict:
        return {
            "status": "error", "tool": "earnings_calendar",
            "data": None, "error": msg,
            "timestamp": datetime.utcnow().isoformat()
        }

earnings_calendar_tool = EarningsCalendarTool()