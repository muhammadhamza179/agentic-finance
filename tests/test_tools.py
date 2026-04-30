import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from app.tools.news_sentiment import news_sentiment_tool

async def test():
    result = await news_sentiment_tool.get_news("Apple")
    print(result["data"]["sentiment_label"])  # positive / neutral / negative

asyncio.run(test())