import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _mock_pool_with_conn(mock_get_pool: AsyncMock, mock_conn: AsyncMock) -> None:
    """Mock await get_pool() and async with pool.acquire() as conn."""
    mock_pool = MagicMock()
    acquire_ctx = AsyncMock()
    acquire_ctx.__aenter__.return_value = mock_conn
    acquire_ctx.__aexit__.return_value = None
    mock_pool.acquire.return_value = acquire_ctx
    mock_get_pool.return_value = mock_pool


# ── Tool tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_stock_price_success():
    mock_response = {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "211.45",
            "09. change": "-1.23",
            "10. change percent": "-0.58%",
            "06. volume": "48234100",
            "07. latest trading day": "2024-11-01",
            "08. previous close": "212.68",
            "02. open": "212.00",
            "03. high": "213.10",
            "04. low": "210.50"
        }
    }
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: mock_response,
            raise_for_status=lambda: None
        )
        
        from app.tools.stock_price import StockPriceTool
        tool = StockPriceTool()
        result = await tool.get_quote("AAPL")
    
    assert result["status"] == "success"
    assert result["data"]["symbol"] == "AAPL"
    assert result["data"]["price"] == 211.45


@pytest.mark.asyncio
async def test_stock_price_rate_limit():
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"Note": "API rate limit reached"},
            raise_for_status=lambda: None
        )
        
        from app.tools.stock_price import StockPriceTool
        tool = StockPriceTool()
        result = await tool.get_quote("AAPL")
    
    assert result["status"] == "rate_limited"


@pytest.mark.asyncio
async def test_news_sentiment_scoring():
    from app.tools.news_sentiment import NewsSentimentTool
    tool = NewsSentimentTool()
    
    positive_article = {
        "title": "Apple beats earnings with record profit and surge",
        "description": "Strong growth",
        "source": {"name": "Reuters"},
        "publishedAt": "2024-11-01T10:00:00Z",
        "url": "https://example.com"
    }
    
    result = tool._score_article(positive_article)
    assert result["score"] > 0


# ── API tests ──────────────────────────────────────────

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    username = f"testuser_{int(time.time())}"
    
    with patch("app.api.routes.get_pool", new_callable=AsyncMock) as mock_get_pool:
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(side_effect=[
            None,       # No existing user
            None,       # No existing email
            {"id": 1}   # Insert returns id
        ])
        _mock_pool_with_conn(mock_get_pool, mock_conn)
        
        r = client.post("/register", json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "TestPassword123"
        })
        assert r.status_code == 200
        assert r.json()["access_token"] is not None


def test_login_wrong_password():
    with patch("app.api.routes.get_pool", new_callable=AsyncMock) as mock_get_pool:
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        _mock_pool_with_conn(mock_get_pool, mock_conn)
        
        r = client.post("/login", json={
            "username": "doesnotexist",
            "password": "wrongpassword"
        })
        assert r.status_code == 401


def test_protected_route_requires_auth():
    r = client.get("/me")
    assert r.status_code == 403