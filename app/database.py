# app/database.py

import asyncpg
from app.config import settings

# Connection pool — not one connection per request
_pool = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,   # Always keep 2 connections warm
            max_size=10   # Max 10 concurrent DB operations
        )
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None