"""Message handler module."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..ai_agent import AIAgent
from ..api_client import MidasAPIClient
from ..config import config
from ..user_storage import storage
from ..transaction_actions import show_transaction_with_actions, handle_edit_transaction_message
from .common import with_auth_check, get_main_keyboard
from ..lang_messages import get_message

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with AI."""
    user_id = update.effective_user.id
    
    # Auth check
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    text = update.message.text
    
    # Check if user is editing a transaction
    if context.user_data.get('editing_tx'):
        from ..confirmation_handlers import handle_edit_message
        await handle_edit_message(update, context)
        return
    
    # Handle menu buttons first
    if text == "💰 Баланс":
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        # Get user language
        lang = storage.get_user_language(user_id) or 'uz'
        await show_balance(update, api, lang)
        return
    elif text == "📊 Статистика":
        # Show statistics (keep existing functionality)
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        lang = storage.get_user_language(user_id) or 'uz'
        await show_statistics(update, api, lang)
        return
    elif text == "❓ Помощь":
        from .commands import help_command
        await help_command(update, context)
        return
    
    # Check if user is editing a transaction
    is_editing = await handle_edit_transaction_message(update, context)
    if is_editing:
        return  # Edit handled
    
    # Get token and API client
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Get user language
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Process with AI
    agent = AIAgent(api)
    result = await agent.process_message(user_id, text)
    
    response_text = result.get("response", "")
    created_transactions = result.get("created_transactions", [])
    
    # Show AI response only if no transactions created
    if not created_transactions and response_text:
        try:
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        except Exception:
            await update.message.reply_text(
                response_text,
                reply_markup=get_main_keyboard()
            )
    
    # Show each created transaction with Edit/Delete buttons
    if created_transactions:
        for tx_data in created_transactions:
            await show_transaction_with_actions(update, user_id, tx_data)


async def show_statistics(update: Update, api: MidasAPIClient, lang: str):
    """Show user statistics."""
    try:
        balance = await api.get_balance(period="month")
        breakdown = await api.get_category_breakdown(period="month")
        
        # Format statistics
        stats_text = get_message(lang, 'statistics_title') + "\n\n"
        balance_value = float(balance.get('balance', 0))
        stats_text += f"💰 {get_message(lang, 'balance')}: {balance_value:,.0f} {balance.get('currency', 'UZS')}\n\n"
        
        # Extract categories list
        if breakdown and isinstance(breakdown, dict):
            categories = breakdown.get('categories', [])
            if categories:
                stats_text += "**" + get_message(lang, 'by_categories') + ":**\n"
                for cat in categories[:5]:  # Top 5
                    cat_name = cat.get('category', get_message(lang, 'other'))
                    cat_total = float(cat.get('total', 0))
                    stats_text += f"• {cat_name}: {cat_total:,.0f}\n"
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.exception(f"Statistics error: {e}")
        await update.message.reply_text(
            "❌ " + get_message(lang, 'error_occurred'),
            reply_markup=get_main_keyboard()
        )

async def show_balance(update: Update, api: MidasAPIClient, lang: str):
    """Show user balance."""
    try:
        balance_data = await api.get_balance()
        balance_value = float(balance_data.get('balance', 0))
        currency = balance_data.get('currency', 'UZS')
        
        balance_text = f"💰 {get_message(lang, 'your_balance')}: {balance_value:,.0f} {currency}"
        
        await update.message.reply_text(
            balance_text,
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.exception(f"Balance error: {e}")
        await update.message.reply_text(
            "❌ " + get_message(lang, 'error_occurred'),
            reply_markup=get_main_keyboard()
        )
