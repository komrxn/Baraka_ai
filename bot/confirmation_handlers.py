"""Transaction confirmation handlers."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Dict, Any

from .api_client import BarakaAPIClient
from .config import config
from .user_storage import storage
from .pending_storage import pending_storage
from .handlers.common import get_main_keyboard
from .i18n import t, translate_category

logger = logging.getLogger(__name__)


async def show_transaction_confirmation(
    update: Update,
    user_id: int,
    tx_data: Dict[str, Any]
) -> str:
    """Show transaction confirmation with buttons."""
    # Store pending transaction
    tx_id = pending_storage.add(user_id, tx_data)
    
    # Get user language
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Format message
    # tx_type = "💰 Доход" if tx_data['type'] == 'income' else "💸 Расход"
    tx_type_val = tx_data.get('type', 'expense')
    tx_type_emoji = t(f"transactions.type_emoji.{tx_type_val}", lang)
    tx_type_text = t(f"transactions.type.{tx_type_val}", lang)
    
    amount_str = f"{tx_data['amount']:,.0f}".replace(',', ' ')
    currency = tx_data.get('currency', 'UZS').upper()
    
    # Get category name if available
    category_text = ""
    if tx_data.get('category_slug'):
        # category_text = f"\n📁 Категория: {tx_data['category_slug']}"
        cat_name = translate_category(tx_data['category_slug'], lang)
        category_text = f"\n📁 {t('transactions.fields.category', lang)}: {cat_name}"
    
    # message = (
    #     f"{tx_type}\n"
    #     f"💵 Сумма: {amount_str} {currency}\n"
    #     f"📝 Описание: {tx_data['description']}"
    #     f"{category_text}\n\n"
    #     "Подтвердить?"
    # )
    
    message = (
        f"{tx_type_emoji} {tx_type_text}\n"
        f"💵 {t('transactions.fields.amount', lang)}: {amount_str} {currency}\n"
        f"📝 {t('transactions.fields.description', lang)}: {tx_data['description']}"
        f"{category_text}\n\n"
        f"{t('transactions.confirmation.prompt', lang)}"
    )
    
    # Create buttons
    keyboard = [
        [
            InlineKeyboardButton(t('common.actions.confirm', lang), callback_data=f"confirm_{tx_id}"),
        ],
        [
            InlineKeyboardButton(t('common.actions.cancel', lang), callback_data=f"cancel_{tx_id}"),
            InlineKeyboardButton(t('common.actions.edit', lang), callback_data=f"edit_{tx_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    return tx_id


async def handle_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transaction confirmation callbacks."""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data
    action, tx_id = query.data.split('_', 1)
    
    # Get user language (we need user_id first, attempt to get it from query)
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Get pending transaction
    pending = pending_storage.get(tx_id)
    if not pending:
        # await query.edit_message_text("⏰ Время подтверждения истекло")
        await query.edit_message_text(t('transactions.confirmation.expired', lang))
        return
    
    if pending['user_id'] != user_id:
        # await query.answer("❌ Это не твоя транзакция", show_alert=True)
        await query.answer(t('transactions.confirmation.not_yours', lang), show_alert=True)
        return
    
    tx_data = pending['tx_data']
    
    if action == "confirm":
        # Create transaction
        token = storage.get_user_token(user_id)
        api = BarakaAPIClient(config.API_BASE_URL)
        api.set_token(token)
        
        try:
            # Get category_id from slug if provided
            if tx_data.get('category_slug'):
                categories = await api.get_categories()
                for cat in categories:
                    if cat.get('slug') == tx_data['category_slug']:
                        tx_data['category_id'] = cat['id']
                        break
                del tx_data['category_slug']  # Remove slug, keep only ID
            
            result = await api.create_transaction(tx_data)
            
            # Format success message
            amount_str = f"{tx_data['amount']:,.0f}".replace(',', ' ')
            # tx_type = "доход" if tx_data['type'] == 'income' else "расход"
            
            # await query.edit_message_text(
            #     f"✅ {tx_type.capitalize()} записан!\n"
            #     f"💵 {amount_str} {tx_data.get('currency', 'UZS').upper()}"
            # )
            
            await query.edit_message_text(
                f"{t('transactions.confirmation.recorded', lang)}\n"
                f"💵 {amount_str} {tx_data.get('currency', 'UZS').upper()}"
            )
            
            # Clean up
            pending_storage.remove(tx_id)
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {e}")
            # await query.edit_message_text(f"❌ Ошибка: {str(e)}")
            await query.edit_message_text(f"{t('transactions.confirmation.error', lang)}: {str(e)}")
    
    elif action == "cancel":
        # await query.edit_message_text("❌ Отменено")
        await query.edit_message_text(t('transactions.confirmation.cancelled', lang))
        pending_storage.remove(tx_id)
    
    elif action == "edit":
        # Start edit dialog
        # await query.edit_message_text(
        #     "✏️ Редактирование транзакции\n\n"
        #     "Напиши новую сумму или описание:"
        # )
        await query.edit_message_text(t('transactions.actions.edit_prompt', lang))
        # Store edit state
        context.user_data['editing_tx'] = tx_id


async def handle_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle message when user is editing a transaction."""
    tx_id = context.user_data.pop('editing_tx', None)
    if not tx_id:
        return
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    # Get pending transaction
    pending = pending_storage.get(tx_id)
    if not pending:
        # await update.message.reply_text("⏰ Время редактирования истекло")
        await update.message.reply_text(t('transactions.confirmation.expired', lang))
        return
    
    text = update.message.text
    
    # Get old transaction data for context
    old_tx = pending['tx_data']
    old_amount = old_tx.get('amount', 0)
    old_desc = old_tx.get('description', '')
    old_category = old_tx.get('category_slug', '')
    # old_type = old_tx.get('type', 'expense')
    
    # Process edit with AI
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        from .ai import AIAgent
        agent = AIAgent(api)
        
        # Give AI context about what's being edited
        # context_prompt = (
        #     f"Было: {old_amount} {old_tx.get('currency', 'uzs')} {old_desc} ({old_category or 'no category'}). "
        #     f"Обновить на: {text}"
        # )
        
        # NOTE: This prompt to AI can remain in Russian/English mix as AI understands it, 
        # or we could localize it. For now, keeping it basic.
        context_prompt = (
            f"Context: Was {old_amount} {old_tx.get('currency', 'uzs')} {old_desc} ({old_category or 'no category'}). "
            f"User update: {text}"
        )
        
        result = await agent.process_message(user_id, context_prompt)
        
        # Extract new transaction data
        response = result.get("response", "")
        parsed_transactions = result.get("parsed_transactions", [])
        
        if parsed_transactions:
            # Update pending transaction with new data
            new_data = parsed_transactions[0]
            tx_data = pending['tx_data']
            
            # Merge changes (keep old values if not provided)
            if 'amount' in new_data:
                tx_data['amount'] = new_data['amount']
            if 'description' in new_data:
                tx_data['description'] = new_data['description']
            if 'category_slug' in new_data:
                tx_data['category_slug'] = new_data['category_slug']
            if 'type' in new_data:
                tx_data['type'] = new_data['type']
            
            # Update pending storage
            pending['tx_data'] = tx_data
            pending_storage.update(tx_id, pending)
            
            # Show updated confirmation
            await show_transaction_confirmation(update, user_id, tx_data)
        else:
            await update.message.reply_text(
                # f"{response}\n\nПопробуй ещё раз или отмени /start",
                f"{response}",
                reply_markup=get_main_keyboard(lang)
            )
    except Exception as e:
        logger.exception(f"Edit error: {e}")
        await update.message.reply_text(
            # "❌ Ошибка редактирования. Попробуй заново.",
            t('common.common.error', lang),
            reply_markup=get_main_keyboard(lang)
        )


# Export handler
transaction_callback_handler = CallbackQueryHandler(
    handle_transaction_callback,
    pattern="^(confirm|cancel|edit)_"
)

