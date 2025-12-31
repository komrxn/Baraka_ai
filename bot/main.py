"""Main bot entry point."""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from bot.config import config
from bot.handlers import (
    handle_text,
    handle_voice,
    handle_photo
)
from bot.handlers.commands import start, help_command, help_callback, language_selector_handler
from bot.handlers.balance import get_balance
from bot.auth_handlers import register_conv, login_conv
from bot.transaction_actions import transaction_action_handler
from bot.debt_actions import debt_action_handler

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


from telegram.request import HTTPXRequest

def main():
    """Start the bot."""
    # Increase timeouts for better stability in slow networks
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).request(request).build()
    
    # Auth conversation handlers (priority)
    application.add_handler(register_conv)
    application.add_handler(login_conv)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", get_balance))
    application.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    application.add_handler(language_selector_handler)  # Language selection at /start
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    
    # Callback handler for transaction actions (Edit/Delete)
    application.add_handler(transaction_action_handler)
    application.add_handler(debt_action_handler)
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Start bot
    logger.info("🤖 Starting Baraka Ai Telegram Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
