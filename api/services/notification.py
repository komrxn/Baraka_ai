
import httpx
import logging
from ..config import get_settings
from ..models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

async def send_subscription_success_message(user: User, message_key: str = None):
    """
    Send a detailed success message with instructions to the user via Telegram Bot API.
    """
    if not user.telegram_id:
        return

    try:
        from bot.i18n import t
    except ImportError:
        logger.error("Could not import i18n from bot module (send_subscription_success_message).")
        return

    lang = user.language or 'uz'
    
    if message_key:
        message = t(message_key, lang)
    else:
        # Fallback to logic based on subscription type
        sub_type = user.subscription_type or 'free'
        
        if sub_type == 'premium':
            message = t('subscription.success_premium', lang)
        elif sub_type == 'pro':
            message = t('subscription.success_pro', lang)
        elif sub_type == 'plus':
            message = t('subscription.success_plus', lang)
        else:
             message = t('subscription.subscription_activated', lang, tier=sub_type.capitalize())

    # Send via Telegram Bot API
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send subscription success message: {e}")

async def send_subscription_expired_message(user: User):
    """
    Send subscription expired notification.
    """
    if not user.telegram_id:
        return

    lang = user.language or 'uz'
    
    if lang == 'ru':
        message = (
            "⏳ **Срок действия пробного периода истек**\n\n"
            "Ваш тариф изменен на **Free**.\n"
            "Чтобы вернуть безлимитные возможности и доступ к Premium AI, обновите подписку.\n\n"
            "👉 Нажмите кнопку **Baraka AI PLUS** в меню для выбора тарифа."
        )
    elif lang == 'en':
        message = (
            "⏳ **Trial period expired**\n\n"
            "Your plan has been changed to **Free**.\n"
            "To restore unlimited features and Premium AI access, please upgrade your subscription.\n\n"
            "👉 Press **Baraka AI PLUS** in the menu to select a plan."
        )
    else: # Default Uzbek
        message = (
            "⏳ **Sinov davri tugadi**\n\n"
            "Sizning tarifingiz **Free** ga o'zgartirildi.\n"
            "Cheksiz imkoniyatlar va Premium AI dan foydalanish uchun obunani yangilang.\n\n"
            "👉 Tarifni tanlash uchun menyuda **Baraka AI PLUS** tugmasini bosing."
        )

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send subscription expired message: {e}")
