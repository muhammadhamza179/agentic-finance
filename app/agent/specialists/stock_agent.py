# app/agent/specialists/stock_agent.py

from openai import AsyncOpenAI
from app.config import settings

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

STOCK_AGENT_SYSTEM = """You are a specialist stock analysis agent.
Your ONLY job: analyze stock price data and technical indicators.

When given stock data, provide:
1. Current price assessment (cheap/fair/expensive vs 52-week range)
2. Volume interpretation (high volume = conviction in price move)  
3. Momentum (is it trending up or down based on moving averages?)
4. One clear short-term outlook sentence

Be specific. Use the numbers. Maximum 4 sentences.
No financial advice disclaimer needed — parent agent handles that.
"""

async def analyze_stock(stock_data: dict) -> str:
    """Takes raw stock tool output, returns specialist analysis."""
    if not stock_data or stock_data.get("status") != "success":
        return "Stock data unavailable for analysis."
    
    response = await openai_client.chat.completions.create(
        model=settings.OPENAI_FALLBACK_MODEL,
        messages=[
            {"role": "system", "content": STOCK_AGENT_SYSTEM},
            {"role": "user", "content": f"Analyze this data: {stock_data['data']}"}
        ],
        max_tokens=200,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()