from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.tools.stock_price import stock_price_tool
from app.database import get_pool, close_pool
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    required = {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "ALPHA_VANTAGE_API_KEY": settings.ALPHA_VANTAGE_API_KEY,
        "NEWS_API_KEY": settings.NEWS_API_KEY,
        "JWT_SECRET_KEY": settings.JWT_SECRET_KEY,
    }
    
    missing = [k for k, v in required.items() if not v or v == ""]
    if missing:
        print(f"⚠️ Warning: Missing env vars: {missing}")
    else:
        print("✓ All API keys present")
    
    try:
        pool = await get_pool()
        print("✓ Database pool ready")
    except Exception as e:
        print(f"⚠️ Database not available: {e}")
    
    print(f"✓ Using model: {settings.OPENAI_MODEL}")
    
    yield
    
    await stock_price_tool.close()
    await close_pool()
    print("✓ Cleaned up all connections")


app = FastAPI(title="Financial AI Agent", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}