"""Debt action handlers - Edit, Delete, and Settle functionality."""
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Dict, Any
from datetime import datetime

from .api_client import MidasAPIClient
from .config import config
from .user_storage import storage
from .i18n import t

logger = logging.getLogger(__name__)


async def show_debt_with_actions(
    update: Update,
    user_id: int,
    debt_data: Dict[str, Any]
) -> None:
    """Show created/existing debt with Edit/Delete/Settle buttons."""
    debt_id = debt_data.get('debt_id') or debt_data.get('id')
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Debt properties
    person = debt_data.get('person') or debt_data.get('person_name')
    amount = float(debt_data.get('amount', 0))
    currency_code = debt_data.get('currency', 'UZS').upper()
    current_type = debt_data.get('type')
    description = debt_data.get('description', '')
    due_date = debt_data.get('due_date')

    amount_str = f"{amount:,.0f}".replace(",", " ")
    
    # Emojis and titles
    if current_type == 'i_owe':
        type_emoji = "🔴"
        type_text = t('debts.i_owe', lang)
    else:  # owe_me
        type_emoji = "🟢"
        type_text = t('debts.owe_me', lang)

    # Format Date
    # If created just now, we can use today. Or if it has created_at
    created_at_iso = debt_data.get('created_at')
    if created_at_iso:
        try:
            date_obj = datetime.fromisoformat(created_at_iso.replace('Z', '+00:00'))
            date_str = date_obj.strftime("%d.%m.%Y")
        except:
            date_str = datetime.now().strftime("%d.%m.%Y")
    else:
        date_str = datetime.now().strftime("%d.%m.%Y")

    # Construct Message
    text = (
        f"**{t('debts.new_debt_created', lang)} {type_emoji}**\n\n"
        f"**{type_text}**\n"
        f"**{t('debts.person', lang)}:** {person}\n"
        f"**{t('debts.amount', lang)}:** {amount_str} {currency_code}\n"
    )

    if due_date:
        text += f"**{t('debts.due_date', lang)}:** {due_date}\n"
    
    if description:
        text += f"**{t('debts.description', lang)}:** {description}\n"

    # Add Edit / Delete / Settle buttons
    keyboard = []
    
    # First row: Settle (Söndirish/Погасить)
    keyboard.append([
        InlineKeyboardButton(f"{t('debts.actions.settle', lang)}", callback_data=f"settle_debt_{debt_id}")
    ])
    
    # Second row: Cancel (Delete) | Edit
    keyboard.append([
        InlineKeyboardButton(t('common.actions.cancel', lang), callback_data=f"delete_debt_{debt_id}"),
        InlineKeyboardButton(t('common.actions.edit', lang), callback_data=f"edit_debt_{debt_id}")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"Debt shown: {debt_id}")


async def handle_debt_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Settle/Edit/Delete callbacks for debts."""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    # Expected format: action_debt_ID -> split('_') -> [action, "debt", ID...]
    # action = parts[0] (settle/edit/delete)
    # debt_id = parts[2:] joined
    
    action = parts[0]
    debt_id = '_'.join(parts[2:])
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    token = storage.get_user_token(user_id)
    
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)

    if action == "settle":
        # Usually settle means paid. We can confirm or just do it.
        # Let's do it immediately for simplicity as per request "add button settle"
        try:
            result = await api.mark_debt_as_paid(debt_id)
            # Edit usage to show it is settled
            person = result.get('person_name')
            amount = float(result.get('amount', 0))
            currency = result.get('currency', 'UZS')
            
            await query.edit_message_text(
                f"{t('debts.actions.settled_success', lang)}\n\n"
                f"{t('debts.person', lang)}: {person}\n"
                f"{t('debts.amount', lang)}: {amount:,.0f} {currency}"
            )
        except Exception as e:
            logger.error(f"Failed to settle debt: {e}")
            await query.edit_message_text(f"{t('common.common.error', lang)}: {str(e)}")

    elif action == "delete":
        try:
            await api.delete_debt(debt_id)
            await query.edit_message_text(t('debts.actions.deleted', lang))
        except Exception as e:
            logger.error(f"Failed to delete debt: {e}")
            await query.edit_message_text(f"{t('common.common.error', lang)}: {str(e)}")

    elif action == "edit":
        context.user_data['editing_debt_id'] = debt_id
        await query.edit_message_text(t('debts.actions.edit_prompt', lang))


async def handle_edit_debt_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle message when user is editing a debt."""
    debt_id = context.user_data.pop('editing_debt_id', None)
    if not debt_id:
        return False
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    text = update.message.text
    
    token = storage.get_user_token(user_id)
    api = MidasAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        updates = {}
        
        # Parse amount like transaction editing
        # "Ali 50k" -> name + amount? Or just description/amount?
        # Let's support updating amount and description/person
        # Re-use simple parsing logic
        
        ming_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(?:ming|минг)', text, re.IGNORECASE)
        k_match = re.search(r'(\d+(?:[.,]\d+)?)\s*k\b', text, re.IGNORECASE)
        plain_match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        
        amount = None
        if ming_match:
            amount = float(ming_match.group(1).replace(',', '.')) * 1000
        elif k_match:
            amount = float(k_match.group(1).replace(',', '.')) * 1000
        elif plain_match:
            # If plain number is significant part of message
            amount = float(plain_match.group(1).replace(',', '.'))
        
        description = re.sub(r'\d+(?:[.,]\d+)?\s*(?:ming|минг|k)?', '', text, flags=re.IGNORECASE).strip()
        
        if amount:
            updates['amount'] = amount
            
        if description:
            # Check if user meant person_name or description
            # Since simpler editing is ambiguous, let's treat text as description 
            # OR we could just update description.
            # But user might want to change person name.
            # Let's update description for now.
            updates['description'] = description

        # If only text provided without numbers, maybe update description
        if not amount and text:
            updates['description'] = text

        # Update debt
        result = await api.update_debt(debt_id, **updates)
        
        await show_debt_with_actions(update, user_id, result)
        return True
        
    except Exception as e:
        logger.exception(f"Edit debt error: {e}")
        from .handlers.common import get_main_keyboard
        await update.message.reply_text(
            f"{t('common.common.error', lang)}: {str(e)}",
            reply_markup=get_main_keyboard(lang)
        )
        return True

# Export handler
debt_action_handler = CallbackQueryHandler(
    handle_debt_action,
    pattern="^(settle|edit|delete)_debt_"
)
