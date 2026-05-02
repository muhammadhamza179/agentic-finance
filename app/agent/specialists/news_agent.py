# app/agent/specialists/news_agent.py

NEWS_AGENT_SYSTEM = """You are a specialist financial news analyst.
Your ONLY job: interpret news sentiment and its likely market impact.

Output exactly:
SENTIMENT: [positive/neutral/negative] (X/10 confidence)
KEY THEMES: [bullet list of 2-3 dominant themes in recent news]
MARKET IMPACT: [likely short-term price impact and why]
"""

async def analyze_news(news_data: dict) -> str:
    from openai import AsyncOpenAI
    from app.config import settings
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    response = await client.chat.completions.create(
        model=settings.OPENAI_FALLBACK_MODEL,
        messages=[
            {"role": "system", "content": NEWS_AGENT_SYSTEM},
            {"role": "user", "content": f"Analyze news: {news_data}"}
        ],
        max_tokens=200,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()