
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

    # TODO: Localize this message based on user.language
    lang = user.language or 'uz'
    
    # Message content based on language
    # Beautiful formatting, no raw numbers, focus on value
    if lang == 'ru':
        message = (
            "🎉 **Поздравляем! Ваш план обновлен!** 🚀\n\n"
            "Теперь ваши возможности стали еще шире с **Baraka AI**:\n\n"
            "🧠 **Умнее** — доступ к более мощной модели искусственного интеллекта.\n"
            "💬 **Больше общения** — увеличены лимиты на голосовые сообщения.\n"
            "📸 **Больше анализа** — распознавайте больше чеков и фото.\n"
            "⚡ **Быстрее** — приоритетная обработка ваших запросов.\n\n"
            "Спасибо, что выбираете нас! Мы продолжаем совершенствоваться для вас."
        )
    elif lang == 'en':
        message = (
            "🎉 **Congratulations! Plan Upgraded!** 🚀\n\n"
            "Your experience with **Baraka AI** just got better:\n\n"
            "🧠 **Smarter** — access to a more powerful AI model.\n"
            "💬 **More Voice** — increased limits for voice messages.\n"
            "📸 **More Vision** — scan more receipts and photos.\n"
            "⚡ **Faster** — priority processing for your requests.\n\n"
            "Thank you for choosing us! We keep improving for you."
        )
    else: # Default Uzbek
        message = (
            "🎉 **Tabriklaymiz! Rejangiz yangilandi!** 🚀\n\n"
            "Endi **Baraka AI** imkoniyatlari yanada kengaydi:\n\n"
            "🧠 **Aqlliroq** — kuchliroq sun'iy intellekt modeliga kirish.\n"
            "💬 **Ko'proq muloqot** — ovozli xabarlar uchun limitlar oshirildi.\n"
            "📸 **Ko'proq tahlil** — ko'proq chek va rasmlarni aniqlash imkoniyati.\n"
            "⚡ **Dammroq** — so'rovlaringiz ustuvor tartibda qayta ishlanadi.\n\n"
            "Bizni tanlaganingiz uchun rahmat! Siz uchun yaxshilanishda davom etamiz."
        )

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
