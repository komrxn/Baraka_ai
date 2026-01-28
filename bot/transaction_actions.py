"""Transaction action handlers - Edit and Delete functionality."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Dict, Any
from datetime import datetime

from .api_client import BarakaAPIClient
from .config import config
from .user_storage import storage
from .i18n import t, translate_category
from .handlers.common import send_typing_action

logger = logging.getLogger(__name__)


async def show_transaction_with_actions(
    update: Update,
    user_id: int,
    tx_data: Dict[str, Any]
) -> None:
    """Show created transaction with Edit/Delete buttons."""
    tx_id = tx_data.get('transaction_id')
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Fetch current balance
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(storage.get_user_token(user_id))
    try:
        balance_data = await api.get_balance()
        balance_value = float(balance_data.get('balance', 0))
        currency = balance_data.get('currency', 'UZS').upper()
    except Exception as e:
        logger.warning(f"Could not fetch balance for tx message: {e}")
        balance_value = 0
        currency = 'UZS'

    # Transaction type
    type_val = tx_data.get('type', 'expense')
    type_emoji = t(f"transactions.type_emoji.{type_val}", lang)
    type_text = t(f"transactions.type.{type_val}", lang)
    
    # Amount formatting
    amount = float(tx_data.get('amount', 0))
    amount_formatted = f"{amount:,.0f}".replace(",", " ")
    currency_lower = tx_data.get('currency', 'UZS').lower()
    
    # Category translation
    category = tx_data.get('category')
    if isinstance(category, dict):
        category_slug = category.get('slug', '')
        category_name = translate_category(category_slug, lang) if category_slug else translate_category('general', lang)
    elif isinstance(category, str):
        category_name = translate_category(category, lang)
    else:
        category_name = translate_category('general', lang)
    
    # Description
    desc = tx_data.get('description', '')
    
    # Date
    date_str = datetime.now().strftime("%d.%m.%Y")

    # Construct message
    text = (
        f"**{t('transactions.created', lang)}**\n\n"
        f"{type_emoji} **{type_text}:**\n"
        f"{t('transactions.fields.date', lang)}: {date_str}\n\n"
        f"**{t('transactions.fields.amount', lang)}:** {currency_lower} {amount_formatted}\n"
        f"**{t('transactions.fields.category', lang)}:** {category_name}\n"
    )
    
    if desc:
        text += f"**{t('transactions.fields.description', lang)}:** {desc}\n"
    
    # Balance display
    balance_formatted = f"{balance_value:,.2f}".replace(",", " ")
    text += f"\n💰 {t('common.common.balance', lang)}: {currency.lower()} {balance_formatted}"

    # Buttons
    keyboard = [
        [
            InlineKeyboardButton(t('common.actions.cancel', lang), callback_data=f"delete_tx_{tx_id}"),
            InlineKeyboardButton(t('common.actions.edit', lang), callback_data=f"edit_tx_{tx_id}")
        ]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    logger.info(f"Transaction shown: {tx_id}")


async def handle_transaction_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Edit/Delete callbacks."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    action = parts[0]
    tx_id = '_'.join(parts[2:])
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    token = storage.get_user_token(user_id)
    
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)

    if action == "edit":
        # Show field selection keyboard
        keyboard = [
            [
                InlineKeyboardButton(t('transactions.actions.edit_amount', lang), callback_data=f"edit_field_{tx_id}_amount"),
                InlineKeyboardButton(t('transactions.actions.edit_category', lang), callback_data=f"edit_field_{tx_id}_category")
            ],
            [
                InlineKeyboardButton(t('transactions.actions.edit_description', lang), callback_data=f"edit_field_{tx_id}_description")
            ]
        ]
        await query.edit_message_text(
            t('transactions.actions.select_field', lang),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif action == "delete":
        try:
            await api.delete_transaction(tx_id)
            await query.edit_message_text(t('transactions.actions.deleted', lang))
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            await query.edit_message_text(f"{t('common.common.error', lang)}: {str(e)}")


@send_typing_action
async def handle_edit_transaction_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message when user is editing a transaction."""
    tx_id = context.user_data.pop('editing_transaction_id', None)
    if not tx_id:
        return False
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    text = update.message.text
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # Fetch current transaction to provide context to AI
        current_tx = {}
        try:
            # We need to fetch full details. The listing endpoint gives summary, but let's see if we can get by ID
            # BarakaAPIClient doesn't have get_transaction_by_id yet, but we can reconstruct from what we have 
            # or add get_transaction. For now, let's assume we can proceed with partial info or
            # better: implement get_transaction in api_client.py if needed.
            # actually we can just pass what we know, or fetch.
            # Let's try to fetch list and find it (inefficient) or just rely on user input?
            # AI needs context. "Taxi" -> "Switch to Metro" needs to know it was Taxi.
            # Let's add get_transaction to api_client first? 
            # Or just use get_transactions with limit if recently created.
            pass
        except:
            pass
        
        # NOTE: We need a way to get the current transaction details!
        # Since we don't have get_transaction(id), we will try to fetch recent.
        # But this is inside edit flow.
        
        # Let's assume we added get_transaction to api_client.py. If not, I should add it.
        # Checking api_client.py... it does NOT have get_transaction(id).
        # purely update_transaction.
        
        # I will add get_transaction to api_client first.
        # But for now, let's assume I will add it in next step.
        
        # Wait, I cannot use it if it's not there.
        # I'll implement the call assuming method exists, then I'll add the method.
        
        # Actually, let's look at `show_transaction_with_actions`... it takes `tx_data`.
        # We don't have `tx_data` stored in context (only ID).
        # I will add `get_transaction` to `BarakaAPIClient` in `api_client.py` IMMEDIATELY after this tool call.
        
        current_tx = await api.get_transaction(tx_id)
        
        # Prepare data for AI
        old_data = {
            "amount": float(current_tx.get('amount', 0)),
            "description": current_tx.get('description', ''),
            "category_slug": current_tx.get('category', {}).get('slug', ''),
            "type": current_tx.get('type', 'expense'),
            "currency": current_tx.get('currency', 'uzs')
        }
        
        from .ai_agent import AIAgent
        agent = AIAgent(api)
        
        if 'editing_field' in context.user_data:
            field = context.user_data['editing_field']
            updates = {}
            
            if field == 'amount':
                # Parse amount
                import re
                # simple parser: remove non-numeric except dot
                clean_text = re.sub(r'[^\d.]', '', text.replace(',', '.'))
                try:
                    amount = float(clean_text)
                    updates = {'amount': amount}
                except ValueError:
                    await update.message.reply_text(t('common.common.error', lang))
                    return True
                    
            elif field == 'category':
                # For category, user types name. We might need slug.
                # Let's assume API can take slug OR we try to find it.
                # Actually, API usually expects ID or slug.
                # Text input for category is tricky without lookup.
                # Let's pass it as 'category_slug' if it matches known slugs,
                # or rely on backend/agent to resolve it?
                # agent.edit_transaction is smart. Let's use it but scoped?
                # For now simplify: User text -> description? No.
                # Let's use AI agent to resolve category from text.
                
                # We can reuse the Agent for category resolution!
                agent_updates = await agent.edit_transaction(old_data, f"change category to {text}")
                if 'category_slug' in agent_updates:
                    updates = {'category_slug': agent_updates['category_slug']}
                else:
                    # Fallback or error
                    pass
            
            elif field == 'description':
                updates = {'description': text}
                
            # Clear field state
            del context.user_data['editing_field']
            
        else:
            # Legacy/Fallback: Generic AI edit
            updates = await agent.edit_transaction(old_data, text)
        
        if not updates:
             await update.message.reply_text(t('common.common.error', lang))
             return True
             
        # Update transaction
        await api.update_transaction(tx_id, **updates)
        
        # Fetch fresh transaction data to ensure we have full category details
        fresh_tx = await api.get_transaction(tx_id)
        
        # Show updated transaction
        category_data = fresh_tx.get('category', {})
        category_slug = category_data.get('slug', 'other_expense') if isinstance(category_data, dict) else 'other_expense'
        
        tx_data = {
            'transaction_id': str(fresh_tx['id']),
            'amount': fresh_tx.get('amount', 0),
            'description': fresh_tx.get('description', ''),
            'type': fresh_tx.get('type', 'expense'),
            'currency': fresh_tx.get('currency', 'uzs'),
            'category': category_slug
        }
        
        await show_transaction_with_actions(update, user_id, tx_data)
        return True
        
    except Exception as e:
        logger.exception(f"Edit error: {e}")
        from .handlers.common import get_main_keyboard
        await update.message.reply_text(
            f"{t('common.common.error', lang)}: {str(e)}",
            reply_markup=get_main_keyboard(lang)
        )
        return True


async def handle_edit_field_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection for editing."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    # pattern: edit_field_{tx_id}_{field}
    # parts: [edit, field, tx, id, ..., field]
    # Reconstruct tx_id carefully since it might contain underscores? UUIDs usually don't but just in case.
    # Actually split logic: 
    # query.data = "edit_field_<TX_ID>_<FIELD>"
    # TX_ID is UUID? 
    # Let's assume field is the LAST part.
    
    field = parts[-1]
    tx_id = "_".join(parts[2:-1])
    
    context.user_data['editing_transaction_id'] = tx_id
    context.user_data['editing_field'] = field
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    prompt_key = f"transactions.actions.enter_{field}"
    prompt = t(prompt_key, lang)
    
    await query.edit_message_text(prompt)

# Export handler
transaction_action_handler = CallbackQueryHandler(
    handle_transaction_action,
    pattern="^(edit|delete)_tx_"
)

transaction_edit_field_handler = CallbackQueryHandler(
    handle_edit_field_callback,
    pattern="^edit_field_"
)
