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



async def get_transaction_message_data(user_id: int, tx_data: Dict[str, Any]) -> tuple[str, InlineKeyboardMarkup]:
    """Helper to generate transaction message text and markup."""
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
    
    return text, InlineKeyboardMarkup(keyboard)


async def show_transaction_with_actions(
    update: Update,
    user_id: int,
    tx_data: Dict[str, Any]
) -> None:
    """Show created transaction with Edit/Delete buttons."""
    text, reply_markup = await get_transaction_message_data(user_id, tx_data)
    
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    logger.info(f"Transaction shown: {tx_data.get('transaction_id')}")


async def restore_transaction_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, user_id: int, tx_id: str):
    """Restore the transaction message content (used when cancelling edit)."""
    try:
        # Fetch current transaction data
        token = storage.get_user_token(user_id)
        api = BarakaAPIClient(config.API_BASE_URL)
        api.set_token(token)
        
        fresh_tx = await api.get_transaction(tx_id)
        
        # Reconstruct tx_data
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
        
        text, reply_markup = await get_transaction_message_data(user_id, tx_data)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to restore transaction message: {e}")


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
            ],
            [
                InlineKeyboardButton(t('common.actions.back', lang), callback_data=f"cancel_edit_{tx_id}")
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


async def handle_edit_transaction_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text_override: str = None):
    """Handle message when user is editing a transaction."""
    tx_id = context.user_data.pop('editing_transaction_id', None)
    context.user_data.pop('editing_message_id', None) # Clear stored message ID
    
    if not tx_id:
        return False
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    text = text_override if text_override is not None else update.message.text
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # Fetch current transaction
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
        
        updates = {}
        
        if 'editing_field' in context.user_data:
            field = context.user_data.pop('editing_field') # consumed
            logger.info(f"Editing specific field '{field}' with text: {text}")
            
            # Use AI to parse the specific field update
            # We explicitly tell AI which field is being updated
            prompt_context = f"Update {field} to: {text}"
            
            agent_updates = await agent.edit_transaction(old_data, prompt_context)
            
            # Filter updates based on field (optional safety, but AI usually does right thing)
            # If user said "70k", AI returns {"amount": 70000}.
            
            # Map standard fields
            if field == 'amount':
                if 'amount' in agent_updates:
                    updates['amount'] = agent_updates['amount']
            elif field == 'category':
                 if 'category_id' in agent_updates:
                    updates['category_id'] = agent_updates['category_id']
                 elif 'category_slug' in agent_updates:
                    updates['category_slug'] = agent_updates['category_slug']
            elif field == 'description':
                 if 'description' in agent_updates:
                    updates['description'] = agent_updates['description']
            
            # If primary field missing in update, fallback to using whatever AI returned
            if not updates:
                updates = agent_updates
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
    
    try:
        parts = query.data.split('_')
        logger.info(f"Edit field callback data: {query.data}, parts: {parts}")
        
        # pattern: edit_field_{tx_id}_{field}
        # parts: [edit, field, tx, id, ..., field]
        
        if len(parts) < 4:
            logger.error(f"Invalid callback data parts length: {len(parts)}")
            return

        field = parts[-1]
        tx_id = "_".join(parts[2:-1])
        
        logger.info(f"Extracted tx_id: {tx_id}, field: {field}")
        
        context.user_data['editing_transaction_id'] = tx_id
        context.user_data['editing_field'] = field
        context.user_data['editing_message_id'] = query.message.message_id # Store message ID
        
        user_id = query.from_user.id
        lang = storage.get_user_language(user_id) or 'uz'
        
        prompt_key = f"transactions.actions.enter_{field}"
        prompt = t(prompt_key, lang)
        
        
        logger.info(f"Prompt key: {prompt_key}, translated: {prompt}")
        
        # Add a "Back" button to cancel editing
        back_text = t('common.actions.back', lang) # "Back" or "Назад"
        keyboard = [[InlineKeyboardButton(back_text, callback_data=f"cancel_edit_{tx_id}")]]
        
        await query.edit_message_text(
            prompt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        logger.info("Message edited successfully")
        
    except Exception as e:
        logger.exception(f"Error in handle_edit_field_callback: {e}")
        await query.edit_message_text(f"Error: {str(e)}")


async def handle_cancel_edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancellation of manual edit (Back button)."""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split('_')
        # pattern: cancel_edit_{tx_id}
        if len(parts) < 3:
            return
            
        tx_id = "_".join(parts[2:]) # Rejoin just in case UUID has underscores (unlikely but safe)
        
        user_id = query.from_user.id
        chat_id = update.effective_chat.id
        message_id = query.message.message_id
        
        # Clear editing states
        context.user_data.pop('editing_transaction_id', None)
        context.user_data.pop('editing_field', None)
        context.user_data.pop('editing_message_id', None)
        
        # Restore the transaction card
        await restore_transaction_message(context, chat_id, message_id, user_id, tx_id)
        
    except Exception as e:
        logger.exception(f"Error in handle_cancel_edit_callback: {e}")


# Export handler
transaction_action_handler = CallbackQueryHandler(
    handle_transaction_action,
    pattern="^(edit|delete)_tx_"
)

transaction_edit_field_handler = CallbackQueryHandler(
    handle_edit_field_callback,
    pattern="^edit_field_"
)

transaction_cancel_edit_handler = CallbackQueryHandler(
    handle_cancel_edit_callback,
    pattern="^cancel_edit_"
)
