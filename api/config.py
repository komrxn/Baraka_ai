from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str
    
    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days
    
    # OpenAI
    openai_api_key: str
    
    # Telegram
    telegram_bot_token: str

    # Click.uz
    click_secret_key: str = "test_key"
    click_service_id: str = "test_ems"
    click_merchant_id: str = "test_id"

    # Payme
    payme_merchant_id: str = "test_merchant"
    payme_key: str = "test_key"
    payme_test_mode: bool = False

    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
