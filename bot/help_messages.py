"""Multilingual help messages for the bot."""

HELP_MESSAGES = {
    "ru": """
🤖 **Midas AI - Твой умный финансовый помощник**

📱 **Как пользоваться:**

**В БОТЕ:**
💬 Просто напиши что потратил или заработал:
   • "потратил 50к на еду"
   • "получил зарплату 5 млн"
   • "такси 30 тысяч"

🎤 Или отправь голосовое сообщение!

📊 Спрашивай баланс:
   • "сколько я потратил?"
   • "мой баланс"
   • "покажи статистику"

**В ВЕБ-ПРИЛОЖЕНИИ:**
🌐 Нажми кнопку "📊 Открыть Midas" → откроется приложение
   
📈 Там можно:
   • Смотреть графики расходов
   • Управлять категориями
   • Просматривать историю транзакций
   • Устанавливать лимиты

💡 **Команды:**
/start - Главное меню
/help - Эта справка
/balance - Баланс за месяц

🎯 Просто общайся со мной как с другом!
""",
    
    "en": """
🤖 **Midas AI - Your Smart Finance Assistant**

📱 **How to use:**

**IN THE BOT:**
💬 Just write what you spent or earned:
   • "spent 50k on food"
   • "got salary 5M"
   • "taxi 30 thousand"

🎤 Or send a voice message!

📊 Ask about balance:
   • "how much did I spend?"
   • "my balance"
   • "show statistics"

**IN THE WEB APP:**
🌐 Click "📊 Open Midas" button → app opens
   
📈 You can:
   • View expense charts
   • Manage categories
   • Browse transaction history
   • Set spending limits

💡 **Commands:**
/start - Main menu
/help - This help
/balance - Monthly balance

🎯 Just chat with me like a friend!
""",
    
    "uz": """
🤖 **Midas AI - Sizning aqlli moliyaviy yordamchingiz**

📱 **Qanday foydalanish:**

**BOTDA:**
💬 Shunchaki xarajat yoki daromadingizni yozing:
   • "ovqatga 50k sarfladim"
   • "5M oylik oldim"
   • "taksi 30 ming"

🎤 Yoki ovozli xabar yuboring!

📊 Balans haqida so'rang:
   • "qancha sarfladim?"
   • "mening balansi"
   • "statistikani ko'rsat"

**VEB ILOVADA:**
🌐 "📊 Midas ochish" tugmasini bosing → ilova ochiladi
   
📈 Mumkin:
   • Xarajatlar grafiklarini ko'rish
   • Toifalarni boshqarish
   • Tranzaksiyalar tarixini ko'rish
   • Limitlar o'rnatish

💡 **Buyruqlar:**
/start - Asosiy menyu
/help - Bu yordam
/balance - Oylik balans

🎯 Men bilan do'st kabi suhbatlashing!
"""
}


def get_help_message(language: str = "ru") -> str:
    """Get help message in specified language."""
    return HELP_MESSAGES.get(language, HELP_MESSAGES["ru"])
