import functools
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.api_client import BarakaAPIClient
from bot.config import config
from bot.i18n import t
from bot.user_storage import storage

def check_subscription(func):
    """
    Decorator to check if user has active subscription or trial.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
            return await func(update, context, *args, **kwargs)

        try:
            # We can optimize this by caching status in context.user_data
            # for a short period to avoid API spam, but for now strict check.
            token = storage.get_user_token(user.id)
            api = BarakaAPIClient(config.API_BASE_URL)
            api.set_token(token)
            status = await api.get_subscription_status(user.id)
            
            if status.get("is_active"):
                return await func(update, context, *args, **kwargs)
            
            # Not active
            lang = storage.get_user_language(user.id) or 'uz'
            
            keyboard = []
            if not status.get("is_trial_used"):
                keyboard.append([InlineKeyboardButton(t("subscription.activate_trial_btn", lang), callback_data="activate_trial")])
            
            keyboard.append([InlineKeyboardButton(t("subscription.buy_subscription_btn", lang), callback_data="buy_subscription")])
            
            text = (
                f"{t('subscription.access_restricted', lang)}\n\n"
                f"{t('subscription.feature_locked', lang)}"
            )
            
            if update.message:
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            elif update.callback_query:
                await update.callback_query.answer(t("subscription.access_restricted", lang), show_alert=True)
                # Optionally send a fresh message if it was a callback
                await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                
            return
            
        except Exception as e:
            print(f"Subscription check failed: {e}")
            # If API fails, maybe fail open or closed? 
            # For now, let's fail open to not block users on technical errors, 
            # OR fail closed safely. Let's return func to be safe during dev.
            return await func(update, context, *args, **kwargs)

    return wrapper
