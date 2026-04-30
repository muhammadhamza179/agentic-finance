from app.memory.postgres_store import save_query, update_session_active, create_session


class SessionMemory:
    """Holds conversation context for one user session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list = []
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.history.append({"role": role, "content": content})
        if len(self.history) > 20:
            self.history = self.history[-20:]
    
    async def save_exchange(self, user_input: str, agent_response: str):
        """Save a complete Q&A exchange to database."""
        self.add_message("user", user_input)
        self.add_message("assistant", agent_response)
        await save_query(self.session_id, user_input, agent_response)
        await update_session_active(self.session_id)
    
    def get_context(self) -> list:
        """Return the full conversation history for the agent."""
        return self.history


# Active sessions — maps user_id to their session
_active_sessions: dict = {}


async def get_or_create_session(user_id: int) -> SessionMemory:
    """
    Get the user's existing session or create a new one.
    Called at the start of every /query request.
    """
    if user_id not in _active_sessions:
        session_id = await create_session(user_id)
        _active_sessions[user_id] = SessionMemory(session_id)
    return _active_sessions[user_id]