# oracle/app/config.py
"""
Application configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "MSME Finance Oracle"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:Admin@123@localhost:5432/msme_finance"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Blockchain
    POLYGON_RPC_URL: str = "https://polygon-mumbai.g.alchemy.com/v2/demo"
    ORACLE_PRIVATE_KEY: str = "0x0000000000000000000000000000000000000000000000000000000000000000"
    ORACLE_ADDRESS: str = "0x0000000000000000000000000000000000000000"
    
    # Contract Addresses (will be set after deployment)
    ORDER_FACTORY_ADDRESS: Optional[str] = None
    ORACLE_REGISTRY_ADDRESS: Optional[str] = None
    
    # GeM Portal Credentials
    GEM_PORTAL_URL: str = "https://gem.gov.in"
    GEM_PORTAL_USERNAME: Optional[str] = None
    GEM_PORTAL_PASSWORD: Optional[str] = None
    
    # GSTN API
    GSTN_API_URL: str = "https://api.gst.gov.in"
    GSTN_API_KEY: Optional[str] = None
    GSTN_CLIENT_ID: Optional[str] = None
    GSTN_CLIENT_SECRET: Optional[str] = None
    
    # IPFS (Pinata)
    PINATA_API_KEY: Optional[str] = None
    PINATA_SECRET_KEY: Optional[str] = None
    PINATA_API_URL: str = "https://api.pinata.cloud"
    
    # Banking API
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_SECRET: str = "change-this-jwt-secret-in-production"
    ENCRYPTION_PASSWORD: str = "change-this-encryption-password"
    
    # Scraping Settings
    SCRAPE_INTERVAL_MINUTES: int = 15
    SCRAPE_TIMEOUT_SECONDS: int = 30
    MAX_RETRY_ATTEMPTS: int = 3
    
    # Monitoring
    ENABLE_PROMETHEUS: bool = True
    SENTRY_DSN: Optional[str] = None
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings (for dependency injection)"""
    return settings


# Test if module loads
if __name__ == "__main__":
    print("Configuration loaded successfully!")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.DATABASE_URL[:30]}...")
    print(f"GeM Portal: {settings.GEM_PORTAL_URL}")