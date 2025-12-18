"""Voice message handler."""
from telegram import Update
from telegram.ext import ContextTypes
import logging
import httpx
import io

from ..user_storage import storage
from ..api_client import MidasAPIClient
from ..config import config
from .common import with_auth_check, get_main_keyboard
from ..confirmation_handlers import show_transaction_confirmation

logger = logging.getLogger(__name__)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages."""
    if not storage.is_user_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    user_id = update.effective_user.id
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
        
        # Use AI agent to process
        async def _process_transcribed():
            from ..ai_agent import AIAgent
            agent = AIAgent(api)
            return await agent.process_message(user_id, transcribed_text)
        
        result = await with_auth_check(update, user_id, _process_transcribed)
        if result is None:
            return  # Auth failed
        
        # Extract response and transactions
        response_text = result.get("response", "")
        parsed_transactions = result.get("parsed_transactions", [])
        
        # Only send AI response if no transactions (confirmations will show the data)
        if not parsed_transactions:
            try:
                await update.message.reply_text(
                    f"🎤 *Ты сказал:* {transcribed_text}\n\n{response_text}",
                    parse_mode='Markdown',
                    reply_markup=get_main_keyboard()
                )
            except Exception:
                await update.message.reply_text(
                    f"🎤 Ты сказал: {transcribed_text}\n\n{response_text}",
                    reply_markup=get_main_keyboard()
                )
        
        # Show confirmations (this is the main response when transactions exist)
        if parsed_transactions:
            for tx_data in parsed_transactions:
                await show_transaction_confirmation(update, user_id, tx_data)
                
    except Exception as e:
        logger.exception(f"Voice error: {e}")
        await update.message.reply_text(
            "❌ Не смог обработать голосовое.\nПопробуй ещё раз или напиши текстом.",
            reply_markup=get_main_keyboard()
        )
