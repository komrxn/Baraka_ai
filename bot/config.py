"""Configuration for Telegram bot."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Bot configuration."""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # API
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # UzbekVoice AI (for STT)
    UZAI_API_KEY = os.getenv("UZAI_API_KEY")
    UZAI_STT_URL = "https://uzbekvoice.ai/api/v1/stt"
    
    # Web App
    WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:3001/midas/")
    
    @classmethod
    def validate(cls):
        """Validate required config."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL is required")


config = Config()
