"""Photo/receipt handler - Vision AI integration."""
from telegram import Update
from telegram.ext import ContextTypes
import logging
import base64

from ..user_storage import storage
from ..api_client import BarakaAPIClient
from ..config import config
from .common import with_auth_check, get_main_keyboard, send_typing_action
from ..confirmation_handlers import show_transaction_confirmation
from ..i18n import t
from ..utils.subscription import check_subscription

logger = logging.getLogger(__name__)


@send_typing_action
@send_typing_action
# @check_subscription <-- REMOVED
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages (receipt scanning with Vision AI)."""
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    if not storage.is_user_authorized(user_id):
        # await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        await update.message.reply_text(t('auth.common.auth_required', lang))
        return
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # 1. Check Limits (Freemium)
        me = await api.get_me()
        
        is_premium = me.get('is_premium', False)
        
        if not is_premium:
            usage = me.get('photo_usage_count', 0)
            if usage >= 10:
                # Limit reached
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                sub_keyboard = InlineKeyboardMarkup([
                     [InlineKeyboardButton(t("subscription.buy_subscription_btn", lang), callback_data="buy_subscription")]
                ])
                await update.message.reply_text(
                    f"🔒 {t('subscription.limit_reached_photo', lang)} (10/10).\n\n{t('subscription.upgrade_to_continue', lang)}",
                    reply_markup=sub_keyboard
                )
                return

        # await update.message.reply_text("📸 Анализирую фото...")
        await update.message.reply_text(t('common.common.loading', lang)) # Using loading or I could add specific "analyzing" key
        await update.message.chat.send_action(action="typing")
        
        # Download photo (highest resolution)
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Extract text using GPT-4o Vision
        from openai import AsyncOpenAI
        vision_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
        b64_image = base64.b64encode(bytes(photo_bytes)).decode('utf-8')
        
        vision_response = await vision_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Извлеки из этого чека/квитанции сумму и описание. Напиши простым текстом что на чеке."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        
        extracted_text = vision_response.choices[0].message.content
        logger.info(f"Extracted from photo: {extracted_text}")
        
        # Process with AI agent
        async def _process_receipt():
            from ..ai import AIAgent
            agent = AIAgent(api)
            return await agent.process_message(user_id, f"Вот чек: {extracted_text}")
        
        result = await with_auth_check(update, user_id, _process_receipt)
        if result is None:
            return  # Auth failed
        
        # Extract response and transactions
        response_text = result.get("response", "")
        parsed_transactions = result.get("parsed_transactions", [])
        
        # Send response
        try:
            await update.message.reply_text(
                f"📸 *С чека:* {extracted_text}\n\n{response_text}",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(lang)
            )
        except Exception:
            await update.message.reply_text(
                f"📸 С чека: {extracted_text}\n\n{response_text}",
                reply_markup=get_main_keyboard(lang)
            )
        
        # Show confirmations
        if parsed_transactions:
            for tx_data in parsed_transactions:
                await show_transaction_confirmation(update, user_id, tx_data)
        
        # Increment usage
        if not is_premium:
             try:
                await api.increment_usage('photo')
             except Exception as ex:
                logger.error(f"Failed to increment usage: {ex}")
                
    except Exception as e:
        logger.exception(f"Photo error: {e}")
        await update.message.reply_text(
            # "❌ Не смог обработать фото.\nПопробуй сфотографировать получше или введи вручную.",
            t('common.common.error', lang),
            reply_markup=get_main_keyboard(lang)
        )
