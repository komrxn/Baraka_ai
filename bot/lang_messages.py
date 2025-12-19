"""Multilingual messages for bot."""

MESSAGES = {
    'uz': {
        'auth_required': "⛔ Avval ro'yxatdan o'ting: /start",
        'balance_month': "💰 **Oylik balans**\n\n",
        'income': "📈 Daromad",
        'expense': "📉 Xarajat",
        'total': "💵 Jami",
        'stats_month': "📊 **Oylik statistika**\n\n",
        'balance': "💰 Balans",
        'by_categories': "**Kategoriyalar bo'yicha:**\n",
        'stats_error': "❌ Statistikani olishda xatolik",
        'expense_recorded': "расход записан!",  # Confirmation uses language from old message
        'income_recorded': "daromad записан!",
    },
    'ru': {
        'auth_required': "⛔ Сначала авторизуйся: /start",
        'balance_month': "💰 **Баланс за месяц**\n\n",
        'income': "📈 Доход",
        'expense': "📉 Расход", 
        'total': "💵 Итого",
        'stats_month': "📊 **Статистика за месяц**\n\n",
        'balance': "💰 Баланс",
        'by_categories': "**По категориям:**\n",
        'stats_error': "❌ Ошибка получения статистики",
        'expense_recorded': "расход записан!",
        'income_recorded': "доход записан!",
    },
    'en': {
        'auth_required': "⛔ Please authenticate first: /start",
        'balance_month': "💰 **Monthly Balance**\n\n",
        'income': "📈 Income",
        'expense': "📉 Expense",
        'total': "💵 Total",
        'stats_month': "📊 **Monthly Statistics**\n\n",
        'balance': "💰 Balance",
        'by_categories': "**By categories:**\n",
        'stats_error': "❌ Error fetching statistics",
        'expense_recorded': "expense recorded!",
        'income_recorded': "income recorded!",
    }
}


def get_message(user_lang: str, key: str, **kwargs) -> str:
    """Get localized message by key."""
    lang = user_lang if user_lang in MESSAGES else 'uz'
    msg = MESSAGES[lang].get(key, MESSAGES['uz'].get(key, key))
    
    # Format with kwargs if provided
    if kwargs:
        try:
            return msg.format(**kwargs)
        except:
            return msg
    return msg
