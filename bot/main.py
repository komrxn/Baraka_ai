```python
"""Main bot entry point."""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

from config import config
from handlers import start, help_command, help_callback, get_balance, handle_text, handle_voice, handle_photo
from auth_handlers import register_conv, login_conv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # Auth handlers
    application.add_handler(register_conv)
    application.add_handler(login_conv)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", get_balance))
    
    # Callback handler for help language selection
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Start bot
    logger.info("🤖 Starting Midas Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
