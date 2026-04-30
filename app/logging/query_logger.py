# app/logging/query_logger.py  — replace the stub from Step 1

import json
from datetime import datetime
from app.database import get_pool

async def log_tool_call(tool: str, input: dict, output: dict, latency_ms: int):
    """Log a tool execution to the DB."""
    await _log(
        level="info",
        event="tool_call",
        data={
            "tool": tool,
            "input": input,
            "output_status": output.get("status"),
            "latency_ms": latency_ms
        }
    )

async def log_query(session_id: str, user_input: str, response: str, latency_ms: int):
    """Log a complete user query cycle."""
    await _log(
        level="info",
        event="query",
        data={
            "session_id": session_id,
            "input_length": len(user_input),
            "response_length": len(response),
            "latency_ms": latency_ms
        }
    )

async def log_error(event: str, error: str, context: dict = None):
    """Log an error with context for debugging."""
    await _log(
        level="error",
        event=event,
        data={"error": error, "context": context or {}}
    )

async def _log(level: str, event: str, data: dict):
    """Internal: write one log row to Postgres."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO logs (level, event, data) VALUES ($1, $2, $3)",
                level, event, json.dumps(data)
            )
    except Exception as e:
        # Logging must NEVER crash the main app
        print(f"[LOG FAIL] {e} | {level} | {event}")