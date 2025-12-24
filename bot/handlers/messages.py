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
from ..i18n import t, translate_category

logger = logging.getLogger(__name__)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with AI."""
    user_id = update.effective_user.id
    text = update.message.text
    lang = storage.get_user_language(user_id) or 'uz'
    
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text(t('auth.common.auth_required', lang))
        return
    
    if context.user_data.get('editing_tx'):
        from ..confirmation_handlers import handle_edit_message
        await handle_edit_message(update, context)
        return
    
    await process_text_message(update, context, text, user_id)


async def process_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, user_id: int):
    """Process any text message (typed or transcribed) through the main pipeline."""
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Handle menu buttons (compare with localized button text)
    button_balance = t('common.buttons.balance', lang)
    button_stats = t('common.buttons.statistics', lang)
    button_help = t('common.buttons.instructions', lang)
    
    if text == button_balance:
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        await show_balance(update, api, lang)
        return
    elif text == button_stats:
        token = storage.get_user_token(user_id)
        api = MidasAPIClient(config.API_BASE_URL)
        api.set_token(token)
        await show_statistics(update, api, lang)
        return
    elif text == button_help:
        from .commands import help_command
        await help_command(update, context)
        return
    
    # Check if editing transaction
    is_editing = await handle_edit_transaction_message(update, context)
    if is_editing:
        return
    
    # Get token and API client
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Process with AI
    agent = AIAgent(api)
    result = await agent.process_message(user_id, text)
    
    response_text = result.get("response", "")
    created_transactions = result.get("created_transactions", [])
    created_debts = result.get("created_debts", [])
    
    # Show AI response (only if no transactions/debts created)
    if not created_transactions and not created_debts and response_text:
        try:
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard(lang)
            )
        except Exception:
            await update.message.reply_text(
                response_text,
                reply_markup=get_main_keyboard(lang)
            )
            
    # Show each created transaction with Edit/Delete buttons
    if created_transactions:
        for tx_data in created_transactions:
            await show_transaction_with_actions(update, user_id, tx_data)

    # Show created debts
    if created_debts:
        for debt in created_debts:
            # debt: {debt_id, person, amount, type}
            amount_val = float(debt.get('amount', 0))
            amount_str = f"{amount_val:,.0f}".replace(",", " ")
            currency = debt.get('currency', 'UZS')
            
            debt_type_key = 'debts.i_owe' if debt.get('type') == 'i_owe' else 'debts.owe_me'
            
            text = f"{t('debts.new_debt_created', lang)}\n\n"
            text += f"{t(debt_type_key, lang)}\n"
            text += f"{t('debts.person', lang)}: {debt.get('person')}\n"
            text += f"{t('debts.amount', lang)}: {amount_str} {currency}\n"
            
            if debt.get('due_date'):
               text += f"{t('debts.due_date', lang)}: {debt.get('due_date')}\n"

            if debt.get('description'):
               text += f"{t('debts.description', lang)}: {debt.get('description')}\n"
            
            await update.message.reply_text(
                text,
                reply_markup=get_main_keyboard(lang)
            )


async def show_statistics(update: Update, api: MidasAPIClient, lang: str):
    """Show user statistics."""
    try:
        balance = await api.get_balance(period="month")
        breakdown = await api.get_category_breakdown(period="month")
        
        stats_text = t('transactions.stats.month', lang)
        
        if breakdown and isinstance(breakdown, dict):
            categories = breakdown.get('categories', [])
            total_expense = float(breakdown.get('total', 0))
            
            if categories:
                stats_text += t('transactions.stats.by_categories', lang)
                
                # Filter out zero amounts and sort
                valid_cats = [c for c in categories if float(c.get('amount', 0)) > 0]
                valid_cats.sort(key=lambda x: float(x.get('amount', 0)), reverse=True)
                
                for cat in valid_cats[:7]:
                    # Get category slug and translate
                    cat_slug = cat.get('category_slug') or cat.get('slug', '')
                    cat_name = translate_category(cat_slug, lang) if cat_slug else translate_category('other', lang)
                    
                    cat_total = float(cat.get('amount', 0))
                    
                    # Calculate percentage
                    percentage = 0
                    if total_expense > 0:
                        percentage = (cat_total / total_expense) * 100
                    
                    stats_text += f"• {cat_name}: {cat_total:,.0f} ({percentage:.1f}%)\n"
                
                currency = balance.get('currency', 'UZS')
                stats_text += f"\n{t('common.common.total', lang)}: {total_expense:,.0f} {currency}"
            else:
                stats_text += t('transactions.stats.no_data', lang)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=get_main_keyboard(lang)
        )
    except Exception as e:
        logger.exception(f"Statistics error: {e}")
        await update.message.reply_text(
            t('transactions.stats.error', lang),
            reply_markup=get_main_keyboard(lang)
        )


async def show_balance(update: Update, api: MidasAPIClient, lang: str):
    """Show user balance."""
    try:
        balance_data = await api.get_balance()
        balance_value = float(balance_data.get('balance', 0))
        currency = balance_data.get('currency', 'UZS')
        
        balance_text = t('transactions.balance.month', lang)
        balance_formatted = f"{balance_value:,.0f}".replace(",", " ")
        balance_text += f"💰 {t('transactions.balance.your_balance', lang)}: {balance_formatted} {currency}\n\n"
        
        # Add recent transactions
        try:
            transactions_data = await api.get_transactions(limit=5)
            # Handle paginated response
            if isinstance(transactions_data, dict) and 'items' in transactions_data:
                transactions = transactions_data['items']
            elif isinstance(transactions_data, list):
                transactions = transactions_data
            else:
                transactions = []

            if transactions:
                balance_text += t('transactions.balance.last_transactions', lang)
                for tx in transactions:
                    icon = "📈" if tx['type'] == 'income' else "📉"
                    amount = float(tx['amount'])
                    
                    # Get description or category
                    desc = tx.get('description', '')
                    if not desc:
                        category = tx.get('category', {})
                        if isinstance(category, dict):
                            cat_slug = category.get('slug', '')
                            desc = translate_category(cat_slug, lang) if cat_slug else t('categories.other', lang)
                        else:
                            desc = translate_category('other', lang)
                    
                    balance_text += f"{icon} {amount:,.0f} - {desc}\n"
        except Exception as e:
            logger.error(f"Failed to fetch recent transactions: {e}")

        await update.message.reply_text(
            balance_text,
            reply_markup=get_main_keyboard(lang)
        )
    except Exception as e:
        logger.exception(f"Balance error: {e}")
        await update.message.reply_text(
            t('common.common.error', lang),
            reply_markup=get_main_keyboard(lang)
        )
