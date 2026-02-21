
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

    # Robust Translation Logic
    # We avoid importing bot.i18n to prevent path/dependency issues in API container
    import json
    from pathlib import Path
    
    lang = user.language or 'uz'
    
    # Calculate path to bot/locales relative to this file
    # This file: api/services/notification.py
    # Locales: bot/locales
    # Path: ../../../bot/locales
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent # api/services/ -> api/ -> root
        locales_dir = project_root / "bot" / "locales"
        
        # Load specific file: subscription.json
        lang_file = locales_dir / lang / "subscription.json"
        
        with open(lang_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        def get_text(key):
            # key format: subscription.success_trial -> we need just success_trial since we loaded subscription.json
            if key.startswith("subscription."):
                key = key.replace("subscription.", "")
            return data.get(key, key) # Return key if not found
            
    except Exception as e:
        logger.error(f"Failed to load translations in notification service: {e}")
        # Fallback to key, escaped for Markdown
        def get_text(key): 
            return key.replace("_", "\\_").replace("*", "\\*")

    if message_key:
        message = get_text(message_key)
    else:
        # Fallback to logic based on subscription type
        sub_type = user.subscription_type or 'free'
        
        if sub_type == 'premium':
            message = get_text('success_premium')
        elif sub_type == 'pro':
            message = get_text('success_pro')
        elif sub_type == 'plus':
            message = get_text('success_plus')
        else:
            # For dynamic tier, we might not have it in this simple loader if it uses placeholders
            # But 'subscription_activated' uses {tier}.
            # Let's simple check
            raw_msg = get_text('subscription_activated')
            if raw_msg:
                message = raw_msg.replace("{tier}", sub_type.capitalize())
            else:
                message = f"Subscription {sub_type} activated!"

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

    import json
    from pathlib import Path

    lang = user.language or 'uz'
    
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        locales_dir = project_root / "bot" / "locales"
        lang_file = locales_dir / lang / "subscription.json"
        
        with open(lang_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        message = data.get("trial_ended", "Trial ended.")
        btn_text = data.get("buy_subscription_btn", "💎 Buy Subscription")
        if "trial_ended" not in data:
            raise ValueError("Key missing")
    except Exception as e:
        logger.error(f"Failed to load translations for expiration: {e}")
        if lang == 'ru':
            message = "⚠️ **Пробный период завершен.**\n\nВаш тариф автоматически изменен на **Базовый (Free)**."
            btn_text = "💎 Выбрать тариф"
        elif lang == 'en':
            message = "⚠️ **Trial period ended.**\n\nYour current plan has been changed to **Basic (Free)**."
            btn_text = "💎 Select Plan"
        else:
            message = "⚠️ **Sinov muddati yakunlandi.**\n\nSizning ta'rifingiz avtomatik tarzda **Asosiy (Free)** ga o'zgartirildi."
            btn_text = "💎 Tarifni tanlash"
    
    # Inline keyboard dictionary format for raw Telegram API
    reply_markup = {
        "inline_keyboard": [
            [{"text": btn_text, "callback_data": "buy_subscription"}]
        ]
    }

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send subscription expired message: {e}")

async def send_premium_upsell_message(user: User):
    """
    Send the premium trial upsell message to free users who haven't used their trial yet.
    """
    if not user.telegram_id:
        return

    import json
    from pathlib import Path

    lang = user.language or 'uz'
    
    try:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        locales_dir = project_root / "bot" / "locales"
        lang_file = locales_dir / lang / "subscription.json"
        
        with open(lang_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        message = data.get("registration_welcome", "Premium Trial Offer")
        btn_text = data.get("activate_trial_btn", "🚀 Activate Trial")
        if "registration_welcome" not in data:
            raise ValueError("Key missing")
    except Exception as e:
        logger.error(f"Failed to load translations for upsell: {e}")
        if lang == 'ru':
            message = "🔥 **Добро пожаловать в Baraka AI!**\n\nАктивируйте премиум в 1 клик: **3 дня подписки Premium абсолютно бесплатно.**"
            btn_text = "🚀 Попробовать бесплатно (3 дня)"
        elif lang == 'en':
            message = "🔥 **Welcome to Baraka AI!**\n\nActivate premium in 1 click: **3 days of Premium subscription absolutely free.**"
            btn_text = "🚀 Try Free (3 days)"
        else:
            message = "🔥 **Baraka AI'ga xush kelibsiz!**\n\nPremiumni 1 marta bosish orqali faollashtiring: **3 kunga Premium obunasi mutlaqo bepul.**"
            btn_text = "🚀 Bepul sinab ko'rish (3 kun)"
    
    # Inline keyboard dictionary format for raw Telegram API
    reply_markup = {
        "inline_keyboard": [
            [{"text": btn_text, "callback_data": "activate_trial"}]
        ]
    }

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": user.telegram_id,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send premium upsell message: {e}")
