"""Transaction action handlers - Edit and Delete functionality."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Dict, Any

from .api_client import MidasAPIClient
from .config import config
from .user_storage import storage
from .handlers.common import get_main_keyboard
from .lang_messages import get_message

logger = logging.getLogger(__name__)


async def show_transaction_with_actions(
    update: Update,
    user_id: int,
    tx_data: Dict[str, Any]
) -> None:
    """Show created transaction with Edit/Delete buttons."""
    tx_id = tx_data.get('transaction_id')
    # Get localized strings
    lang = storage.get_user_language(user_id) or 'uz'
    
    type_emoji = "📈" if tx_data['type'] == 'income' else "📉"
    type_text = get_message(lang, 'income') if tx_data['type'] == 'income' else get_message(lang, 'expense')
    amount_text = f"{float(tx_data['amount']):,.0f} {tx_data.get('currency', 'UZS')}"
    
    desc = tx_data.get('description', '')
    category = tx_data.get('category')
    
    # Format message
    # Example:
    # ✅ Xarajat yozildi!
    # 📉 50,000 UZS
    # 📝 Tushlik
    # 🏷 Oziq-ovqat
    
    status_msg = get_message(lang, 'income_recorded' if tx_data['type'] == 'income' else 'expense_recorded')
    # Add checkmark if not already present in localized string (it is not)
    status_msg = f"✅ {status_msg}"
    
    text = (
        f"{status_msg}\n"
        f"{type_emoji} {amount_text}\n"
        f"📝 {desc}"
    )
    if category:
        text += f"\n🏷 {category['name'] if isinstance(category, dict) else category}"

    keyboard = [
        [
            InlineKeyboardButton(f"{get_message(lang, 'edit_btn')}", callback_data=f"edit_tx_{tx_id}"),
            InlineKeyboardButton(f"{get_message(lang, 'delete_btn')}", callback_data=f"delete_tx_{tx_id}")
        ]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_transaction_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Edit/Delete callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Parse: "edit_tx_123" or "delete_tx_123"
    parts = query.data.split('_')
    action = parts[0]  # "edit" or "delete"
    tx_id = '_'.join(parts[2:])  # transaction ID (might contain underscores)
    
    user_id = query.from_user.id
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Get localized strings (reuse user_id from query)
    # Note: query.from_user.id is used above
    lang = storage.get_user_language(user_id) or 'uz'

    if action == "edit":
        # Start edit mode
        context.user_data['editing_transaction_id'] = tx_id
        await query.edit_message_text(get_message(lang, 'edit_prompt'))
        
    elif action == "delete":
        # Delete transaction
        try:
            await api.delete_transaction(tx_id)
            await query.edit_message_text(get_message(lang, 'deleted'))
        except Exception as e:
            logger.error(f"Failed to delete transaction: {e}")
            await query.edit_message_text(f"❌ {get_message(lang, 'error_generic')}: {str(e)}")


async def handle_edit_transaction_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message when user is editing a transaction."""
    tx_id = context.user_data.pop('editing_transaction_id', None)
    if not tx_id:
        return False  # Not editing
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    text = update.message.text
    
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # Parse the edit text to extract updates
        # Support "50ming", "50k" etc for thousands
        import re
        
        updates = {}
        
        # Check for multipliers first (ming, k)
        ming_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:ming|минг)', text, re.IGNORECASE)
        k_match = re.search(r'(\d+(?:[.,]\d+)?)\s*k\b', text, re.IGNORECASE)
        plain_match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        
        if ming_match:
            updates['amount'] = float(ming_match.group(1).replace(',', '.')) * 1000
        elif k_match:
            updates['amount'] = float(k_match.group(1).replace(',', '.')) * 1000
        elif plain_match:
            updates['amount'] = float(plain_match.group(1).replace(',', '.'))
        
        # Get description (remove numbers and multipliers)
        description = re.sub(r'\d+(?:[.,]\d+)?\s*(?:ming|минг|k)?', '', text, flags=re.IGNORECASE).strip()
        if description:
            updates['description'] = description
        
        # If no changes detected, use whole text as description
        if not updates:
            updates['description'] = text
        
        # Update transaction
        result = await api.update_transaction(tx_id, **updates)
        
        # Show updated transaction with Edit/Delete buttons
        tx_data = {
            'transaction_id': str(result['id']),
            'amount': result.get('amount', 0),
            'description': result.get('description', ''),
            'type': result.get('type', 'expense'),
            'currency': result.get('currency', 'uzs')
        }
        
        await show_transaction_with_actions(update, user_id, tx_data)
        
        return True  # Handled
        
    except Exception as e:
        logger.exception(f"Edit error: {e}")
        await update.message.reply_text(
            f"❌ {get_message(lang, 'error_generic')}: {str(e)}",
            reply_markup=get_main_keyboard(lang)
        )
        return True  # Handled


# Export handler
transaction_action_handler = CallbackQueryHandler(
    handle_transaction_action,
    pattern="^(edit|delete)_tx_"
)
