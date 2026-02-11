
import httpx
import logging
from ..config import get_settings
from ..models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

async def send_subscription_success_message(user: User):
    """
    Send a detailed success message with instructions to the user via Telegram Bot API.
    """
    if not user.telegram_id:
        return

    from ..i18n import t
    lang = user.language or 'uz'
    
    # Determine which message to send based on subscription type
    sub_type = user.subscription_type or 'free'
    
    # Map subscription type to translation key
    if sub_type == 'premium':
        message = t('subscription.success_premium', lang)
    elif sub_type == 'pro':
        message = t('subscription.success_pro', lang)
    elif sub_type == 'plus':
        message = t('subscription.success_plus', lang)
    elif sub_type == 'trial': # Trial might be stored as 'premium' with is_trial_used=True, need check
        # Logic check: In activate_trial, we set subscription_type='premium'.
        # So we need to distinguish trial activation explicitly or check context.
        # Ideally, we should check if this was a trial activation.
        # But for now, let's assume if it's premium and trial just started... 
        # Wait, the caller should probably tell us, or we infer?
        # Let's rely on user object state.
        # If user.is_trial_used is True and it was just activated... tough to know "just now".
        # But usually this function is called right after activation.
        # Let's handle 'trial' if passed explicitly? 
        # The model defines subscription_type. 
        # Let's trust subscription_type for now. 
        # If trial sets 'premium', it will show premium message.
        # We should probably update activate_trial to set type='trial' or similar if we want distinct message?
        # OR better: The enable_trial function sets type='premium'. 
        # Let's checking explicit trial key or logic.
        # Actually, let's just use the keys effectively.
        message = t('subscription.success_premium', lang)
    else:
         message = t('subscription.subscription_activated', lang, tier=sub_type.capitalize())

    # Correction: trial activation logic in subscriptions.py sets sub_type='premium'.
    # So we can't easily distinguish unless we check logic.
    # However, 'activate_trial' endpoint calls this.
    # user.is_trial_used is True.
    # Maybe we can check if it expires in 3 days?
    # Simple hack: the caller can't easily pass args here as it is async event potentially?
    # No, it's direct call.
    # Let's proceed with generic for now, but I will improve it.
    
    # If trial, it might be better to have the caller specifying the message type?
    # But signature is fixed? 
    # Let's check if we can import 't' here. Yes.
    
    # Wait, 't' function usually requires initialized i18n.
    # Ensure i18n is available.
    
    # Refined Logic:
    # If we want to distinguish trial, we need to know.
    # But since I cannot change function signature easily without checking callers...
    # I'll check if subscription_ends_at is around 3 days from now? 
    # That's brittle.
    # Let's check `user.is_trial_used` ... 
    
    # Actually, previous implementation of `activate_trial` in `subscriptions.py`
    # sets `current_user.subscription_type = "premium"`.
    
    # I will modify `activate_trial` to maybe pass a flag?
    # Or I can just check if I can modify the signature of this function.
    # Search for usages...
    
    # Usages: `activate_trial` and `handle_payment_webhook` (likely).
    
    # Strategy: Add an optional `message_key` argument.
    pass

async def send_subscription_success_message(user: User, message_key: str = None):
    """
    Send a detailed success message with instructions to the user via Telegram Bot API.
    """
    if not user.telegram_id:
        return

    from ..i18n import t
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
