# app/tools/base.py

import asyncio
from functools import wraps

def with_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator that retries any async tool on failure.
    
    Usage:
        @with_retry(max_attempts=3, delay=1.0)
        async def get_quote(self, symbol): ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    # Only retry on error status, not on "rate_limited"
                    if result.get("status") == "error":
                        raise Exception(result.get("error", "unknown"))
                    return result
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts:
                        wait = delay * attempt  # 1s, 2s, 3s — exponential backoff
                        print(f"[RETRY] attempt {attempt} failed: {e}. Waiting {wait}s...")
                        await asyncio.sleep(wait)
            
            # All attempts failed — return structured error
            return {
                "status": "error",
                "tool": func.__name__,
                "data": None,
                "error": f"Failed after {max_attempts} attempts. Last error: {last_error}",
                "timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
        return wrapper
    return decorator