from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from app.api.auth import (
    hash_password, verify_password,
    create_token, get_current_user
)
from app.api.middleware import rate_limit
from app.memory.session import get_or_create_session
from app.database import get_pool
from app.tools.stock_price import stock_price_tool  # ← ADD THIS

router = APIRouter()

# ------------------------------------------------------------
# Request/Response Models
# ------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class QueryRequest(BaseModel):
    query: str

# ------------------------------------------------------------
# Auth Endpoints
# ------------------------------------------------------------

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE username = $1", body.username
        )
        if existing:
            raise HTTPException(400, "Username already taken")
        
        row = await conn.fetchrow(
            """INSERT INTO users (username, email, password_hash)
               VALUES ($1, $2, $3) RETURNING id""",
            body.username, body.email, hash_password(body.password)
        )
    
    token = create_token(row["id"], body.username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT id, password_hash FROM users WHERE username = $1",
            body.username
        )
    
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Invalid username or password")
    
    token = create_token(user["id"], body.username)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user_id": user["sub"], "username": user["username"]}


# ------------------------------------------------------------
# Stock Endpoint
# ------------------------------------------------------------

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Get real-time stock price for any symbol."""
    result = await stock_price_tool.get_quote(symbol)
    return result


# ------------------------------------------------------------
# Agent Endpoint
# ------------------------------------------------------------

@router.post("/query")
async def query_agent(
    body: QueryRequest,
    request: Request,
    user: dict = Depends(get_current_user)
):
    await rate_limit(request, user)
    
    user_id = int(user["sub"])
    session = await get_or_create_session(user_id)
    context = session.get_context()
    
    response = f"Agent received: '{body.query}' | Context: {len(context)} messages"
    
    await session.save_exchange(body.query, response)
    
    return {
        "status": "ok",
        "query": body.query,
        "user": user["username"],
        "session_id": session.session_id,
        "context_messages": len(context),
        "response": response
    }