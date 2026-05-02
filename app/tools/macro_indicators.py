# app/tools/macro_indicators.py

import httpx
from datetime import datetime
from app.config import settings

class MacroIndicatorsTool:
    """
    Fetches macroeconomic indicators from Alpha Vantage.
    
    Why macro matters for stock analysis:
    - Rising CPI (inflation) → Fed raises rates → bonds attractive → stocks fall
    - Rising GDP → economy strong → corporate earnings up → stocks rise
    - Rising unemployment → consumer spending falls → retail stocks hurt
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    INDICATORS = {
        "inflation":       "CPI",           # Consumer Price Index
        "interest_rate":   "FEDERAL_FUNDS_RATE",
        "gdp":             "REAL_GDP",
        "unemployment":    "UNEMPLOYMENT",
    }
    
    async def _fetch(self, function: str) -> list:
        """Fetch one indicator's time series from Alpha Vantage."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params={
                    "function": function,
                    "interval": "monthly",
                    "apikey": settings.ALPHA_VANTAGE_API_KEY
                })
                response.raise_for_status()
                data = response.json()
            
            if "Note" in data:
                return []  # Rate limited
            
            return data.get("data", [])[:6]  # Last 6 months only
        
        except Exception:
            return []
    
    async def get_all(self) -> dict:
        """
        Fetch all macro indicators and return a unified summary.
        The agent calls this when user asks about market conditions.
        """
        import asyncio
        
        # Fetch all indicators in parallel — not sequentially
        results = await asyncio.gather(
            self._fetch(self.INDICATORS["inflation"]),
            self._fetch(self.INDICATORS["interest_rate"]),
            self._fetch(self.INDICATORS["gdp"]),
            self._fetch(self.INDICATORS["unemployment"]),
            return_exceptions=True  # Don't crash if one fails
        )
        
        inflation_data, rate_data, gdp_data, unemploy_data = results
        
        def latest(data, key="value"):
            """Get the most recent value from a time series."""
            if isinstance(data, list) and data:
                return data[0].get(key, "N/A")
            return "N/A"
        
        def trend(data):
            """Is the indicator rising, falling, or stable?"""
            if not isinstance(data, list) or len(data) < 2:
                return "unknown"
            try:
                recent = float(data[0]["value"])
                prior  = float(data[1]["value"])
                diff = recent - prior
                if diff > 0.1:   return "rising"
                if diff < -0.1:  return "falling"
                return "stable"
            except (ValueError, KeyError):
                return "unknown"
        
        return {
            "status": "success",
            "tool": "macro_indicators",
            "data": {
                "inflation_cpi": {
                    "latest": latest(inflation_data),
                    "trend": trend(inflation_data),
                    "history": inflation_data
                },
                "federal_funds_rate": {
                    "latest": latest(rate_data),
                    "trend": trend(rate_data),
                    "history": rate_data
                },
                "real_gdp": {
                    "latest": latest(gdp_data),
                    "trend": trend(gdp_data),
                    "history": gdp_data
                },
                "unemployment": {
                    "latest": latest(unemploy_data),
                    "trend": trend(unemploy_data),
                    "history": unemploy_data
                },
                "market_signal": self._interpret(
                    trend(rate_data), trend(inflation_data), trend(gdp_data)
                )
            },
            "error": None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _interpret(self, rate_trend: str, inflation_trend: str, gdp_trend: str) -> str:
        """
        Simple rule-based macro signal.
        Real quant models are complex, but this gives the agent directional context.
        """
        if rate_trend == "rising" and inflation_trend == "rising":
            return "CAUTIOUS — Rising rates and inflation typically pressure equity valuations"
        if gdp_trend == "rising" and rate_trend == "stable":
            return "POSITIVE — GDP growth with stable rates is favorable for equities"
        if gdp_trend == "falling":
            return "DEFENSIVE — Slowing GDP suggests risk-off positioning"
        return "NEUTRAL — Mixed macro signals, watch for Fed guidance"

macro_tool = MacroIndicatorsTool()