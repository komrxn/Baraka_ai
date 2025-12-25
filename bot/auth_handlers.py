"""Conversation handlers for phone-based registration and login."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import logging
import httpx

from .config import config
from .api_client import MidasAPIClient
from .user_storage import storage
from .i18n import t
from .handlers.common import get_main_keyboard

logger = logging.getLogger(__name__)

# States
LANGUAGE, NAME, PHONE = range(3)
LOGIN_PHONE = 0


# Registration flow
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start registration - ask user to choose language."""
    # Show language selection
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="reglang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="reglang_en"),
        ],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="reglang_uz")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Show in all 3 languages
    message = (
        "👋 Assalomu alaykum!\nBu bot Sizning shaxsiy moliyaviy yordamchingiz.\n\n"
        "👋 Здравствуйте!\nЭтот бот — ваш личный финансовый помощник.\n\n"
        "👋 Hello!\nThis bot is your personal finance assistant.\n\n"
        "🌐 Tilni tanlang / Выберите язык / Choose language:"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )
    return LANGUAGE


async def register_language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection during registration."""
    query = update.callback_query
    await query.answer()
    
    # Extract language from callback_data: "reglang_ru" -> "ru"
    lang = query.data.split('_')[1]
    
    # Save to context for this registration flow
    context.user_data['registration_language'] = lang
    
    await query.edit_message_text(
        t('auth.registration.ask_name', lang)
    )
    return NAME


async def register_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get('registration_language', 'uz')
    name = update.message.text.strip()
    context.user_data['register_name'] = name
    
    phone_button = KeyboardButton(t('auth.registration.share_phone', lang), request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        t('auth.registration.ask_phone', lang, name=name),
        reply_markup=keyboard
    )
    return PHONE


async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get('registration_language', 'uz')
    
    logger.info(f"=== REGISTRATION DEBUG ===")
    logger.info(f"User ID: {user_id}")
    logger.info(f"context.user_data.get('registration_language'): {context.user_data.get('registration_language')}")
    logger.info(f"Final lang: {lang}")
    logger.info(f"========================")
    
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text(t('auth.registration.use_button', lang))
        return PHONE
    
    phone = contact.phone_number
    context.user_data['register_phone'] = phone
    
    telegram_id = update.effective_user.id
    name = context.user_data['register_name']
    
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        logger.info(f"Calling API register with language={lang}")
        result = await api.register(telegram_id, phone, name, language=lang)
        token = result['access_token']
        storage.save_user_token(telegram_id, token)
        
        # Fetch user info to get language from database  
        api.set_token(token)
        user_info = await api.get_me()
        db_lang = user_info.get('language', lang)
        
        # Sync language from database to local storage
        storage.set_user_language(telegram_id, db_lang)
        
        await update.message.reply_text(
            t('auth.registration.success', db_lang),
            reply_markup=get_main_keyboard(db_lang)
        )
        
        # Send help message after registration
        keyboard = [
            [
                InlineKeyboardButton("🇷🇺 Русский", callback_data="help_ru"),
                InlineKeyboardButton("🇬🇧 English", callback_data="help_en"),
            ],
            [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="help_uz")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            t('auth.common.choose_language', db_lang),
            reply_markup=reply_markup
        )
        
        return ConversationHandler.END
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Registration error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 400:
            error_data = e.response.json()
            if "already registered" in str(error_data):
                msg = {
                    'uz': "⚠️ Siz allaqachon ro'yxatdan o'tgansiz!\nIltimos, tizimga kiring: /login",
                    'ru': "⚠️ Вы уже зарегистрированы!\nПожалуйста, войдите в систему: /login",
                    'en': "⚠️ You are already registered!\nPlease login: /login"
                }.get(lang, "Already registered")
                
                await update.message.reply_text(msg, reply_markup=get_main_keyboard(lang))
            else:
                await update.message.reply_text(
                    t('auth.registration.error_exists', lang),
                    reply_markup=get_main_keyboard(lang)
                )
        else:
            await update.message.reply_text(
                t('auth.registration.error_generic', lang),
                reply_markup=get_main_keyboard(lang)
            )
        return ConversationHandler.END
    except Exception as e:
        logger.exception(f"Unexpected error during registration: {e}")
        await update.message.reply_text(
            t('auth.registration.error_generic', lang),
            reply_markup=get_main_keyboard(lang)
        )
        return ConversationHandler.END


# Login flow
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = storage.get_user_language(update.effective_user.id) or 'uz'
    phone_button = KeyboardButton(t('auth.login.button', lang), request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(t('auth.login.prompt', lang), reply_markup=keyboard)
    return LOGIN_PHONE


async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    lang = storage.get_user_language(update.effective_user.id) or 'uz'
    
    if not contact:
        await update.message.reply_text(t('auth.registration.use_button', lang))
        return LOGIN_PHONE
    
    phone = contact.phone_number
    telegram_id = update.effective_user.id
    
    api = MidasAPIClient(config.API_BASE_URL)
    
    try:
        result = await api.login(phone)
        token = result['access_token']
        storage.save_user_token(telegram_id, token)
        
        # Fetch user info to get language from database
        api.set_token(token)
        user_info = await api.get_me()
        db_lang = user_info.get('language', lang)
        
        # Sync language from database to local storage
        storage.set_user_language(telegram_id, db_lang)
        
        await update.message.reply_text(
            t('auth.login.success', db_lang),
            reply_markup=get_main_keyboard(db_lang)
        )
        return ConversationHandler.END
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Login error: {e.response.status_code} - {e.response.text}")
        
        if e.response.status_code == 401:
             # Phone number mismatch or invalid
             msg = {
                 'uz': "❌ Telefon raqami noto'g'ri yoki ro'yxatdan o'tmagansiz.\nIltimos, qayta ro'yxatdan o'ting: /register",
                 'ru': "❌ Неверный номер телефона или вы не зарегистрированы.\nПожалуйста, зарегистрируйтесь заново: /register",
                 'en': "❌ Invalid phone number or not registered.\nPlease register: /register"
             }.get(lang, "Invalid phone number")
        elif e.response.status_code == 404:
             msg = t('auth.login.error_not_found', lang)
        else:
             msg = t('auth.login.error_generic', lang)
             
        await update.message.reply_text(
            msg,
            reply_markup=get_main_keyboard(lang)
        )
        return ConversationHandler.END


# Cancel handler
async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration."""
    await update.message.reply_text(
        "Registration cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def login_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel login."""
    await update.message.reply_text(
        "Login cancelled.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Registration Conversation Handler
register_conv = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Text(["📝 Ro'yxatdan o'tish", "📝 Регистрация", "📝 Register"]),
            register_start
        )
    ],
    states={
        LANGUAGE: [CallbackQueryHandler(register_language_selected, pattern="^reglang_")],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_name)],
        PHONE: [MessageHandler(filters.CONTACT, register_phone)]
    },
    fallbacks=[CommandHandler('cancel', register_cancel)],
    allow_reentry=True
)


# Login Conversation Handler
login_conv = ConversationHandler(
    entry_points=[
        MessageHandler(
            filters.Text(["🔑 Kirish", "🔑 Войти", "🔑 Login"]),
            login_start
        )
    ],
    states={
        LOGIN_PHONE: [MessageHandler(filters.CONTACT, login_phone)]
    },
    fallbacks=[CommandHandler('cancel', login_cancel)],
    allow_reentry=True
)
