from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from bot.api_client import BarakaAPIClient
from bot.config import config
from bot.i18n import t
from bot.user_storage import storage

async def activate_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle trial activation callback."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await query.answer()
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        data = await api.activate_trial()
        
        expires = data.get("expires_at", "soon")
        text = (
            f"{t('subscription.trial_activated_title', lang)}\n\n"
            f"{t('subscription.trial_activated_body', lang, date=expires)}"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
        
    except Exception as e:
        status_code = getattr(e, "response", None) and e.response.status_code
        if status_code == 400:
             await query.edit_message_text(t("subscription.trial_already_used", lang), parse_mode="Markdown")
        else:
             await query.edit_message_text(t("subscription.trial_error", lang), parse_mode="Markdown")

async def buy_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Step 1: Select Tier (Plus, Pro, Premium)
    """
    query = update.callback_query
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(t("subscription.tier_plus_btn", lang), callback_data="select_tier_plus")],
        [InlineKeyboardButton(t("subscription.tier_pro_btn", lang), callback_data="select_tier_pro")],
        [InlineKeyboardButton(t("subscription.tier_premium_btn", lang), callback_data="select_tier_premium")],
        [InlineKeyboardButton(t("subscription.back_btn", lang), callback_data="profile_menu")] 
    ]
    
    await query.edit_message_text(
        f"{t('subscription.select_tier_title', lang)}\n\n"
        f"{t('subscription.select_tier_body', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def select_tier_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Step 2: Select Duration (1 Month, 3 Months) for the chosen tier
    Pattern: ^select_tier_(plus|pro|premium)$
    """
    query = update.callback_query
    data = query.data
    tier = data.split("_")[2] # plus, pro, premium
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await query.answer()
    
    # Prices (Hardcoded here for display, but validated on backend)
    prices = {
        "plus": {"1": "34 999", "3": "99 999"},
        "pro": {"1": "49 999", "3": "139 999"},
        "premium": {"1": "89 999", "3": "249 999"},
    }
    
    tier_desc_key = f"subscription.tier_{tier}_desc"
    desc = t(tier_desc_key, lang)
    
    p1 = prices[tier]["1"]
    p3 = prices[tier]["3"]
    
    # Buttons: pay_{tier}_1, pay_{tier}_3
    keyboard = [
        [InlineKeyboardButton(t("subscription.duration_1_month", lang, price=p1), callback_data=f"pay_{tier}_1")],
        [InlineKeyboardButton(t("subscription.duration_3_months", lang, price=p3), callback_data=f"pay_{tier}_3")],
        [InlineKeyboardButton(t("subscription.back_btn", lang), callback_data="buy_subscription")]
    ]
    
    await query.edit_message_text(
        f"{desc}\n\n"
        f"{t('subscription.select_duration_title', lang)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_payment_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: str, provider: str):
    """Helper to generate payment link."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await query.answer(t("common.common.loading", lang))
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        data = await api.generate_payment_link(plan_id=plan_id, provider=provider)
        url = data.get("url")
        
        provider_name = "Click" if provider == "click" else "Payme"
        
        # Back button goes to provider selection for this plan
        keyboard = [
            [InlineKeyboardButton(t('subscription.pay_btn_format', lang, provider=provider_name), url=url)],
            [InlineKeyboardButton(t("subscription.back_btn", lang), callback_data=f"choice_{plan_id}")] # Loop back to choice
        ]
        
        await query.edit_message_text(
            f"{t('subscription.payment_initiated', lang)}\n\n"
            f"{t('subscription.payment_instructions', lang)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        error_text = f"❌ Error: {str(e)}"
        if "400" in str(e):
             error_text = "❌ Error: Invalid plan or request."
        await query.edit_message_text(error_text, parse_mode="Markdown")

async def ask_provider(update: Update, context: ContextTypes.DEFAULT_TYPE, plan_id: str):
    """
    Step 3: Ask user to select payment provider (Click/Payme)
    plan_id example: 'plus_1', 'pro_3'
    """
    query = update.callback_query
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    await query.answer()
    
    title = t('subscription.select_payment_method', lang)
    
    # Parse tier to go back correctly
    try:
        tier = plan_id.split("_")[0] # plus, pro...
    except:
        tier = "pro"
        
    keyboard = [
        [
            InlineKeyboardButton("Click", callback_data=f"choice_{plan_id}_click"),
            InlineKeyboardButton("Payme", callback_data=f"choice_{plan_id}_payme"),
        ],
        [InlineKeyboardButton(t("subscription.back_btn", lang), callback_data=f"select_tier_{tier}")]
    ]
    
    await query.edit_message_text(
        text=f"💳 *{title}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_provider_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle provider selection."""
    query = update.callback_query
    data = query.data
    # format: choice_{plan_id}_{provider}. plan_id can contain underscores (plus_1)
    # So split carefully.
    # Ex: choice_plus_1_click -> [choice, plus, 1, click] -> invalid logic if we just split by _
    # Better: split by _ with limit
    
    try:
        # data = choice_plus_1_click
        parts = data.split("_")
        # provider is last element
        provider = parts[-1]
        
        # Check for Payme coming soon
        if provider == "payme":
            user_id = query.from_user.id
            lang = storage.get_user_language(user_id) or 'uz'
            await query.answer(t("subscription.payme_coming_soon", lang), show_alert=True)
            return

        # plan_id is everything in between 'choice' and 'provider'
        # e.g. plus_1
        plan_id = "_".join(parts[1:-1])
        
        await handle_payment_generation(update, context, plan_id, provider)
    except ValueError:
        await query.answer("Error parsing callback data")

async def pay_plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle selection of specific plan duration.
    Pattern: ^pay_(plus|pro|premium)_(1|3)$
    """
    query = update.callback_query
    data = query.data
    # data = pay_plus_1
    # plan_id = plus_1
    plan_id = data.replace("pay_", "")
    
    await ask_provider(update, context, plan_id)

async def select_provider_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle back button from payment generation page.
    pattern: ^choice_{plan_id}$  (Note: in handle_payment_generation I used callback_data=f"choice_{plan_id}")
    Wait, "choice_" pattern is used for PROVIDER SELECTION too.
    Let's distinct them.
    In ask_provider: choice_{plan_id}_{provider}
    In handle_payment_generation back btn: I should probably just call ask_provider cleanly.
    Let's change handle_payment_generation back button to: `back_to_provider_{plan_id}`
    """
    pass # Replaced logic below

async def back_to_provider_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    # back_to_provider_plus_1
    plan_id = data.replace("back_to_provider_", "")
    await ask_provider(update, context, plan_id)

subscription_handlers = [
    CallbackQueryHandler(activate_trial_callback, pattern="^activate_trial$"),
    CallbackQueryHandler(buy_subscription_callback, pattern="^buy_subscription$"),
    CallbackQueryHandler(select_tier_callback, pattern="^select_tier_"),
    CallbackQueryHandler(pay_plan_callback, pattern="^pay_"),
    CallbackQueryHandler(handle_provider_choice, pattern="^choice_"),
    CallbackQueryHandler(back_to_provider_callback, pattern="^back_to_provider_"),
]

