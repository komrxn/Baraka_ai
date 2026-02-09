"""Currency rates handler for Telegram bot."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
import logging
import math

from ..user_storage import storage
from ..i18n import t
from ..api_client import BarakaAPIClient
from ..config import config
from .common import send_typing_action

logger = logging.getLogger(__name__)

# Pagination settings
CURRENCIES_PER_PAGE = 10  # 2 columns × 5 rows
COLUMNS = 2


@send_typing_action
async def currency_rates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Курс валют' button press - show default rates."""
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Check subscription
    token = storage.get_user_token(user_id)
    if not token:
        await update.message.reply_text(t('auth.common.auth_required', lang))
        return
    
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        sub_status = await api.get_subscription_status(user_id)
        sub_type = sub_status.get("subscription_type", "free")
        
        # Only for subscribers
        if sub_type == "free":
            keyboard = [[InlineKeyboardButton(t("subscription.buy_subscription_btn", lang), callback_data="buy_subscription")]]
            await update.message.reply_text(
                t("currency.premium_only", lang),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
            
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        await update.message.reply_text(t("common.common.error", lang))
        return
    
    # Fetch and display rates
    try:
        rates_data = await api.get_currency_rates()
        
        if not rates_data or "rates" not in rates_data:
            await update.message.reply_text(t("currency.error", lang))
            return
        
        rates = rates_data["rates"]
        date = rates_data.get("date", "")
        
        # Get top 5 default currencies
        default_codes = ["USD", "EUR", "RUB", "CNY", "KZT"]
        default_rates = [r for r in rates if r["code"] in default_codes]
        
        # Sort by default order
        default_rates.sort(key=lambda x: default_codes.index(x["code"]) if x["code"] in default_codes else 999)
        
        # Format message
        message = format_rates_message(default_rates, date, lang)
        
        # Button to select other currencies
        keyboard = [[InlineKeyboardButton(t("currency.select_currency", lang), callback_data="currency_list_0")]]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error fetching currency rates: {e}")
        await update.message.reply_text(t("currency.error", lang))


async def currency_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle paginated currency list."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Extract page number from callback data: currency_list_0
    try:
        page = int(query.data.split("_")[-1])
    except:
        page = 0
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        rates_data = await api.get_currency_rates()
        
        if not rates_data or "rates" not in rates_data:
            await query.edit_message_text(t("currency.error", lang))
            return
        
        rates = rates_data["rates"]
        total_pages = math.ceil(len(rates) / CURRENCIES_PER_PAGE)
        
        # Get current page items
        start_idx = page * CURRENCIES_PER_PAGE
        end_idx = start_idx + CURRENCIES_PER_PAGE
        page_rates = rates[start_idx:end_idx]
        
        # Build keyboard grid (2 columns)
        keyboard = []
        row = []
        for rate in page_rates:
            flag = rate.get("flag", "💱")
            code = rate["code"]
            btn = InlineKeyboardButton(f"{flag} {code}", callback_data=f"currency_show_{code}")
            row.append(btn)
            
            if len(row) == COLUMNS:
                keyboard.append(row)
                row = []
        
        if row:  # Add remaining buttons
            keyboard.append(row)
        
        # Navigation row
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"currency_list_{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"currency_list_{page + 1}"))
        keyboard.append(nav_row)
        
        # Back button
        keyboard.append([InlineKeyboardButton(t("subscription.back_btn", lang), callback_data="currency_back")])
        
        await query.edit_message_text(
            t("currency.select_title", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in currency list: {e}")
        await query.edit_message_text(t("currency.error", lang))


async def currency_show_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show single currency rate."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Extract currency code: currency_show_USD
    currency_code = query.data.replace("currency_show_", "")
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        rates_data = await api.get_currency_rates()
        
        if not rates_data or "rates" not in rates_data:
            await query.edit_message_text(t("currency.error", lang))
            return
        
        rates = rates_data["rates"]
        date = rates_data.get("date", "")
        
        # Find the specific rate
        rate = next((r for r in rates if r["code"] == currency_code), None)
        
        if not rate:
            await query.edit_message_text(t("currency.error", lang))
            return
        
        # Format single currency message
        message = format_single_rate(rate, date, lang)
        
        keyboard = [[InlineKeyboardButton(t("subscription.back_btn", lang), callback_data="currency_list_0")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing currency: {e}")
        await query.edit_message_text(t("currency.error", lang))


async def currency_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to default rates view."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        rates_data = await api.get_currency_rates()
        
        if not rates_data or "rates" not in rates_data:
            await query.edit_message_text(t("currency.error", lang))
            return
        
        rates = rates_data["rates"]
        date = rates_data.get("date", "")
        
        # Get top 5 default currencies
        default_codes = ["USD", "EUR", "RUB", "CNY", "KZT"]
        default_rates = [r for r in rates if r["code"] in default_codes]
        default_rates.sort(key=lambda x: default_codes.index(x["code"]) if x["code"] in default_codes else 999)
        
        message = format_rates_message(default_rates, date, lang)
        
        keyboard = [[InlineKeyboardButton(t("currency.select_currency", lang), callback_data="currency_list_0")]]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in currency back: {e}")
        await query.edit_message_text(t("currency.error", lang))


def format_rates_message(rates: list, date: str, lang: str = "ru") -> str:
    """Format multiple currency rates for display."""
    titles = {
        "ru": "🏦 *Курс валют ЦБ РУз*",
        "uz": "🏦 *O'zbekiston MB valyuta kurslari*",
        "en": "🏦 *CBU Exchange Rates*"
    }
    
    title = titles.get(lang, titles["ru"])
    lines = [f"{title} — {date}\n"]
    
    for rate in rates:
        flag = rate.get("flag", "💱")
        code = rate["code"]
        nominal = rate.get("nominal", 1)
        rate_val = rate["rate"]
        diff = rate.get("diff", 0)
        
        # Format rate with spaces
        if rate_val >= 1000:
            rate_str = f"{rate_val:,.2f}".replace(",", " ")
        else:
            rate_str = f"{rate_val:.2f}"
        
        # Format diff
        if diff > 0:
            diff_str = f"▲{diff}"
        elif diff < 0:
            diff_str = f"▼{abs(diff)}"
        else:
            diff_str = "—"
        
        nominal_str = f"{nominal} " if nominal > 1 else "1 "
        lines.append(f"{flag} {nominal_str}{code} = {rate_str} сум ({diff_str})")
    
    return "\n".join(lines)


def format_single_rate(rate: dict, date: str, lang: str = "ru") -> str:
    """Format single currency rate for display."""
    flag = rate.get("flag", "💱")
    code = rate["code"]
    nominal = rate.get("nominal", 1)
    rate_val = rate["rate"]
    diff = rate.get("diff", 0)
    name = rate.get(f"name_{lang}", rate.get("name_ru", code))
    
    # Format rate
    if rate_val >= 1000:
        rate_str = f"{rate_val:,.2f}".replace(",", " ")
    else:
        rate_str = f"{rate_val:.2f}"
    
    # Format diff
    if diff > 0:
        diff_str = f"▲{diff}"
    elif diff < 0:
        diff_str = f"▼{abs(diff)}"
    else:
        diff_str = "—"
    
    nominal_str = f"{nominal} " if nominal > 1 else "1 "
    
    return (
        f"{flag} *{name}* ({code})\n\n"
        f"📅 {date}\n"
        f"💰 {nominal_str}{code} = *{rate_str}* сум\n"
        f"📊 Изменение: {diff_str}"
    )


# Handlers list for registration
currency_handlers = [
    CallbackQueryHandler(currency_list_callback, pattern="^currency_list_"),
    CallbackQueryHandler(currency_show_callback, pattern="^currency_show_"),
    CallbackQueryHandler(currency_back_callback, pattern="^currency_back$"),
]
