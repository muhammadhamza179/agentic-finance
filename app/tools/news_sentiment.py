# app/tools/news_sentiment.py

import httpx
from datetime import datetime
from app.config import settings

class NewsSentimentTool:
    BASE_URL = "https://newsapi.org/v2/everything"
    
    async def get_news(self, company: str, days: int = 3) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params={
                    "q": company,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 5,
                    "apiKey": settings.NEWS_API_KEY
                })
                response.raise_for_status()
                data = response.json()
            
            articles = data.get("articles", [])
            scored = [self._score_article(a) for a in articles]
            
            avg_score = sum(a["score"] for a in scored) / len(scored) if scored else 0
            
            return {
                "status": "success",
                "tool": "news_sentiment",
                "data": {
                    "company": company,
                    "articles": scored,
                    "average_sentiment": round(avg_score, 2),
                    "sentiment_label": self._label(avg_score),
                    "article_count": len(scored)
                },
                "error": None,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error", "tool": "news_sentiment",
                "data": None, "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _score_article(self, article: dict) -> dict:
        """Simple keyword-based sentiment. No ML dependency needed."""
        text = (
            (article.get("title") or "") + " " +
            (article.get("description") or "")
        ).lower()
        
        positive = ["beat", "surge", "profit", "growth", "rally",
                    "record", "strong", "upgrade", "buy", "gain"]
        negative = ["miss", "fall", "loss", "decline", "cut",
                    "warn", "downgrade", "sell", "drop", "risk"]
        
        pos = sum(1 for w in positive if w in text)
        neg = sum(1 for w in negative if w in text)
        
        score = (pos - neg) / max(pos + neg, 1)  # -1 to +1
        
        return {
            "title": article.get("title", "")[:100],
            "source": article.get("source", {}).get("name", ""),
            "published": article.get("publishedAt", "")[:10],
            "url": article.get("url", ""),
            "score": round(score, 2)
        }
    
    def _label(self, score: float) -> str:
        if score > 0.2:   return "positive"
        if score < -0.2:  return "negative"
        return "neutral"

news_sentiment_tool = NewsSentimentTool()