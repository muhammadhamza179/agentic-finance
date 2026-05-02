import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import asyncpg
from app.config import settings

CREATE_TABLES = """
-- Users table (Step 9-10)
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions table (memory per user)
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     INTEGER REFERENCES users(id),
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);

-- Queries table (what users asked)
CREATE TABLE IF NOT EXISTS queries (
    id          SERIAL PRIMARY KEY,
    session_id  UUID REFERENCES sessions(id),
    user_input  TEXT NOT NULL,
    agent_response TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Tool calls table (what tools ran, with results)
CREATE TABLE IF NOT EXISTS tool_calls (
    id          SERIAL PRIMARY KEY,
    query_id    INTEGER REFERENCES queries(id),
    tool_name   TEXT NOT NULL,
    tool_input  JSONB,
    tool_output JSONB,
    latency_ms  INTEGER,
    status      TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Logs table (Step 8)
CREATE TABLE IF NOT EXISTS logs (
    id          SERIAL PRIMARY KEY,
    level       TEXT NOT NULL,
    event       TEXT NOT NULL,
    data        JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolio table (Step 5)
CREATE TABLE IF NOT EXISTS portfolio (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id),
    symbol      TEXT NOT NULL,
    shares      NUMERIC(12,4) NOT NULL,
    buy_price   NUMERIC(12,4) NOT NULL,
    added_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, symbol)
);
"""

async def init():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    await conn.execute(CREATE_TABLES)
    await conn.close()
    print("✓ All tables created")

asyncio.run(init())