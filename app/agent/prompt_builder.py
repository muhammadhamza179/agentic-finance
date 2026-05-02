from app.memory.retriever import retrieve_relevant_context
from app.memory.session import SessionMemory
from app.tools.registry import list_tools


async def build_prompt(
    user_input: str,
    user_id: int,
    session: SessionMemory,
    tool_result: str = None
) -> list[dict]:
    """
    Assembles the complete message list for the LLM API call.
    
    Order matters:
    1. System prompt (who the agent is)
    2. RAG context (semantic memory)
    3. Conversation history (recent turns)
    4. Current user message
    5. Tool result (if a tool was called)
    """
    
    # 1. System prompt — tools are auto-loaded from registry
    system = f"""You are a professional financial AI agent.

TOOLS YOU CAN USE:
{list_tools()}

HOW TO USE A TOOL:
When you need data, respond with ONLY this JSON (nothing else):
{{"tool": "tool_name", "parameters": {{"key": "value"}}}}

When you have enough information to answer, respond normally in plain text.
Always end financial advice with: "⚠️ Not financial advice."
"""
    
    messages = [{"role": "system", "content": system}]
    
    # 2. RAG: semantic memory
    rag_context = await retrieve_relevant_context(user_id, user_input)
    if rag_context:
        messages.append({
            "role": "system",
            "content": rag_context
        })
    
    # 3. Conversation history
    history_text = await session.format_for_prompt()
    if history_text:
        messages.append({
            "role": "system",
            "content": history_text
        })
    
    # 4. Current user message
    messages.append({"role": "user", "content": user_input})
    
    # 5. Tool result
    if tool_result:
        messages.append({
            "role": "system",
            "content": f"Tool result:\n{tool_result}"
        })
    
    return messages