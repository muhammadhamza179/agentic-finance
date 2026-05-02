# app/memory/retriever.py

from app.memory.vector_store import search_memory

async def retrieve_relevant_context(
    user_id: int,
    current_query: str,
    top_k: int = 3
) -> str:
    """
    Finds past queries/answers semantically similar to the current one.
    Returns a formatted string ready to inject into the prompt.
    """
    results = await search_memory(
        query=current_query,
        user_id=user_id,
        top_k=top_k
    )
    
    if not results:
        return ""
    
    # Filter out very distant results (not really relevant)
    relevant = [r for r in results if r["distance"] < 0.5]
    
    if not relevant:
        return ""
    
    lines = ["Relevant past context:"]
    for r in relevant:
        lines.append(f"- {r['text']}")
    
    return "\n".join(lines)