# app/agent/planner.py

import json
from openai import AsyncOpenAI
from app.config import settings
from app.tools.registry import list_tools

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def plan_query(user_input: str) -> list[dict]:
    """
    Takes the user's query and returns an ordered list of tool calls to make.
    
    Example input:  "Should I invest in Tesla right now?"
    Example output: [
        {"tool": "stock_price",          "parameters": {"symbol": "TSLA"}},
        {"tool": "company_fundamentals", "parameters": {"symbol": "TSLA"}},
        {"tool": "news_sentiment",       "parameters": {"company": "Tesla"}},
        {"tool": "risk_scoring",         "parameters": {"symbol": "TSLA"}},
        {"tool": "macro_indicators",     "parameters": {}}
    ]
    """
    
    system = f"""You are a planning agent for a financial AI system.

Given a user's financial question, output a JSON array of tool calls needed to answer it.
Use ONLY tools from this list:

{list_tools()}

Output ONLY a JSON array. No explanation. No markdown. Just the array.

Example:
User: "Is Apple stock cheap right now?"
Output: [
  {{"tool": "stock_price", "parameters": {{"symbol": "AAPL"}}}},
  {{"tool": "company_fundamentals", "parameters": {{"symbol": "AAPL"}}}},
  {{"tool": "news_sentiment", "parameters": {{"company": "Apple"}}}}
]

Rules:
- Use 1-5 tools maximum
- Only include tools that are genuinely needed
- Order from most critical to least
- If query is simple (e.g. "What is Apple's price?"), use only 1 tool
"""
    
    response = await openai_client.chat.completions.create(
        model=settings.OPENAI_FALLBACK_MODEL,  # Use cheaper model for planning
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_input}
        ],
        temperature=0,         # Deterministic — we want consistent plans
        max_tokens=500,
        response_format={"type": "json_object"}  # Force JSON output
    )
    
    raw = response.choices[0].message.content.strip()
    
    try:
        parsed = json.loads(raw)
        # Handle both {"steps": [...]} and [...] responses
        if isinstance(parsed, dict):
            plan = parsed.get("steps", parsed.get("tools", []))
        else:
            plan = parsed
        
        # Validate each step has required fields
        valid_plan = []
        for step in plan:
            if isinstance(step, dict) and "tool" in step:
                valid_plan.append({
                    "tool": step["tool"],
                    "parameters": step.get("parameters", {})
                })
        
        return valid_plan if valid_plan else [{"tool": "stock_price", "parameters": {}}]
    
    except json.JSONDecodeError:
        # Fallback: if planning fails, just get stock price
        print(f"[PLANNER] Failed to parse plan: {raw}")
        return [{"tool": "stock_price", "parameters": {}}]