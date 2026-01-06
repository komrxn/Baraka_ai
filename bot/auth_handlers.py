"""Conversation handlers for phone-based registration and login."""
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import logging
import httpx

from .config import config
from .api_client import BarakaAPIClient
from .user_storage import storage
from .i18n import t
from .handlers.common import get_main_keyboard, send_typing_action

logger = logging.getLogger(__name__)

# States
LANGUAGE, NAME, PHONE = range(3)
LOGIN_PHONE = 0


# Registration flow
@send_typing_action
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


@send_typing_action
async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = context.user_data.get('registration_language', 'uz')
    
    contact = update.message.contact
    
    if not contact:
        await update.message.reply_text(t('auth.registration.use_button', lang))
        return PHONE
    
    # 1. SECURITY CHECK: Ensure contact belongs to the user
    if contact.user_id and contact.user_id != user_id:
        logger.warning(f"Registration security alert: User {user_id} tried to use contact of {contact.user_id}")
        await update.message.reply_text(
            "⚠️ Security Alert: You can only register with your own phone number.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    phone = contact.phone_number
    context.user_data['register_phone'] = phone
    
    telegram_id = update.effective_user.id
    name = context.user_data['register_name']
    
    api = BarakaAPIClient(config.API_BASE_URL)
    
    try:
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
            f"{t('auth.registration.success', db_lang)}",
            reply_markup=get_main_keyboard(db_lang),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Registration error: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 400:
            error_data = e.response.json()
            if "already registered" in str(error_data):
                # User already exists - show login button
                login_text = "🔑 " + ("Kirish" if lang == 'uz' else ("Войти" if lang == 'ru' else "Login"))
                keyboard = [[KeyboardButton(login_text)]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                
                msg = {
                    'uz': "⚠️ Siz allaqachon ro'yxatdan o'tgansiz!\n\nKirish uchun quyidagi tugmani bosing:",
                    'ru': "⚠️ Вы уже зарегистрированы!\n\nДля входа нажмите на кнопку ниже:",
                    'en': "⚠️ You are already registered!\n\nClick the button below to login:"
                }.get(lang, "Already registered")
                
                await update.message.reply_text(msg, reply_markup=reply_markup)
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
@send_typing_action
async def login_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = storage.get_user_language(update.effective_user.id) or 'uz'
    phone_button = KeyboardButton(t('auth.login.button', lang), request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(t('auth.login.prompt', lang), reply_markup=keyboard)
    return LOGIN_PHONE


@send_typing_action
async def login_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    if not contact:
        await update.message.reply_text(t('auth.registration.use_button', lang))
        return LOGIN_PHONE
    
    # 1. SECURITY CHECK: Ensure contact belongs to the user
    if contact.user_id and contact.user_id != user_id:
        logger.warning(f"Login security alert: User {user_id} tried to use contact of {contact.user_id}")
        await update.message.reply_text(
            "⚠️ Security Alert: You can only login with your own phone number.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    phone = contact.phone_number
    telegram_id = update.effective_user.id
    
    api = BarakaAPIClient(config.API_BASE_URL)
    
    try:
        result = await api.login(phone)
        token = result['access_token']
        
        # 2. SECURITY CHECK: Verify account binding
        # Use the token to get user info and check if telegram_id matches
        api.set_token(token)
        user_info = await api.get_me()
        
        bound_telegram_id = user_info.get('telegram_id')
        
        # If account is already bound to another Telegram ID
        if bound_telegram_id and str(bound_telegram_id) != str(telegram_id):
            logger.critical(f"Account Takeover Attempt: Account {phone} is bound to {bound_telegram_id}, but user {telegram_id} tried to access it.")
            
            # Reject access
            msg = {
                'uz': "⛔️ Bu hisob boshqa Telegram akkauntiga bog'langan. Xavfsizlik uchun kirish rad etildi.",
                'ru': "⛔️ Этот аккаунт привязан к другому Telegram ID. В доступе отказано в целях безопасности.",
                'en': "⛔️ This account is linked to another Telegram ID. Access denied for security."
            }.get(lang, "Access denied")
            
            await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        # If we passed checks, save token and proceed
        storage.save_user_token(telegram_id, token)
        
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
             reg_btn_text = {
                 'uz': "📝 Ro'yxatdan o'tish",
                 'ru': "📝 Регистрация",
                 'en': "📝 Register"
             }.get(lang, "📝 Register")
             
             msg = {
                 'uz': "❌ Telefon raqami noto'g'ri yoki ro'yxatdan o'tmagansiz.\nIltimos, qayta ro'yxatdan o'ting:",
                 'ru': "❌ Неверный номер телефона или вы не зарегистрированы.\nПожалуйста, зарегистрируйтесь заново:",
                 'en': "❌ Invalid phone number or not registered.\nPlease register again:"
             }.get(lang, "Invalid phone number")
             
             keyboard = [[KeyboardButton(reg_btn_text)]]
             reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
             
             await update.message.reply_text(
                msg,
                reply_markup=reply_markup
             )
             return ConversationHandler.END
        elif e.response.status_code == 404:
             msg = t('auth.login.error_not_found', lang)
             await update.message.reply_text(
                msg,
                reply_markup=get_main_keyboard(lang)
             )
             return ConversationHandler.END
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
            filters.Text(["🔑 Kirish", "🔑 Войти", "🔑 Login", "🔑 Kirish / Войти / Login"]),
            login_start
        )
    ],
    states={
        LOGIN_PHONE: [MessageHandler(filters.CONTACT, login_phone)]
    },
    fallbacks=[CommandHandler('cancel', login_cancel)],
    allow_reentry=True
)
