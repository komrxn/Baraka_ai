"""Command handlers: /start, /help, etc."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging

from ..user_storage import storage
from ..help_messages import HELP_MESSAGES
from .common import get_main_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show registration or login options."""
    user = update.effective_user
    
    if storage.is_user_authorized(user.id):
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\nТы уже авторизован.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я помогу тебе вести учёт финансов.\n\n"
            "Для начала работы:\n"
            "/register - регистрация\n"
            "/login - вход",
            reply_markup=ReplyKeyboardRemove()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help with language selection."""
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
        ],
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="help_uz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Выбери язык / Choose language / Tilni tanlang:",
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
