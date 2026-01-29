"""
Configuration management for Agentic Buyer backend.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Best Buy API
    bestbuy_api_key: str = os.getenv("BESTBUY_API_KEY")
    
    # eBay API
    ebay_client_id: str = os.getenv("EBAY_CLIENT_ID")
    ebay_client_secret: str = os.getenv("EBAY_CLIENT_SECRET")
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentic_buyer"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Cache settings
    cache_ttl_seconds: int = 600  # 10 minutes
    
    # API settings
    max_results_per_source: int = 25
    request_timeout_seconds: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
