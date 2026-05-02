# app/tools/registry.py

from app.tools.stock_price import stock_price_tool
from app.tools.news_sentiment import news_sentiment_tool
from app.tools.roi_calculator import roi_calculator_tool       # built in original Step 4
from app.tools.risk_scoring import risk_scoring_tool           # built in original Step 5
from app.tools.portfolio_tracker import portfolio_tracker_tool
from app.tools.earnings_calendar import earnings_calendar_tool
from app.tools.macro_indicators import macro_tool
from app.tools.company_fundamentals import fundamentals_tool

# Tool registry — maps tool name → async callable
# Every tool follows the same contract: takes kwargs, returns {status, tool, data, error}
TOOL_REGISTRY = {
    "stock_price": {
        "description": "Get current stock price and basic stats for a symbol",
        "parameters": {"symbol": "string — stock ticker e.g. AAPL"},
        "call": lambda **kw: stock_price_tool.get_quote(kw["symbol"])
    },
    "news_sentiment": {
        "description": "Get recent financial news and sentiment score for a company",
        "parameters": {"company": "string — company name or ticker"},
        "call": lambda **kw: news_sentiment_tool.get_news(kw["company"])
    },
    "roi_calculator": {
        "description": "Calculate return on investment for a stock position",
        "parameters": {
            "symbol": "string — ticker",
            "buy_price": "float — price paid per share",
            "shares": "float — number of shares owned"
        },
        "call": lambda **kw: roi_calculator_tool.calculate(
            kw["symbol"], kw["buy_price"], kw["shares"]
        )
    },
    "risk_scoring": {
        "description": "Score investment risk for a stock on a 1-10 scale",
        "parameters": {"symbol": "string — ticker"},
        "call": lambda **kw: risk_scoring_tool.score(kw["symbol"])
    },
    "portfolio": {
        "description": "Get user's full portfolio with live P&L",
        "parameters": {"user_id": "int — current user's ID"},
        "call": lambda **kw: portfolio_tracker_tool.get_portfolio(kw["user_id"])
    },
    "earnings_calendar": {
        "description": "Get next earnings date and recent EPS history for a stock",
        "parameters": {"symbol": "string — ticker"},
        "call": lambda **kw: earnings_calendar_tool.get_earnings(kw["symbol"])
    },
    "macro_indicators": {
        "description": "Get current macroeconomic indicators: inflation, rates, GDP",
        "parameters": {},
        "call": lambda **kw: macro_tool.get_all()
    },
    "company_fundamentals": {
        "description": "Get P/E, EPS, margins, beta and analyst targets for a stock",
        "parameters": {"symbol": "string — ticker"},
        "call": lambda **kw: fundamentals_tool.get_fundamentals(kw["symbol"])
    }
}

def get_tool(name: str):
    """Look up a tool by name. Returns None if not found."""
    return TOOL_REGISTRY.get(name)

def list_tools() -> str:
    """
    Format all tools for injection into the LLM system prompt.
    The LLM reads this and decides which tool to call.
    """
    lines = []
    for name, info in TOOL_REGISTRY.items():
        params = ", ".join(
            f"{k}: {v}" for k, v in info["parameters"].items()
        )
        lines.append(f"- {name}({params}): {info['description']}")
    return "\n".join(lines)