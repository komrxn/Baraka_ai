"""Conversation handlers for phone-based registration and login."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters
import logging
import httpx

from .config import config
from .api_client import MidasAPIClient
from .user_storage import storage
from .lang_messages import get_message
from .handlers.common import get_main_keyboard

logger = logging.getLogger(__name__)

# States
NAME, PHONE = range(2)
LOGIN_PHONE = 0


# Registration flow
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await update.message.reply_text(
        get_message(lang, 'intro_ask_name'),
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    name = update.message.text.strip()
    context.user_data['register_name'] = name
    
    phone_button = KeyboardButton(get_message(lang, 'share_phone'), request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        get_message(lang, 'intro_ask_phone', name=name),
        reply_markup=keyboard
    )
    return PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text(get_message(lang, 'use_button'))
        return PHONE # Keep returning PHONE if contact is not provided via button
    
    phone = contact.phone_number
    context.user_data['register_phone'] = phone
    
    # Get phone from user data
    telegram_id = update.effective_user.id
    name = context.user_data['register_name']
    
    # Lang is correctly retrieved above
    
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        # Register with language
        result = await api.register(telegram_id, phone, name, language=lang)
        token = result['access_token']
        storage.save_user_token(telegram_id, token)
        
        # Save language preference
        storage.set_user_language(telegram_id, lang)
        
        await update.message.reply_text(
            get_message(lang, 'reg_success'),
            reply_markup=get_main_keyboard(lang)
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
            get_message(lang, 'choose_language'),
            reply_markup=reply_markup
        )
        
        return ConversationHandler.END
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            # TODO: Localize API error messages
            error_text = "❌ Bu raqam ro'yxatdan o'tgan / This number is already registered"
            if lang =='ru':
                error_text = "❌ Этот номер уже зарегистрирован.\nИспользуй /login для входа."
            elif lang == 'en':
                error_text = "❌ Expected error: Number already registered."
            
            await update.message.reply_text(
                error_text,
                reply_markup=get_main_keyboard(lang)
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
        result = await api.login(phone)  # Fixed - removed telegram_id
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
