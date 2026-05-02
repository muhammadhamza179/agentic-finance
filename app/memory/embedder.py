# app/memory/embedder.py

from datetime import datetime
from app.memory.vector_store import store_memory

async def embed_and_store_query(
    user_id: int,
    session_id: str,
    query_id: int,
    user_input: str,
    agent_response: str
):
    """
    Called after every completed query.
    Stores both the question and answer in vector memory.
    """
    # Store the query
    await store_memory(
        text=f"Question: {user_input}",
        metadata={
            "user_id": user_id,
            "session_id": session_id,
            "query_id": query_id,
            "type": "query",
            "timestamp": datetime.utcnow().isoformat()
        },
        doc_id=f"query_{query_id}"
    )
    
    # Store the response too — agent can recall its own past answers
    await store_memory(
        text=f"Answer: {agent_response}",
        metadata={
            "user_id": user_id,
            "session_id": session_id,
            "query_id": query_id,
            "type": "response",
            "timestamp": datetime.utcnow().isoformat()
        },
        doc_id=f"response_{query_id}"
    )