"""Text message handler - AI integration."""
from telegram import Update
from telegram.ext import ContextTypes
import logging

from ..user_storage import storage
from ..api_client import MidasAPIClient
from ..config import config
from .common import with_auth_check, get_main_keyboard
from .balance import get_balance
from ..confirmation_handlers import show_transaction_confirmation

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - menu buttons and AI agent."""
    if not storage.is_user_authorized(update.effective_user.id):
        await update.message.reply_text("⛔ Сначала авторизуйся: /start")
        return
    
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check if user is editing a transaction
    if context.user_data.get('editing_tx'):
        from ..confirmation_handlers import handle_edit_message
        await handle_edit_message(update, context)
        return
    
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
            
            # Format statistics
            stats_text = "📊 **Статистика за месяц**\n\n"
            # Convert balance to float (API returns string)
            balance_value = float(balance.get('balance', 0))
            stats_text += f"💰 Баланс: {balance_value:,.0f} {balance.get('currency', 'UZS')}\n\n"
            
            # Extract categories list from breakdown response
            if breakdown and isinstance(breakdown, dict):
                categories = breakdown.get('categories', [])
                if categories:
                    stats_text += "**По категориям:**\n"
                    for cat in categories[:5]:  # Top 5
                        cat_name = cat.get('category', 'Другое')
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
                "❌ Ошибка получения статистики",
                reply_markup=get_main_keyboard()
            )
        return
    elif text == "❓ Помощь":
        from .commands import help_command
        await help_command(update, context)
        return
    
    # Use AI agent for all other messages
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Send typing action
    await update.message.chat.send_action(action="typing")
    
    async def _process_with_ai():
        from ..ai_agent import AIAgent
        agent = AIAgent(api)
        return await agent.process_message(user_id, text)
    
    result = await with_auth_check(update, user_id, _process_with_ai)
    if result is None:
        return  # Auth failed, user prompted to /start
    
    # Extract response and transactions from AI result
    response = result.get("response", "")
    parsed_transactions = result.get("parsed_transactions", [])
    
    # Only send AI response if no transactions (confirmations will show everything)
    if not parsed_transactions:
        try:
            await update.message.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )
        except Exception as markdown_error:
            logger.warning(f"Markdown parsing failed, sending plain text: {markdown_error}")
            await update.message.reply_text(
                response,
                reply_markup=get_main_keyboard()
            )
    
    # Show confirmation for each parsed transaction
    if parsed_transactions:
        for tx_data in parsed_transactions:
            await show_transaction_confirmation(update, user_id, tx_data)
