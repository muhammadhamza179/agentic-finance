# 🤖 FinAgent — AI-Powered Financial Analysis Agent

> A production-grade AI agent for real-time financial analysis.
> Built with FastAPI, OpenAI, Alpha Vantage, and a multi-agent architecture.

[![CI](https://github.com/muhammadhamza179/agentic-finance/actions/workflows/ci.yml/badge.svg)](https://github.com/muhammadhamza179/agentic-finance/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)

## 🚀 Quick Demo

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "Should I invest in Apple right now?"}'


  Live API docs: http://127.0.0.1:8000/docs

✨ What It Does
📈 Stock Analysis — Live prices, 30-day history, technical signals

🔍 Fundamentals — P/E, EPS, margins, analyst targets, beta

📰 News Sentiment — Real-time news + NLP scoring

💼 Portfolio Tracking — Live P&L, allocation charts

🌎 Macro Context — Inflation, interest rates, GDP

🧠 RAG Memory — Semantic search across past conversations

🏗️ Architecture
Multi-agent system:

Planner → decides which of 8 tools to call

Executor → runs tools in parallel (~1 second)

Specialists → 3 agents interpret results

Synthesizer → writes the final answer

🛠️ Tech Stack
Layer	Technology
API	FastAPI + uvicorn
LLM	OpenAI GPT-4o + GPT-4o-mini
Data	Alpha Vantage + NewsAPI
Database	PostgreSQL (Neon.tech)
Vector DB	ChromaDB
Cache	Redis
Frontend	Streamlit + Plotly
Auth	JWT + bcrypt
CI/CD	GitHub Actions + Railway


git clone https://github.com/muhammadhamza179/agentic-finance.git
cd agentic-finance
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python scripts/init_db.py
uvicorn app.main:app --reload

📊 Streamlit Dashboard
cd streamlit_app
streamlit run app.py

🧪 Tests
pytest tests/ -v                           # Unit tests
locust -f tests/load_test.py               # Load testing
python scripts/model_benchmark.py       


💰 Cost Model (per query)
Component	Model	Avg Cost
Planning	gpt-4o-mini	$0.00011
Specialists	gpt-4o-mini	$0.00022
Synthesis	gpt-4o	$0.0050
Total		~$0.005

📁 Project Structure

app/
├── main.py # FastAPI entrypoint with lifespan
├── config.py # Settings from .env with hot-reload
├── database.py # PostgreSQL connection pool
│
├── agent/ # Multi-agent system
│ ├── loop.py # Think → Plan → Execute → Synthesize
│ ├── planner.py # GPT-4o-mini decides which tools to call
│ ├── executor.py # Runs tools in parallel
│ ├── prompt_builder.py # Assembles LLM prompt with RAG context
│ ├── tracer.py # Logs every agent step
│ └── specialists/ # Expert analysis agents
│ ├── stock_agent.py # Interprets price & technical data
│ ├── news_agent.py # Analyzes sentiment patterns
│ └── risk_agent.py # Evaluates investment risk
│
├── tools/ # 8 financial data tools
│ ├── registry.py # Dynamic tool loader
│ ├── base.py # Retry decorator with backoff
│ ├── stock_price.py # Live prices (Alpha Vantage)
│ ├── news_sentiment.py # News scoring (NewsAPI)
│ ├── roi_calculator.py # Return on investment
│ ├── risk_scoring.py # 1-10 risk assessment
│ ├── portfolio_tracker.py # Live P&L with charts
│ ├── earnings_calendar.py # Earnings dates
│ ├── macro_indicators.py # Inflation, rates, GDP
│ └── company_fundamentals.py # P/E, EPS, margins, beta
│
├── memory/ # Memory system
│ ├── session.py # Per-user conversation context
│ ├── postgres_store.py # SQL persistence
│ ├── vector_store.py # ChromaDB semantic search
│ ├── embedder.py # OpenAI embeddings
│ ├── retriever.py # RAG context retrieval
│ └── compressor.py # Conversation summarization
│
├── api/ # API layer
│ ├── routes.py # All endpoints (/query, /register, etc.)
│ ├── auth.py # JWT + bcrypt authentication
│ └── middleware.py # Rate limiting + latency tracking
│
├── logging/ # Observability
│ ├── query_logger.py # Structured query logging
│ ├── cost_tracker.py # OpenAI token/cost tracking
│ ├── latency_tracker.py # P50/P95/P99 latency
│ └── alerter.py # Slack alerts on errors
│
├── cache/ # Performance
│ └── redis_cache.py # Response cache (5-min TTL)
│
├── streamlit_app/ # Frontend
│ ├── app.py # Chat UI with auth
│ └── charts.py # Candlestick, pie, bar charts
│
tests/ # Testing
├── test_tools.py # Unit tests (7/7 passing)
├── eval_suite.py # Agent evaluation
└── load_test.py # Locust load testing

scripts/ # Utilities
├── init_db.py # Create all 6 tables
└── model_benchmark.py # GPT-4o vs GPT-4o-mini

docs/
└── architecture.md # Full system design doc

.github/workflows/
├── ci.yml # Automated testing + eval
└── deploy.yml # Auto-deploy to Railway

👤 Author
Muhammad Hamza — GitHub

📝 License
MIT


---

## 👤 Author

**Muhammad Hamza**
- [GitHub](https://github.com/muhammadhamza179)
- [LinkedIn](https://www.linkedin.com/in/muhammad-hamza-23893a176)

