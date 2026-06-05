import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_TRENDS_ENABLE: bool = os.getenv("GOOGLE_TRENDS_ENABLE", "true").lower() == "true"
    REPORT_OUTPUT_FOLDER: str = os.getenv("REPORT_OUTPUT_FOLDER", "reports")
    TREND_LOOKBACK_DAYS: int = int(os.getenv("TREND_LOOKBACK_DAYS", "180"))
    MIN_MARGIN_PERCENT: float = float(os.getenv("MIN_MARGIN_PERCENT", "60"))
    CONTENT_IDEA_COUNT: int = int(os.getenv("CONTENT_IDEA_COUNT", "50"))
    MIN_CONTENT_UNIQUENESS: float = float(os.getenv("MIN_CONTENT_UNIQUENESS", "70"))

    AMAZON_API_KEY: str = os.getenv("AMAZON_API_KEY", "")
    AMAZON_ASSOCIATE_TAG: str = os.getenv("AMAZON_ASSOCIATE_TAG", "")
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "ProductAgent/1.0")

    PROVIDER_CACHE_TTL: int = int(os.getenv("PROVIDER_CACHE_TTL", "3600"))
    PROVIDER_RATE_LIMIT_DELAY: float = float(os.getenv("PROVIDER_RATE_LIMIT_DELAY", "1.0"))
    PROVIDER_MAX_RETRIES: int = int(os.getenv("PROVIDER_MAX_RETRIES", "2"))


settings = Settings()
