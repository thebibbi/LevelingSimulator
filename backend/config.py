"""
Configuration Management for Platform Leveling API
Uses pydantic-settings for environment variable management
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Server settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # CORS settings
    cors_origins: str = Field(
        default="http://localhost:3000",
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed origins",
    )

    # Security
    api_key: str = Field(default="", env="API_KEY")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Optional: Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")

    # Optional: Database
    database_url: str = Field(default="sqlite:///./leveling.db", env="DATABASE_URL")
    database_enabled: bool = Field(default=False, env="DATABASE_ENABLED")

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
