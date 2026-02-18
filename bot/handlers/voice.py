"""Voice message handler module."""
import logging
import io
from telegram import Update
from telegram.ext import ContextTypes
import httpx

from ..api_client import BarakaAPIClient
from ..config import config
from ..user_storage import storage
from ..ai import AIAgent
from ..transaction_actions import show_transaction_with_actions
from ..i18n import t
from .common import get_main_keyboard, send_typing_action
from ..utils.subscription import check_subscription

logger = logging.getLogger(__name__)


@send_typing_action
@check_subscription
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and process with AI."""
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Check limit for Freemium
    # We fetch status not by API but by storage/cache or optimize later.
    # For now, let's fetch user info to get counters?
    # Actually `check_subscription` decorator might be too strict if we just want to allow 20 limits.
    # Auth check
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text(t('auth.common.auth_required', lang))
        return
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # 1. Get user info (with is_premium and counters)
        # 2. If is_premium, proceed.
        # 3. If !is_premium, check counter < 20.
        # 4. If limit reached, ask to subscribe.
        
        # NOTE: We can't use `check_subscription` decorator here anymore because it blocks EVERYTHING if not premium/trial.
        # We need to remove the decorator and handle logic inside.

        # 1. Check Limits (Freemium)
        me = await api.get_me()
        user_info = me
        
        # Determine strict 'is_active' status
        is_active = user_info.get('is_active', False)
        
        # If not active, check usage
        if not is_active:
            usage = user_info.get('voice_usage_count', 0)
            if usage >= 20:
                # Limit reached
                keyboard = get_main_keyboard(lang) # Or subscription keyboard
                sub_keyboard = InlineKeyboardMarkup([
                     [InlineKeyboardButton(t("subscription.buy_subscription_btn", lang), callback_data="buy_subscription")]
                ])
                await update.message.reply_text(
                    f"🔒 {t('subscription.limit_reached_voice', lang)} (20/20).\n\n{t('subscription.upgrade_to_continue', lang)}",
                    reply_markup=sub_keyboard
                )
                return

        await update.message.reply_text(t('transactions.voice.listening', lang))
        await update.message.chat.send_action(action="typing")
        
        # Download voice
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        
        # Transcribe using UzbekVoice.AI STT
        audio_file = io.BytesIO(bytes(voice_bytes))
        audio_file.name = "voice.ogg"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            stt_response = await client.post(
                config.UZAI_STT_URL,
                headers={"Authorization": config.UZAI_API_KEY},
                files={"file": ("voice.ogg", audio_file, "audio/ogg")},
                data={
                    "language": "ru-uz",
                    "blocking": "true",
                    "return_offsets": "false",
                    "run_diarization": "false"
                }
            )
            stt_response.raise_for_status()
            stt_result = stt_response.json()
        
        logger.info(f"UzbekVoice.AI response: {stt_result}")
        
        # Parse response
        result = stt_result.get("result", {})
        transcribed_text = result.get("text", "").strip()
        
        if not transcribed_text:
            logger.error(f"Empty transcription: {stt_result}")
            raise ValueError(f"No text in response")
        
        logger.info(f"Transcribed: {transcribed_text}")
        
        # Process transcribed text using common pipeline
        from .messages import process_text_message
        
        # Process as if it was a text message
        await process_text_message(update, context, transcribed_text, user_id)
        
        # Increment usage counter if success (and not active)
        if not is_active:
            # We need an endpoint to increment usage?
            # Or the API should do it when processing transaction?
            # Ideally API handles it. But we used external STT here.
            try:
                await api.increment_usage('voice')
            except Exception as ex:
                logger.error(f"Failed to increment usage: {ex}")

    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text(
            t('transactions.voice.error', lang),
            reply_markup=get_main_keyboard(lang)
        )
