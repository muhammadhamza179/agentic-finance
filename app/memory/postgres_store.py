import uuid
import json
import asyncio
from app.database import get_pool
from app.memory.embedder import embed_and_store_query


async def create_session(user_id: int) -> str:
    """Create a new conversation session. Returns session_id."""
    pool = await get_pool()
    session_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO sessions (id, user_id) VALUES ($1, $2)",
            session_id, user_id
        )
    return session_id


async def save_query(session_id: str, user_input: str, agent_response: str, user_id: int) -> int:
    """Save a completed query+response. Returns query_id."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO queries (session_id, user_input, agent_response)
               VALUES ($1, $2, $3) RETURNING id""",
            session_id, user_input, agent_response
        )
    
    query_id = row["id"]
    
    # Embed and store in vector DB (non-blocking)
    asyncio.create_task(embed_and_store_query(
        user_id=user_id,
        session_id=session_id,
        query_id=query_id,
        user_input=user_input,
        agent_response=agent_response
    ))
    
    return query_id


async def save_tool_call(
    query_id: int, tool_name: str,
    tool_input: dict, tool_output: dict,
    latency_ms: int, status: str
):
    """Log every tool call to the DB."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO tool_calls
               (query_id, tool_name, tool_input, tool_output, latency_ms, status)
               VALUES ($1, $2, $3, $4, $5, $6)""",
            query_id, tool_name,
            json.dumps(tool_input), json.dumps(tool_output),
            latency_ms, status
        )


async def get_session_history(session_id: str, limit: int = 10) -> list:
    """Retrieve last N queries for a session. Used by memory system."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT user_input, agent_response, created_at
               FROM queries
               WHERE session_id = $1
               ORDER BY created_at DESC LIMIT $2""",
            session_id, limit
        )
    return [dict(r) for r in rows]


async def update_session_active(session_id: str):
    """Update the last_active timestamp on a session."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE sessions SET last_active = NOW() WHERE id = $1",
            session_id
        )