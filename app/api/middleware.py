# app/api/middleware.py

from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from app.config import settings

# In-memory rate limiter — simple and sufficient for now
# Step 39 upgrades this to Redis for multi-server support
_request_counts: dict = defaultdict(list)

async def rate_limit(request: Request, user: dict):
    """
    Call this inside protected endpoints.
    Allows MAX N requests per user per 60 seconds.
    """
    user_id = user["sub"]
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=60)
    
    # Remove timestamps older than 60 seconds
    _request_counts[user_id] = [
        ts for ts in _request_counts[user_id]
        if ts > window_start
    ]
    
    if len(_request_counts[user_id]) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {settings.RATE_LIMIT_PER_MINUTE} requests/minute."
        )
    
    _request_counts[user_id].append(now)