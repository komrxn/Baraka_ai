"""Common utilities for handlers."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
import logging
from functools import wraps

from ..user_storage import storage
from ..api_client import BarakaAPIClient, UnauthorizedError
from ..i18n import t

logger = logging.getLogger(__name__)


def send_typing_action(func):
    """Sends typing action while processing command."""
    @wraps(func)
    async def command_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            if update and update.effective_user:
                 user = update.effective_user
                 user_name = user.full_name or user.first_name or "Unknown"
                 # Log action with user info
                 logger.info(f"👤 User Activity [{user.id} | {user_name}]: Handler '{func.__name__}' triggered")

            if update and update.effective_message:
                await update.effective_message.reply_chat_action(ChatAction.TYPING)
        except Exception as e:
            # Ignore errors if sending action fails (e.g. invalid chat)
            logger.debug(f"Failed to send typing action: {e}")
            pass
            
        return await func(update, context, *args, **kwargs)
    return command_func


async def with_auth_check(update: Update, user_id: int, api_call):
    """Execute API call with automatic 401 error handling."""
    try:
        return await api_call()
    except UnauthorizedError:
        storage.clear_user_token(user_id)
        lang = storage.get_user_language(user_id) or 'uz'
        
        # Show login button
        keyboard = [
            [KeyboardButton("🔑 Kirish / Войти / Login")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        msg = (
            "⚠️ Avtorizatsiya talab qilinadi\n"
            "⚠️ Требуется авторизация\n"
            "⚠️ Authorization required\n\n"
            "👇 Kirish / Войти / Login:"
        )
        
        await update.message.reply_text(msg, reply_markup=reply_markup)
        logger.info(f"User {user_id} token expired, prompted to re-authenticate")
        return None
    except Exception as e:
        raise


def get_main_keyboard(lang: str = 'uz', subscription_type: str = 'free'):
    """Get main menu keyboard with localized buttons."""
    # Currency button text
    currency_texts = {
        'ru': "💱 Курс валют",
        'uz': "💱 Valyuta kursi",
        'en': "💱 Exchange Rates"
    }
    currency_btn_text = currency_texts.get(lang, currency_texts['uz'])
    
    keyboard = [
        [
            KeyboardButton(t('common.buttons.balance', lang)),
            KeyboardButton(t('common.buttons.statistics', lang))
        ],
        [KeyboardButton(currency_btn_text)],  # Always show currency button
        [
            KeyboardButton("Baraka AI PLUS 🌟"),
            KeyboardButton(t('common.buttons.instructions', lang))
        ],
        [KeyboardButton(t('common.buttons.support', lang))],
        [KeyboardButton(t('common.buttons.delete', lang))]
    ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)



async def get_keyboard_for_user(user_id: int, lang: str = 'uz'):
    """Get main keyboard with subscription-aware features.
    
    Fetches user's subscription status and returns appropriate keyboard.
    """
    from ..config import config
    
    subscription_type = 'free'
    token = storage.get_user_token(user_id)
    
    if token:
        try:
            api = BarakaAPIClient(config.API_BASE_URL)
            api.set_token(token)
            sub_status = await api.get_subscription_status(user_id)
            subscription_type = sub_status.get("subscription_type", "free")
        except Exception as e:
            logger.debug(f"Could not fetch subscription for keyboard: {e}")
    
    return get_main_keyboard(lang, subscription_type)

