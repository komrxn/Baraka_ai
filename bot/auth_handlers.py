"""Conversation handlers for phone-based registration and login."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import logging
import httpx

from .config import config
from .api_client import MidasAPIClient
from .user_storage import storage
from .handlers import get_main_keyboard

logger = logging.getLogger(__name__)

# States
NAME, PHONE = range(2)
LOGIN_PHONE = 0


# Registration flow
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Давай познакомимся! 👋\n\nКак тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['register_name'] = name
    
    phone_button = KeyboardButton("📱 Поделиться номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        f"Приятно познакомиться, {name}! 😊\n\nПоделись номером телефона:",
        reply_markup=keyboard
    )
    return PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text("❌ Используй кнопку 'Поделиться номером'")
        return PHONE # Keep returning PHONE if contact is not provided via button
    
    phone = contact.phone_number # Get phone from contact if provided
    context.user_data['register_phone'] = phone # Store it for later use if needed, or if the instruction implies it's always taken from user_data
    
    # Get phone from user data (this line is added as per instruction, assuming it might be set elsewhere or as a fallback)
    phone = context.user_data.get('register_phone')
    telegram_id = update.effective_user.id
    name = context.user_data['register_name']
    
    # Get language preference (default uz)
    lang = context.user_data.get('registration_language', 'uz')
    
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        # Register with language
        result = await api.register(telegram_id, phone, name, language=lang)
        token = result['access_token']
        storage.save_user_token(telegram_id, token)
        
        # Save language preference
        storage.set_user_language(telegram_id, lang)
        
        await update.message.reply_text(
            "✅ Регистрация завершена!\n\nТеперь можешь добавлять транзакции.",
            reply_markup=get_main_keyboard()
        )
        
        # Send help message after registration
        from .help_messages import get_help_message
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
            ],
            [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="help_uz")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📖 **Как пользоваться / How to use / Qanday foydalanish:**\n\n"
            "Выбери язык → Choose language → Tilni tanlang:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            await update.message.reply_text(
                "❌ Этот номер уже зарегистрирован.\nИспользуй /login для входа.",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка регистрации. Попробуй позже.",
                reply_markup=get_main_keyboard()
            )
        return ConversationHandler.END


# Login flow
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_button = KeyboardButton("📱 Войти через номер", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text("Войди через номер телефона:", reply_markup=keyboard)
    return LOGIN_PHONE


async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text("❌ Используй кнопку")
        return LOGIN_PHONE
    
    phone = contact.phone_number
    telegram_id = update.effective_user.id
    
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        result = await api.login(phone, telegram_id)
        token = result['access_token']
        storage.save_user_token(telegram_id, token)
        
        await update.message.reply_text("✅ Добро пожаловать!", reply_markup=get_main_keyboard())
        return ConversationHandler.END
        
    except httpx.HTTPStatusError:
        await update.message.reply_text(
            "❌ Номер не найден. Зарегистрируйся: /register",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END


# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=get_main_keyboard())
    return ConversationHandler.END


# Setup handlers
register_conv = ConversationHandler(
    entry_points=[CommandHandler('register', register_start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        PHONE: [MessageHandler(filters.CONTACT, register_phone)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

login_conv = ConversationHandler(
    entry_points=[CommandHandler('login', login_start)],
    states={
        LOGIN_PHONE: [MessageHandler(filters.CONTACT, login_phone)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
