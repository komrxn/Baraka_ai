"""Bot configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class BotConfig:
    """Bot configuration from environment."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # API
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
    
    # OpenAI (если нужен прямой доступ)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # Web App
    WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:3001/midas/")
    
    @classmethod
    def validate(cls):
        """Validate required config."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL is required")


config = BotConfig()
