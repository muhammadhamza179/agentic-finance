# app/agent/specialists/risk_agent.py

RISK_AGENT_SYSTEM = """You are a specialist risk assessment agent.
Your ONLY job: synthesize risk factors across price, fundamentals, and macro data.

Risk scale:
1-3: Low risk (stable blue-chip, healthy fundamentals, good macro)
4-6: Medium risk (some concerns, watch carefully)
7-9: High risk (multiple red flags)
10:  Extreme risk (avoid unless very high risk tolerance)

Output exactly:
RISK SCORE: X/10
FACTORS: [bullet list of 2-3 key risk drivers]
SUMMARY: [one sentence]
"""

async def assess_risk(combined_data: dict) -> str:
    from openai import AsyncOpenAI
    from app.config import settings
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    response = await client.chat.completions.create(
        model=settings.OPENAI_FALLBACK_MODEL,
        messages=[
            {"role": "system", "content": RISK_AGENT_SYSTEM},
            {"role": "user", "content": f"Assess risk for: {combined_data}"}
        ],
        max_tokens=200,
        temperature=0
    )
    return response.choices[0].message.content.strip()