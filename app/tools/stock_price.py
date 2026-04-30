import httpx
import asyncio
from typing import Optional
from datetime import datetime
from app.config import settings
from app.logging.query_logger import log_tool_call
from app.tools.base import with_retry


class StockPriceTool:
    """
    Fetches real-time and historical stock data from Alpha Vantage.
    
    Why async? Because the agent loop runs multiple tool calls concurrently.
    Blocking on network I/O with synchronous requests.get() would serialize
    everything and destroy latency. httpx with async is the production pattern.
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Lazy-initialize the connection pool."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=10.0,
                    write=5.0,
                    pool=2.0
                ),
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10
                )
            )
        return self._client
    
    @with_retry(max_attempts=3, delay=1.0)
    async def get_quote(self, symbol: str) -> dict:
        """
        Get current stock price for a symbol.
        Always includes: status, data, error, timestamp, source.
        """
        symbol = symbol.upper().strip()
        start_time = datetime.utcnow()
        
        try:
            client = await self._get_client()
            
            response = await client.get(
                self.BASE_URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": symbol,
                    "apikey": self.api_key
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "Note" in data:
                return self._rate_limit_response(symbol)
            
            if "Error Message" in data:
                return self._error_response(
                    symbol, 
                    f"Invalid symbol or API error: {data['Error Message']}"
                )
            
            quote = data.get("Global Quote", {})
            if not quote:
                return self._error_response(symbol, "No data returned for symbol")
            
            result = {
                "status": "success",
                "tool": "stock_price",
                "data": {
                    "symbol": quote.get("01. symbol", symbol),
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
                    "volume": int(quote.get("06. volume", 0)),
                    "latest_trading_day": quote.get("07. latest trading day"),
                    "previous_close": float(quote.get("08. previous close", 0)),
                    "open": float(quote.get("02. open", 0)),
                    "high": float(quote.get("03. high", 0)),
                    "low": float(quote.get("04. low", 0)),
                },
                "error": None,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alpha_vantage",
                "latency_ms": (datetime.utcnow() - start_time).microseconds // 1000
            }
            
            await log_tool_call(
                tool="stock_price",
                input={"symbol": symbol},
                output=result,
                latency_ms=result["latency_ms"]
            )
            
            return result
            
        except httpx.TimeoutException:
            return self._error_response(
                symbol, 
                "Alpha Vantage timed out. The market data service may be slow."
            )
        except httpx.HTTPStatusError as e:
            return self._error_response(
                symbol,
                f"HTTP {e.response.status_code}: {e.response.text[:100]}"
            )
        except Exception as e:
            return self._error_response(symbol, f"Unexpected error: {str(e)}")
    
    @with_retry(max_attempts=3, delay=1.0)
    async def get_daily_history(self, symbol: str, days: int = 30) -> dict:
        """
        Get historical daily prices for trend analysis and ROI calculation.
        """
        symbol = symbol.upper().strip()
        
        try:
            client = await self._get_client()
            response = await client.get(
                self.BASE_URL,
                params={
                    "function": "TIME_SERIES_DAILY",
                    "symbol": symbol,
                    "outputsize": "compact",
                    "apikey": self.api_key
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if "Note" in data:
                return self._rate_limit_response(symbol)
            
            time_series = data.get("Time Series (Daily)", {})
            
            history = []
            for date_str, values in list(time_series.items())[:days]:
                history.append({
                    "date": date_str,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"])
                })
            
            return {
                "status": "success",
                "tool": "stock_history",
                "data": {
                    "symbol": symbol,
                    "history": history,
                    "days_returned": len(history)
                },
                "error": None,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "alpha_vantage"
            }
            
        except Exception as e:
            return self._error_response(symbol, str(e))
    
    def _rate_limit_response(self, symbol: str) -> dict:
        return {
            "status": "rate_limited",
            "tool": "stock_price",
            "data": None,
            "error": (
                "Alpha Vantage rate limit reached. "
                "Free tier allows 25 calls/day. "
                "Consider using cached data or upgrading to premium."
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "alpha_vantage"
        }
    
    def _error_response(self, symbol: str, message: str) -> dict:
        return {
            "status": "error",
            "tool": "stock_price",
            "data": None,
            "error": message,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "alpha_vantage"
        }
    
    async def close(self):
        """Clean up connection pool. Call on app shutdown."""
        if self._client:
            await self._client.aclose()


# Singleton
stock_price_tool = StockPriceTool()