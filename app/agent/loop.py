# app/agent/loop.py  — THE COMPLETE AGENT LOOP

import json
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings
from app.agent.planner import plan_query
from app.agent.executor import execute_plan
from app.agent.tracer import AgentTracer
from app.agent.prompt_builder import build_prompt
from app.agent.specialists.stock_agent import analyze_stock
from app.agent.specialists.risk_agent import assess_risk
from app.agent.specialists.news_agent import analyze_news
from app.memory.session import SessionMemory
from app.memory.embedder import embed_and_store_query
from app.logging.query_logger import log_query, log_error

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def run_agent(
    user_input: str,
    user_id: int,
    query_id: int,
    session: SessionMemory
) -> dict:
    """
    The complete agent loop:
    
    1. PLAN   — decide which tools are needed
    2. EXECUTE — run the tools in parallel
    3. ANALYZE — specialist agents interpret results  
    4. SYNTHESIZE — master LLM writes the final answer
    5. STORE  — save to memory for future context
    
    Returns the response + trace for the API endpoint.
    """
    
    tracer = AgentTracer(query=user_input)
    start = datetime.utcnow()
    
    try:
        # ── STEP 1: PLAN ────────────────────────────────────────
        tracer.log("planning", user_input, "Deciding which tools to call")
        
        plan = await plan_query(user_input)
        tracer.log("plan_ready", plan, f"{len(plan)} tool(s) planned")
        
        # ── STEP 2: EXECUTE ─────────────────────────────────────
        tracer.log("executing", plan, "Running tools in parallel")
        
        execution = await execute_plan(plan, query_id, user_id)
        tool_results = execution["results"]
        
        tracer.log("execution_done", 
                   {"tools_run": len(tool_results)},
                   f"All tools completed")
        
        # ── STEP 3: SPECIALIST ANALYSIS ─────────────────────────
        specialist_insights = {}
        
        for tr in tool_results:
            tool_name = tr["tool"]
            result = tr["result"]
            
            if tool_name == "stock_price" and result.get("status") == "success":
                tracer.log("specialist", "stock_agent", "Analyzing price data")
                specialist_insights["stock"] = await analyze_stock(result)
            
            elif tool_name == "news_sentiment" and result.get("status") == "success":
                tracer.log("specialist", "news_agent", "Interpreting news")
                specialist_insights["news"] = await analyze_news(result)
            
            elif tool_name in ["company_fundamentals", "risk_scoring"]:
                if result.get("status") == "success":
                    tracer.log("specialist", "risk_agent", "Assessing risk")
                    specialist_insights["risk"] = await assess_risk(result)
        
        # ── STEP 4: SYNTHESIZE ───────────────────────────────────
        tracer.log("synthesizing", specialist_insights, "Building final response")
        
        # Format tool results for the LLM
        tool_context = _format_tool_results(tool_results, specialist_insights)
        
        # Build the full prompt with RAG + history + tools
        messages = await build_prompt(
            user_input=user_input,
            user_id=user_id,
            session=session,
            tool_result=tool_context
        )
        
        # Final LLM call — synthesize everything into one answer
        response = await openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.4
        )
        
        final_answer = response.choices[0].message.content.strip()
        
        # ── STEP 5: STORE ────────────────────────────────────────
        tracer.log("storing", "memory", "Saving to session + vector memory")
        
        await session.add(user_input, final_answer)
        
        await embed_and_store_query(
            user_id=user_id,
            session_id=session.session_id,
            query_id=query_id,
            user_input=user_input,
            agent_response=final_answer
        )
        
        latency_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        tracer.log("complete", {"latency_ms": latency_ms}, "Agent run finished")
        
        await log_query(session.session_id, user_input, final_answer, latency_ms)
        
        return {
            "response": final_answer,
            "tools_used": [
                {"tool": tr["tool"], "status": tr["result"].get("status"), 
                 "latency_ms": tr["latency_ms"]}
                for tr in tool_results
            ],
            "trace": tracer.to_dict(),
            "latency_ms": latency_ms
        }
    
    except Exception as e:
        await log_error("agent_loop", str(e), {"query": user_input, "user_id": user_id})
        return {
            "response": "I encountered an error processing your request. Please try again.",
            "tools_used": [],
            "trace": tracer.to_dict(),
            "error": str(e)
        }


def _format_tool_results(tool_results: list, insights: dict) -> str:
    """Convert tool outputs + specialist insights into a readable string for the LLM."""
    parts = []
    
    for tr in tool_results:
        tool = tr["tool"]
        result = tr["result"]
        
        if result.get("status") == "success" and result.get("data"):
            parts.append(f"[{tool.upper()} DATA]\n{json.dumps(result['data'], indent=2)}")
        elif result.get("status") == "error":
            parts.append(f"[{tool.upper()} ERROR] {result.get('error')}")
    
    if insights:
        parts.append("\n[SPECIALIST ANALYSIS]")
        for name, analysis in insights.items():
            parts.append(f"{name.upper()} AGENT:\n{analysis}")
    
    return "\n\n".join(parts)