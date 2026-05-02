# app/agent/tracer.py

from datetime import datetime
from typing import Any

class AgentTracer:
    """
    Records every step of an agent run for display and debugging.
    Think of this as a flight recorder for the agent loop.
    """
    
    def __init__(self, query: str):
        self.query = query
        self.started_at = datetime.utcnow()
        self.steps = []
    
    def log(self, stage: str, data: Any, note: str = ""):
        """Record one step in the trace."""
        self.steps.append({
            "stage": stage,
            "data": data,
            "note": note,
            "elapsed_ms": int(
                (datetime.utcnow() - self.started_at).total_seconds() * 1000
            )
        })
        print(f"[TRACE] {stage}: {note or str(data)[:80]}")
    
    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "started_at": self.started_at.isoformat(),
            "total_ms": int(
                (datetime.utcnow() - self.started_at).total_seconds() * 1000
            ),
            "steps": self.steps
        }