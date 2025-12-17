"""Main bot entry point."""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import config
from .handlers import start, get_balance, handle_text, handle_voice, handle_photo, help_command
from .auth_handlers import register_conv, login_conv

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Validate config
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return
    
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Auth conversation handlers (priority)
    application.add_handler(register_conv)
    application.add_handler(login_conv)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", get_balance))
    application.add_handler(CommandHandler("help", help_command))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Start bot
    logger.info("🤖 Starting Midas Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
