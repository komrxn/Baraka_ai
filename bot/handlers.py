"""Telegram bot handlers."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import logging
from datetime import datetime

from .user_storage import storage
from .config import config
from .api_client import MidasAPIClient, UnauthorizedError
from .dialog_context import dialog_context

logger = logging.getLogger(__name__)


async def with_auth_check(update: Update, user_id: int, api_call):
    """Execute API call with automatic 401 error handling.
    
    If the API returns 401 Unauthorized (token expired), automatically:
    1. Clear the invalid token
    2. Prompt user to re-authenticate with /start
    3. Return None to indicate auth failure
    """
    try:
        return await api_call()
    except UnauthorizedError:
        # Token expired or invalid
        storage.clear_user_token(user_id)
        
        await update.message.reply_text(
            "🔑 **Твой токен авторизации истёк.**\n\n"
            "Отправь /start чтобы войти заново.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"User {user_id} token expired, prompted to re-authenticate")
        return None
    except Exception as e:
        # Other errors - let them bubble up
        raise


# Keyboards
def get_main_keyboard():
    """Get main menu keyboard."""
    keyboard = [
        [KeyboardButton("💰 Баланс"), KeyboardButton("📊 Статистика")],
        [KeyboardButton("❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show registration or login options."""
    user = update.effective_user
    
    if storage.is_user_authorized(user.id):
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\nТы уже авторизован.",
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n\n"
            "Я помогу тебе вести учёт финансов.\n\n"
            "Для начала работы:\n"
            "/register - регистрация\n"
            "/login - вход",
            reply_markup=ReplyKeyboardRemove()
        )


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /register command."""
    args = context.args
    
    if len(args) != 3:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Используй: /register username email password\n"
            "Пример: /register ivan ivan@mail.com pass123"
        )
        return
    
    username, email, password = args
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        user_data = await api.register(username, email, password)
        token = user_data.get("access_token")
        
        storage.save_user_token(update.effective_user.id, token, username)
        
        await update.message.reply_text(
            f"✅ Регистрация успешна!\n\n"
            f"Пользователь: {username}\n"
            f"Email: {email}\n\n"
            "Теперь можешь отправлять транзакции!",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        await update.message.reply_text(
            f"❌ Ошибка регистрации: {str(e)}\n\n"
            "Возможно, пользователь уже существует."
        )


async def login_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /login command."""
    args = context.args
    
    if len(args) != 2:
        await update.message.reply_text(
            "❌ Неверный формат!\n\n"
            "Используй: /login username password\n"
            "Пример: /login ivan pass123"
        )
        return
    
    username, password = args
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        user_data = await api.login(username, password)
        token = user_data.get("access_token")
        
        storage.save_user_token(update.effective_user.id, token, username)
        
        await update.message.reply_text(
            f"✅ Вход выполнен!\n\n"
            f"Пользователь: {username}\n\n"
            "Отправь текст, голос или фото чека для добавления транзакции.",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        await update.message.reply_text(
            f"❌ Ошибка входа: {str(e)}\n\n"
            "Проверь username и пароль."
        )


async def get_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user balance."""
    user_id = update.effective_user.id
    
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    async def _get_balance():
        return await api.get_balance(period="month")
    
    balance_data = await with_auth_check(update, user_id, _get_balance)
    if balance_data is None:
        return  # Auth failed, user prompted to /start
    
    try:
        await update.message.reply_text(
            f"💰 **Баланс за месяц:**\n\n"
            f"💵 Доходы: {float(balance_data['total_income']):,.0f} {balance_data['currency'].upper()}\n"
            f"💸 Расходы: {float(balance_data['total_expense']):,.0f} {balance_data['currency'].upper()}\n"
            f"📊 Баланс: **{float(balance_data['balance']):,.0f} {balance_data['currency'].upper()}**",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Balance display error: {e}")
        await update.message.reply_text("❌ Ошибка отображения баланса")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    if not storage.is_user_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # Handle menu buttons first
    if text == "💰 Баланс":
        await get_balance(update, context)
        return
    elif text == "📊 Статистика":
        # Show statistics (keep existing functionality)
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        
        try:
            balance = await api.get_balance(period="month")
            breakdown = await api.get_category_breakdown(period="month")
            
            lines = ["📊 **Статистика за месяц**\n"]
            
            income = float(balance.get('total_income', 0))
            expense = float(balance.get('total_expense', 0))
            bal = float(balance.get('balance', 0))
            currency = balance.get('currency', 'uzs').upper()
            
            lines.append(f"💰 **Доходы**: {income:,.0f} {currency}")
            lines.append(f"💸 **Расходы**: {expense:,.0f} {currency}")
            lines.append(f"📈 **Баланс**: {bal:,.0f} {currency}\n")
            
            if breakdown and breakdown.get('categories'):
                lines.append("**Топ категорий расходов:**\n")
                
                sorted_cats = sorted(
                    breakdown['categories'], 
                    key=lambda x: float(x.get('amount', 0)), 
                    reverse=True
                )[:5]
                
                for i, cat in enumerate(sorted_cats, 1):
                    name = cat['category_name']
                    amount = float(cat['amount'])
                    percent = float(cat['percentage'])
                    
                    emoji = {
                        "Питание": "🍔",
                        "Транспорт": "🚗",
                        "Развлечения": "🎮",
                        "Покупки": "🛍",
                        "Услуги": "💼",
                        "Здоровье": "🏥",
                        "Образование": "📚",
                        "Жильё": "🏠",
                        "Счета": "📱",
                        "Зарплата": "💰",
                    }.get(name, "📌")
                    
                    lines.append(f"{i}. {emoji} **{name}**: {amount:,.0f} ({percent:.1f}%)")
                
                total = float(breakdown.get('total', 0))
                lines.append(f"\n💵 **Всего**: {total:,.0f} {currency}")
            else:
                lines.append("\nПока нет расходов.\nДобавь транзакции!")
            
            await update.message.reply_text(
                "\n".join(lines),
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        except Exception as e:
            logger.exception(f"Statistics error: {e}")
            await update.message.reply_text(
                "❌ Ошибка получения статистики",
                reply_markup=get_main_keyboard()
            )
        return
    elif text == "❓ Помощь":
        await update.message.reply_text(
            "📖 **Инструкция по использованию бота**\n\n"
            "**Как добавить транзакцию:**\n"
            "Просто напиши обычным языком:\n"
            "• Потратил на кофе 25000\n"
            "• Купил продукты за 150к\n"
            "• Получил зарплату 5 млн\n\n"
            "**Можно сразу несколько:**\n"
            "• Потратил на ужин 70к и получил зарплату 300к\n\n"
            "**Голосовые сообщения:**\n"
            "🎤 Отправь голосовое - я распознаю и сохраню\n\n"
            "**Фото чеков:**\n"
            "📸 Отправь фото чека - я извлеку сумму и описание\n\n"
            "**Кнопки:**\n"
            "💰 **Баланс** - текущий баланс за месяц\n"
            "📊 **Статистика** - расходы по категориям\n\n"
            "**Категории распознаются автоматически:**\n"
            "🍔 Еда и кафе, 🚗 Транспорт, 🎮 Развлечения,\n"
            "🛍 Покупки, 📱 Счета, 💼 Услуги и другие\n\n"
            "Просто общайся со мной как с человеком! 🤖",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    # Use AI agent for all other messages
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Send typing action
    await update.message.chat.send_action(action="typing")
    
    async def _process_with_ai():
        from .ai_agent import AIAgent
        agent = AIAgent(api)
        return await agent.process_message(user_id, text)
    
    response = await with_auth_check(update, user_id, _process_with_ai)
    if response is None:
        return  # Auth failed, user prompted to /start
    
    # Try to send with Markdown, fallback to plain text if fails
    try:
        await update.message.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as markdown_error:
        # Markdown parsing failed, send plain text
        logger.warning(f"Markdown parsing failed, sending plain text: {markdown_error}")
        await update.message.reply_text(
            response,
            reply_markup=get_main_keyboard()
        )
    

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
        import httpx
        import io
        
        audio_file = io.BytesIO(bytes(voice_bytes))
        audio_file.name = "voice.ogg"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            stt_response = await client.post(
                config.UZAI_STT_URL,
                headers={
                    "Authorization": config.UZAI_API_KEY
                },
                files={
                    "file": ("voice.ogg", audio_file, "audio/ogg")
                },
                data={
                    "language": "ru-uz",
                    "blocking": "true",
                    "return_offsets": "false",
                    "run_diarization": "false"
                }
            )
            stt_response.raise_for_status()
            stt_result = stt_response.json()
        
        # Debug logging
        logger.info(f"UzbekVoice.AI full response: {stt_result}")
        
        # Parse response - text is in result.text
        result = stt_result.get("result", {})
        transcribed_text = result.get("text", "").strip()
        
        if not transcribed_text:
            logger.error(f"Empty transcription. Response: {stt_result}")
            raise ValueError(f"No text in response: {stt_result}")
        
        logger.info(f"Transcribed (UzbekVoice.AI): {transcribed_text}")
        
        # Use AI agent to process transcribed text
        async def _process_transcribed():
            from .ai_agent import AIAgent
            agent = AIAgent(api)
            return await agent.process_message(user_id, transcribed_text)
        
        response = await with_auth_check(update, user_id, _process_transcribed)
        if response is None:
            return  # Auth failed, user prompted to /start
        
        # Try Markdown, fallback to plain text
        try:
            await update.message.reply_text(
                f"🎤 *Ты сказал:* {transcribed_text}\n\n{response}",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        except Exception:
            await update.message.reply_text(
                f"🎤 Ты сказал: {transcribed_text}\n\n{response}",
                reply_markup=get_main_keyboard()
            )
        
    except Exception as e:
        logger.exception(f"Voice processing error: {e}")
        await update.message.reply_text(
            "❌ Не смог обработать голосовое.\nПопробуй ещё раз или напиши текстом.",
            reply_markup=get_main_keyboard()
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages (receipts)."""
    if not storage.is_user_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    user_id = update.effective_user.id
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        await update.message.reply_text("📸 Анализирую фото...")
        await update.message.chat.send_action(action="typing")
        
        # Download photo
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Extract text using Vision API
        from openai import AsyncOpenAI
        vision_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
        import base64
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
        
        # Use AI agent to process extracted text
        from .ai_agent import AIAgent
        
        agent = AIAgent(api)
        response = await agent.process_message(user_id, f"Вот чек: {extracted_text}")
        
        await update.message.reply_text(
            f"📸 *С чека:* {extracted_text}\n\n{response}",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        logger.exception(f"Photo processing error: {e}")
        await update.message.reply_text(
            "❌ Не смог обработать фото.\nПопробуй сфотографировать получше или введи данные текстом.",
            reply_markup=get_main_keyboard()
        )


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transaction confirmation."""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "✅ Да, верно":
        # Create transaction
        pending = storage.get_pending_transaction(user_id)
        
        if not pending:
            await update.message.reply_text(
                "❌ Нет транзакции для подтверждения",
                reply_markup=get_main_keyboard()
            )
            return
        
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        
        try:
            # Prepare transaction data
            tx_data = {
                "type": pending.get("type"),
                "amount": float(pending.get("amount", 0)),
                "description": pending.get("description", ""),
                "currency": pending.get("currency", "uzs"),
                "transaction_date": datetime.now().isoformat()
            }
            
            # Add category_id if AI suggested one
            if pending.get("suggested_category_id"):
                tx_data["category_id"] = pending["suggested_category_id"]
            elif pending.get("category_id"):
                tx_data["category_id"] = pending["category_id"]
            
            # Create transaction
            result = await api.create_transaction(tx_data)
            
            # Save to context (so next messages can reference it)
            dialog_context.add_message(
                user_id,
                "assistant",
                f"Сохранена транзакция",
                metadata={"type": "saved_transaction", "transaction": pending}
            )
            
            # Clear pending
            storage.clear_pending_transaction(user_id)
            
            await update.message.reply_text(
                "✅ Транзакция сохранена!",
                reply_markup=get_main_keyboard()
            )
            
        except Exception as e:
            logger.error(f"Create transaction error: {e}")
            await update.message.reply_text(
                f"❌ Ошибка сохранения: {str(e)}",
                reply_markup=get_main_keyboard()
            )
            
    elif text == "❌ Нет, повторить":
        # Clear pending and ask to retry
        storage.clear_pending_transaction(user_id)
        
        await update.message.reply_text(
            "Попробуй ещё раз:\n"
            "• Отправь текст (например: купил кофе 25000)\n"
            "• Запиши голосовое\n"
            "• Сфотографируй чек",
            reply_markup=get_main_keyboard()
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message with language selection."""
    from .help_messages import get_help_message
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    # Language selection buttons
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
        ],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="help_uz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📖 **Выбери язык / Choose language / Tilni tanlang:**",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection for help."""
    from .help_messages import get_help_message
    
    query = update.callback_query
    await query.answer()
    
    # Extract language from callback_data (help_ru, help_en, help_uz)
    language = query.data.split('_')[1]
    
    help_text = get_help_message(language)
    
    await query.edit_message_text(
        text=help_text,
        parse_mode='Markdown'
    )
```
