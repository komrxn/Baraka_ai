"""Command handlers: /start, /help, etc."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, CallbackQueryHandler
import logging

from ..user_storage import storage
from ..help_messages import HELP_MESSAGES
from ..i18n import t
from .common import get_main_keyboard

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show language selection or main menu."""
    user = update.effective_user
    lang = storage.get_user_language(user.id)
    
    if storage.is_user_authorized(user.id):
        # Existing user
        if not lang:
            lang = 'uz'
        await update.message.reply_text(
            t('auth.registration.welcome_back', lang, name=user.first_name),
            reply_markup=get_main_keyboard(lang)
        )
    else:
        # New user - show language selection first
        if not lang:
            # First time - show language selector
            keyboard = [
                [
                    InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz"),
                    InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
                ],
                [InlineKeyboardButton("🇬🇧 English", callback_data="setlang_en")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🌍 Choose your language / Tilni tanlang / Выберите язык:",
                reply_markup=reply_markup
            )
        else:
            # Language already set, show welcome
            await update.message.reply_text(
                t('auth.registration.welcome_new', lang, name=user.first_name),
                reply_markup=ReplyKeyboardRemove()
            )


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    
    # Extract language from callback_data: "setlang_uz" -> "uz"
    lang = query.data.split('_')[1]
    user_id = query.from_user.id
    
    # Save language preference
    storage.set_user_language(user_id, lang)
    
    # Show welcome message and registration prompt
    await query.edit_message_text(
        t('auth.registration.welcome_new', lang, name=query.from_user.first_name)
    )
    
    # Prompt to register
    await query.message.reply_text(
        f"{t('auth.common.auth_required', lang)}\n\n"
        "📝 /register\n"
        "🔑 /login"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help with language selection."""
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
        ],
        [InlineKeyboardButton("🇺🇿 O'zbek", callback_data="help_uz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        t('auth.common.choose_language', lang),
        reply_markup=reply_markup
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle help language selection callback."""
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    help_text = HELP_MESSAGES.get(lang, HELP_MESSAGES['ru'])
    
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown'
    )


# Export callback handlers
language_selector_handler = CallbackQueryHandler(language_callback, pattern="^setlang_")
help_selector_handler = CallbackQueryHandler(help_callback, pattern="^help_")
