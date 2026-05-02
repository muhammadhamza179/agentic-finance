# app/agent/executor.py

import asyncio
from datetime import datetime
from app.tools.registry import get_tool
from app.memory.postgres_store import save_tool_call
from app.logging.query_logger import log_tool_call, log_error

async def execute_plan(
    plan: list[dict],
    query_id: int,
    user_id: int
) -> dict:
    """
    Runs each tool in the plan and collects results.
    
    Two execution strategies:
    - Independent tools (macro, news): run in parallel → faster
    - Dependent tools (roi needs price): run sequentially
    
    For now: parallel execution for all (safe because tools don't depend on each other's output)
    """
    
    if not plan:
        return {"results": [], "summary": "No tools were needed for this query."}
    
    # Execute all tools concurrently
    tasks = [
        _run_single_tool(step, query_id, user_id, i)
        for i, step in enumerate(plan)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions, keep structured results
    successful = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"[EXECUTOR] Tool {plan[i]['tool']} raised exception: {result}")
        else:
            successful.append(result)
    
    return {
        "results": successful,
        "tool_count": len(successful),
        "plan": plan
    }


async def _run_single_tool(
    step: dict,
    query_id: int,
    user_id: int,
    step_index: int
) -> dict:
    """
    Run one tool call with timing and error handling.
    Saves the call to DB regardless of success/failure.
    """
    tool_name = step["tool"]
    parameters = step.get("parameters", {})
    start = datetime.utcnow()
    
    # Inject user_id for user-specific tools (portfolio)
    if tool_name == "portfolio":
        parameters["user_id"] = user_id
    
    tool = get_tool(tool_name)
    
    if tool is None:
        result = {
            "status": "error",
            "tool": tool_name,
            "data": None,
            "error": f"Tool '{tool_name}' not found in registry",
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        try:
            result = await tool["call"](**parameters)
        except TypeError as e:
            # Wrong parameters passed — planner made a mistake
            result = {
                "status": "error",
                "tool": tool_name,
                "data": None,
                "error": f"Wrong parameters for {tool_name}: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            result = {
                "status": "error",
                "tool": tool_name,
                "data": None,
                "error": f"Tool execution failed: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    latency_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    
    # Save to DB
    await save_tool_call(
        query_id=query_id,
        tool_name=tool_name,
        tool_input=parameters,
        tool_output=result,
        latency_ms=latency_ms,
        status=result.get("status", "error")
    )
    
    # Log
    await log_tool_call(tool_name, parameters, result, latency_ms)
    
    return {
        "tool": tool_name,
        "step": step_index,
        "result": result,
        "latency_ms": latency_ms
    }