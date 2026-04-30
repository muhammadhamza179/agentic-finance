import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Data APIs
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/financial_agent")
    
    # Auth
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    
    # Cache
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Agent behavior
    MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "10"))


settings = Settings()


def rotate_key(service: str, new_key: str):
    """
    Rotate an API key without restarting the app.
    In production, Step 34 automates this via secrets manager.
    """
    os.environ[service] = new_key
    print(f"[KEY ROTATION] {service} updated. Restart app to apply.")