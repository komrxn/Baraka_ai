"""Debt action handlers - Edit, Delete, and Settle functionality."""
import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from typing import Dict, Any
from datetime import datetime

from .api_client import BarakaAPIClient
from .config import config
from .user_storage import storage
from .i18n import t
from .handlers.common import send_typing_action

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
    created_at_iso = debt_data.get('created_at')
    if created_at_iso:
        try:
            date_obj = datetime.fromisoformat(created_at_iso.replace('Z', '+00:00'))
            # date_str = date_obj.strftime("%d.%m.%Y")
        except:
            pass
            # date_str = datetime.now().strftime("%d.%m.%Y")
    
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
    
    # First row: Settle
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
    action = parts[0]
    debt_id = '_'.join(parts[2:])
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    token = storage.get_user_token(user_id)
    
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)

    if action == "settle":
        try:
            result = await api.mark_debt_as_paid(debt_id)
            person = result.get('person_name')
            amount = float(result.get('amount', 0))
            currency = result.get('currency', 'UZS').upper()
            debt_type = result.get('type', 'owe_me')
            
            await query.edit_message_text(
                f"{t('debts.actions.settled_success', lang)}\n\n"
                f"{t('debts.person', lang)}: {person}\n"
                f"{t('debts.amount', lang)}: {amount:,.0f} {currency}"
            )
            
            # Ask: "Add to main account?"
            amount_str = f"{amount:,.0f}".replace(",", " ")
            prompt = t('debts.add_to_account.prompt_both', lang,
                      amount=amount_str, currency=currency)
            
            cb_data_yes = f"debt_to_tx_yes_{debt_type}_{amount}_{currency}_settled"
            cb_data_no = f"debt_to_tx_no_{debt_id}"
            
            keyboard = [[
                InlineKeyboardButton(t('debts.add_to_account.yes', lang), callback_data=cb_data_yes),
                InlineKeyboardButton(t('debts.add_to_account.no', lang), callback_data=cb_data_no)
            ]]
            
            await query.message.reply_text(
                prompt,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
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


@send_typing_action
async def handle_edit_debt_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle message when user is editing a debt."""
    debt_id = context.user_data.pop('editing_debt_id', None)
    if not debt_id:
        return False
    
    user_id = update.effective_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    text = update.message.text
    
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    try:
        # Fetch current debt
        current_debt = await api.get_debt(debt_id)
        
        # Prepare data for AI
        old_data = {
            "amount": float(current_debt.get('amount', 0)),
            "person_name": current_debt.get('person_name', ''),
            "description": current_debt.get('description', ''),
            "type": current_debt.get('type', 'owe_me'),
            "currency": current_debt.get('currency', 'uzs')
        }
        
        from .ai_agent import AIAgent
        agent = AIAgent(api)
        
        updates = await agent.edit_debt(old_data, text)
        
        if not updates:
             await update.message.reply_text(t('common.common.error', lang))
             return True

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
        
    except Exception as e:
        logger.exception(f"Edit debt error: {e}")
        from .handlers.common import get_main_keyboard
        await update.message.reply_text(
            f"{t('common.common.error', lang)}: {str(e)}",
            reply_markup=get_main_keyboard(lang)
        )
        return True

async def handle_debt_to_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Add to main account?' yes/no after debt creation."""
    from .transaction_actions import get_transaction_message_data
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = storage.get_user_language(user_id) or 'uz'
    
    data = query.data  # e.g. "debt_to_tx_yes_owe_me_200000.0_UZS_open" or "debt_to_tx_no_{debt_id}"
    
    if data.startswith("debt_to_tx_no_"):
        # User declined — just edit the message
        await query.edit_message_text(t('debts.add_to_account.not_added', lang))
        return
    
    if data.startswith("debt_to_tx_yes_"):
        # Parse: debt_to_tx_yes_{type}_{amount}_{currency}_{status}
        parts = data.replace("debt_to_tx_yes_", "").split("_")
        
        try:
            # Handle compound type names
            if parts[0] == "owe" and parts[1] == "me":
                debt_type = "owe_me"
                amount = float(parts[2])
                currency = parts[3].lower()
                status = parts[4] if len(parts) > 4 else "open"
            elif parts[0] == "i" and parts[1] == "owe":
                debt_type = "i_owe"
                amount = float(parts[2])
                currency = parts[3].lower()
                status = parts[4] if len(parts) > 4 else "open"
            else:
                logger.error(f"Cannot parse debt_to_tx callback: {data}")
                await query.edit_message_text(t('common.common.error', lang))
                return
            
            token = storage.get_user_token(user_id)
            api = BarakaAPIClient(config.API_BASE_URL)
            api.set_token(token)
            
            # Resolve "debt" category
            categories = await api.get_categories()
            debt_category_id = None
            debt_category_slug = "debt"
            for cat in categories:
                if cat.get("slug") == "debt":
                    debt_category_id = cat.get("id")
                    break
            
            # Fallback to other_expense if no debt category
            if not debt_category_id:
                debt_category_slug = "other_expense"
                for cat in categories:
                    if cat.get("slug") == "other_expense":
                        debt_category_id = cat.get("id")
                        break
            
            # Remove the prompt message
            await query.edit_message_text(t('debts.add_to_account.added', lang))
            
            created_txs = []
            
            if status == "settled":
                # Flow 2: create two transactions (+income, -expense)
                for tx_type in ["income", "expense"]:
                    tx = {
                        "type": tx_type,
                        "amount": amount,
                        "description": t('debts.add_to_account.added', lang),
                        "currency": currency,
                    }
                    if debt_category_id:
                        tx["category_id"] = debt_category_id
                    result = await api.create_transaction(tx)
                    created_txs.append({
                        "transaction_id": result.get("id"),
                        "type": tx_type,
                        "amount": amount,
                        "currency": currency,
                        "category": debt_category_slug,
                        "description": t('debts.add_to_account.added', lang),
                    })
            else:
                # Flow 1: single transaction
                tx_type = "expense" if debt_type == "owe_me" else "income"
                tx = {
                    "type": tx_type,
                    "amount": amount,
                    "description": t('debts.add_to_account.added', lang),
                    "currency": currency,
                }
                if debt_category_id:
                    tx["category_id"] = debt_category_id
                result = await api.create_transaction(tx)
                created_txs.append({
                    "transaction_id": result.get("id"),
                    "type": tx_type,
                    "amount": amount,
                    "currency": currency,
                    "category": debt_category_slug,
                    "description": t('debts.add_to_account.added', lang),
                })
            
            # Show standard transaction cards with Edit/Delete buttons
            for tx_data in created_txs:
                text, reply_markup = await get_transaction_message_data(user_id, tx_data)
                await query.message.reply_text(
                    text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.exception(f"Error creating debt-to-transaction: {e}")
            await query.edit_message_text(f"{t('common.common.error', lang)}: {str(e)}")


# Export handler
debt_action_handler = CallbackQueryHandler(
    handle_debt_action,
    pattern="^(settle|edit|delete)_debt_"
)

debt_to_tx_handler = CallbackQueryHandler(
    handle_debt_to_transaction_callback,
    pattern="^debt_to_tx_"
)
