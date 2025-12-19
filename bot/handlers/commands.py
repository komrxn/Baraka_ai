"""Command handlers: /start, /help, etc."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging

from ..user_storage import storage
from ..help_messages import HELP_MESSAGES
from ..lang_messages import get_message
from .common import get_main_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show registration or login options."""
    user = update.effective_user
    # Get lang if available (if user exists in storage)
    lang = storage.get_user_language(user.id) or 'uz'
    
    if storage.is_user_authorized(user.id):
        await update.message.reply_text(
            get_message(lang, 'welcome_back', name=user.first_name),
            reply_markup=get_main_keyboard(lang)
        )
    else:
        # For new users, maybe try to guess lang from Telegram user.language_code
        # But for now default to UZ or what message keys say
        await update.message.reply_text(
            get_message(lang, 'welcome_new', name=user.first_name),
            reply_markup=ReplyKeyboardRemove()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help with language selection."""
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz' # Default for menu prompt
    
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
        ],
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="help_uz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        get_message(lang, 'choose_language'),
        reply_markup=reply_markup
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help language selection callback."""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]  # Extract 'ru', 'en', or 'uz'
    help_text = HELP_MESSAGES.get(lang, HELP_MESSAGES['ru'])
    
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown'
    )
