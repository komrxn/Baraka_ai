"""Message handler module."""
import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from ..ai_agent import AIAgent
from ..api_client import BarakaAPIClient
from ..config import config
from ..user_storage import storage
from ..transaction_actions import show_transaction_with_actions, handle_edit_transaction_message
from .common import with_auth_check, get_main_keyboard, send_typing_action, get_keyboard_for_user
from ..i18n import t, translate_category


from ..debt_actions import show_debt_with_actions, handle_edit_debt_message
from ..utils.subscription import check_subscription

logger = logging.getLogger(__name__)


@send_typing_action
@check_subscription
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with AI."""
    user_id = update.effective_user.id
    text = update.message.text
    lang = storage.get_user_language(user_id) or 'uz'
    
    if not storage.is_user_authorized(user_id):
        await update.message.reply_text(t('auth.common.auth_required', lang))
        return
    
    # CHECK FOR MENU BUTTONS FIRST (Interrupt editing)
    # If user presses a menu button, we should cancel any active editing session
    # and process the menu command.
    
    button_balance = t('common.buttons.balance', lang)
    button_stats = t('common.buttons.statistics', lang)
    button_help = t('common.buttons.instructions', lang)
    button_support = t('common.buttons.support', lang)
    button_currency = ["💱 Курс валют", "💱 Valyuta kursi", "💱 Exchange Rates"]
    button_profile = "Baraka AI PLUS 🌟"
    
    is_menu_command = (
        text in [button_balance, button_stats, button_help, button_support, button_profile] or
        text in button_currency
    )

    if is_menu_command:
        # Clear editing states if present
        if context.user_data.get('editing_tx') or context.user_data.get('editing_transaction_id'):
             # Try to restore the message if we have the ID and transaction ID
             edit_msg_id = context.user_data.get('editing_message_id')
             edit_tx_id = context.user_data.get('editing_transaction_id')
             
             if edit_msg_id and edit_tx_id:
                 from ..transaction_actions import restore_transaction_message
                 try:
                     await restore_transaction_message(context, update.effective_chat.id, edit_msg_id, user_id, edit_tx_id)
                 except Exception as e:
                     logger.warning(f"Failed to restore message on interrupt: {e}")

             context.user_data.pop('editing_tx', None)
             context.user_data.pop('editing_transaction_id', None)
             context.user_data.pop('editing_field', None)
             context.user_data.pop('editing_message_id', None)
        
        if context.user_data.get('editing_debt_id'):
             context.user_data.pop('editing_debt_id', None)
             
        # Process the menu command
        await process_text_message(update, context, text, user_id)
        return

    # Then check editing states
    if context.user_data.get('editing_tx'):
        from ..confirmation_handlers import handle_edit_message
        await handle_edit_message(update, context)
        return

    if context.user_data.get('editing_debt_id'):
        await handle_edit_debt_message(update, context)
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
        api = BarakaAPIClient(config.API_BASE_URL)
        api.set_token(token)
        await show_balance(update, api, lang)
        return
    elif text == button_stats:
        token = storage.get_user_token(user_id)
        api = BarakaAPIClient(config.API_BASE_URL)
        api.set_token(token)
        await show_statistics(update, api, lang)
        return
    elif text == button_help:
        from .commands import help_command
        await help_command(update, context)
        return
    elif text in ("💱 Курс валют", "💱 Valyuta kursi", "💱 Exchange Rates"):
        from .currency import currency_rates_handler
        await currency_rates_handler(update, context)
        return
    elif text == "Baraka AI PLUS 🌟":
        from .commands import profile
        await profile(update, context)
        return
    elif text == t('common.buttons.support', lang):
        support_msg = {
            'uz': "🛠 **Texnik yordam**\n\nSavollaringiz bo'lsa, adminga yozing: @bezavtra",
            'ru': "🛠 **Тех. поддержка**\n\nЕсли у вас есть вопросы, напишите админу: @bezavtra",
            'en': "🛠 **Tech Support**\n\nIf you have questions, contact admin: @bezavtra"
        }
        await update.message.reply_text(support_msg.get(lang, support_msg['uz']), parse_mode='Markdown')
        return

    
    # Check if editing transaction
    is_editing = await handle_edit_transaction_message(update, context, text_override=text)
    if is_editing:
        return
    
    # Get token and API client
    token = storage.get_user_token(user_id)
    api = BarakaAPIClient(config.API_BASE_URL)
    api.set_token(token)
    
    # Increment text usage
    try:
        await api.increment_usage("text")
    except Exception as e:
        logger.error(f"Failed to increment usage: {e}")
    
    # Process with AI
    agent = AIAgent(api)
    result = await agent.process_message(user_id, text)
    
    response_text = result.get("response", "")
    created_transactions = result.get("created_transactions", [])
    created_debts = result.get("created_debts", [])
    settled_debts = result.get("settled_debts", [])
    premium_upsells = result.get("premium_upsells", [])
    
    # Handle premium feature upsells first
    if premium_upsells:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        for upsell in premium_upsells:
            feature = upsell.get("feature", "")
            original_amount = upsell.get("original_amount")
            original_currency = upsell.get("original_currency")
            
            if feature == "multi_currency":
                # Use localization with placeholders
                upsell_text = t("currency.multi_currency_upsell", lang, amount=original_amount, currency=original_currency)
                
                keyboard = [[InlineKeyboardButton(t("subscription.buy_subscription_btn", lang), callback_data="buy_subscription")]]
                await update.message.reply_text(
                    upsell_text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        return  # Don't show other responses if upsell was shown

    
    # Show AI response (only if no transactions/debts created or settled)
    if not created_transactions and not created_debts and not settled_debts and response_text:
        keyboard = await get_keyboard_for_user(user_id, lang)
        try:
            await update.message.reply_text(
                response_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
        except Exception:
            await update.message.reply_text(
                response_text,
                reply_markup=keyboard
            )
            
    # Show each created transaction with Edit/Delete buttons
    if created_transactions:
        for tx_data in created_transactions:
            await show_transaction_with_actions(update, user_id, tx_data)

    # Show created debts with actions
    if created_debts:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        for debt in created_debts:
            await show_debt_with_actions(update, user_id, debt)
            
            # Send follow-up: "Add to main account?"
            debt_id = debt.get('debt_id') or debt.get('id')
            debt_type = debt.get('type', 'owe_me')
            amount = float(debt.get('amount', 0))
            currency_code = debt.get('currency', 'uzs').upper()
            person = debt.get('person') or debt.get('person_name', '')
            description = debt.get('description', '')
            amount_str = f"{amount:,.0f}".replace(",", " ")
            
            # New debt: owe_me → expense, i_owe → income
            if debt_type == 'owe_me':
                prompt = t('debts.add_to_account.prompt_expense', lang,
                          amount=amount_str, currency=currency_code)
            else:
                prompt = t('debts.add_to_account.prompt_income', lang,
                          amount=amount_str, currency=currency_code)
            
            # Store metadata for callback handler
            cb_key = f"new_{debt_id}"
            context.user_data[f"debt_to_tx_{cb_key}"] = {
                "type": debt_type,
                "amount": amount,
                "currency": currency_code,
                "person": person,
                "description": description,
                "is_settle": False,
            }
            
            cb_data_yes = f"debt_to_tx_yes_{cb_key}"
            cb_data_no = f"debt_to_tx_no_{debt_id}"
            
            keyboard = [[
                InlineKeyboardButton(t('debts.add_to_account.yes', lang), callback_data=cb_data_yes),
                InlineKeyboardButton(t('debts.add_to_account.no', lang), callback_data=cb_data_no)
            ]]
            
            await update.message.reply_text(
                prompt,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )

    # Show settled debts
    if settled_debts:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Collect IDs of debts created in this same turn (post-factum)
        created_debt_ids = set()
        if created_debts:
            for d in created_debts:
                did = d.get('debt_id') or d.get('id')
                if did:
                    created_debt_ids.add(str(did))
        
        for debt in settled_debts:
             # debt: {settled_debt_id, person, amount, type, currency}
            debt_id = debt.get('settled_debt_id')
            amount_val = float(debt.get('amount', 0))
            amount_str = f"{amount_val:,.0f}".replace(",", " ")
            currency = debt.get('currency', 'UZS').upper()
            debt_type = debt.get('type', 'owe_me')
            person = debt.get('person', '')

            text = f"{t('debts.debt_settled', lang)}\n\n"
            text += f"{t('debts.person', lang)}: {person}\n"
            text += f"{t('debts.amount', lang)}: {amount_str} {currency}\n"

            await update.message.reply_text(
                text,
                reply_markup=get_main_keyboard(lang)
            )
            
            # Skip prompt if this debt was also created in same turn
            # (already prompted via created_debts section above)
            if str(debt_id) in created_debt_ids:
                continue
            
            # Ask: "Add transaction?" — single reverse transaction
            if debt_type == "owe_me":
                prompt = t('debts.add_to_account.prompt_income', lang,
                          amount=amount_str, currency=currency)
            else:
                prompt = t('debts.add_to_account.prompt_expense', lang,
                          amount=amount_str, currency=currency)
            
            # Store metadata for callback handler
            cb_key = f"settle_{debt_id}"
            context.user_data[f"debt_to_tx_{cb_key}"] = {
                "type": debt_type,
                "amount": amount_val,
                "currency": currency,
                "person": person,
                "description": "",
                "is_settle": True,
            }
            
            cb_data_yes = f"debt_to_tx_yes_{cb_key}"
            cb_data_no = f"debt_to_tx_no_{debt_id}"
            
            keyboard = [[
                InlineKeyboardButton(t('debts.add_to_account.yes', lang), callback_data=cb_data_yes),
                InlineKeyboardButton(t('debts.add_to_account.no', lang), callback_data=cb_data_no)
            ]]
            
            await update.message.reply_text(
                prompt,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )



async def show_statistics(update: Update, api: BarakaAPIClient, lang: str):
    """Show user statistics."""
    from ..api_client import UnauthorizedError
    
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
                
                for cat in valid_cats[:10]:  # Top 10
                    category_name = cat.get('category_name', 'Unknown')
                    category_slug = cat.get('category_slug')
                    amount = float(cat.get('amount', 0))
                    
                    # Try to translate category
                    if category_slug:
                        from ..i18n import translate_category
                        category_display = translate_category(category_slug, lang)
                    else:
                        category_display = category_name
                    
                    stats_text += f"\n{category_display}: {amount:,.0f} ({cat.get('percentage', '0')}%)"
                
                currency = balance.get('currency', 'UZS')
                stats_text += f"\n\n{t('common.common.total', lang)}: {total_expense:,.0f} {currency}"
            else:
                stats_text += t('transactions.stats.no_data', lang)
        
        await update.message.reply_text(
            stats_text,
            reply_markup=get_main_keyboard(lang)
        )
    except UnauthorizedError:
        # Token expired or invalid - clear it and prompt re-auth
        user_id = update.effective_user.id
        storage.clear_user_token(user_id)
        await update.message.reply_text(
            t('auth.errors.auth_required', lang),
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.exception(f"Statistics error: {e}")
        await update.message.reply_text(
            t('transactions.stats.error', lang),
            reply_markup=get_main_keyboard(lang)
        )


async def show_balance(update: Update, api: BarakaAPIClient, lang: str):
    """Show user balance."""
    from ..api_client import UnauthorizedError
    
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
                balance_text += f"📝 {t('transactions.balance.recent', lang)}:\n"
                
                for tx in transactions:
                    # Parse transaction
                    tx_type = tx.get('type', 'expense')
                    amount = float(tx.get('amount', 0))
                    desc = tx.get('description', 'No description')
                    category_slug = tx.get('category', {}).get('slug') if isinstance(tx.get('category'), dict) else None
                    
                    # Try to translate category
                    if category_slug:
                        from ..i18n import translate_category
                        category_display = translate_category(category_slug, lang)
                    else:
                        category_display = desc
                    
                    # Format amount with sign
                    sign = "+" if tx_type == "income" else "-"
                    balance_text += f"\n{sign}{amount:,.0f} {currency} - {category_display}"
            else:
                balance_text += t('transactions.balance.no_recent', lang)
        except Exception as e:
            logger.warning(f"Failed to load recent transactions: {e}")
            balance_text += t('transactions.balance.no_recent', lang)
        
        await update.message.reply_text(
            balance_text,
            reply_markup=get_main_keyboard(lang)
        )
    except UnauthorizedError:
        # Token expired or invalid - clear it and prompt re-auth
        user_id = update.effective_user.id
        storage.clear_user_token(user_id)
        await update.message.reply_text(
            t('auth.errors.auth_required', lang),
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception as e:
        logger.exception(f"Balance error: {e}")
        await update.message.reply_text(
            t('transactions.balance.error', lang),
            reply_markup=get_main_keyboard(lang)
        )
