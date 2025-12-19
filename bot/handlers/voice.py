"""Voice message handler module."""
import logging
import io
from telegram import Update
from telegram.ext import ContextTypes
from io import BytesIO
import httpx

from ..api_client import MidasAPIClient
from ..config import config
from ..user_storage import storage
from ..ai_agent import AIAgent
from ..transaction_actions import show_transaction_with_actions
from .common import with_auth_check, get_main_keyboard

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - transcribe and process with AI."""
    user_id = update.effective_user.id
    
    # Auth check
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        await update.message.reply_text("🎤 Слушаю...")
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
        
        # Show what was heard
        # await update.message.reply_text(f"🎤 {transcribed_text}")
        
        # Process as if it was a text message
        await process_text_message(update, context, transcribed_text, user_id)

    except Exception as e:
        logger.error(f"Voice error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке голосового сообщения.\nПопробуй ещё раз или напиши текстом.",
            reply_markup=get_main_keyboard()
        )
