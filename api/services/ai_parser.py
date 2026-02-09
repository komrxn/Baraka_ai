import io
import json
import logging
import re
from typing import Dict, Any, Optional
from decimal import Decimal

from openai import OpenAI
from PIL import Image

logger = logging.getLogger(__name__)


# Category slugs compatible with UI
CATEGORY_SLUGS = [
    "food",  # Питание
    "transport",  # Транспорт
    "entertainment",  # Развлечения
    "shopping",  # Покупки
    "services",  # Услуги
    "health",  # Здоровье
    "education",  # Образование
    "housing",  # Жильё
    "bills",  # Счета
    "salary",  # Зарплата (income)
    "other",  # Прочее
]

# Russian keyword mapping to category slugs
CATEGORY_KEYWORDS = {
    # food / Питание
    "продукт": "food",
    "супермаркет": "food",
    "магазин": "food",
    "еда": "food",
    "кофе": "food",
    "кафе": "food",
    "ресторан": "food",
    "столовая": "food",
    "доставка": "food",
    "фастфуд": "food",
    "пицц": "food",
    "суши": "food",
    "бургер": "food",
    "макдональдс": "food",
    "kfc": "food",
    
    # transport / Транспорт
    "такси": "transport",
    "метро": "transport",
    "автобус": "transport",
    "трамвай": "transport",
    "маршрут": "transport",
    "каршеринг": "transport",
    "парков": "transport",
    "бензин": "transport",
    "заправ": "transport",
    "яндекс.такси": "transport",
    "убер": "transport",
    
    # entertainment / Развлечения
    "кино": "entertainment",
    "развлеч": "entertainment",
    "игр": "entertainment",
    "подпис": "entertainment",
    "spotify": "entertainment",
    "netflix": "entertainment",
    "концерт": "entertainment",
    
    # shopping / Покупки
    "покупк": "shopping",
    "одежд": "shopping",
    "обув": "shopping",
    "маркетплейс": "shopping",
    "бытов": "shopping",
    "техник": "shopping",
    "электро": "shopping",
    "гаджет": "shopping",
    
    # services / Услуги
    "услуг": "services",
    "барбер": "services",
    "парикмахер": "services",
    "салон": "services",
    "мастер": "services",
    
    # health / Здоровье
    "здоров": "health",
    "клиник": "health",
    "врач": "health",
    "стомат": "health",
    "анализ": "health",
    "апт": "health",
    "лекарств": "health",
    
    # education / Образование
    "курс": "education",
    "обуч": "education",
    "учеб": "education",
    "книг": "education",
    "школ": "education",
    
    # housing / Жильё
    "аренда": "housing",
    "квартир": "housing",
    "ипотек": "housing",
    "ремонт": "housing",
    "мебел": "housing",
    
    # bills / Счета
    "коммунал": "bills",
    "жкх": "bills",
    "интернет": "bills",
    "связь": "bills",
    "мобил": "bills",
    "телефон": "bills",
    "электр": "bills",
    
    # salary / Зарплата (income)
    "зарплат": "salary",
    "зп": "salary",
    "аванс": "salary",
    "премия": "salary",
}


class AITransactionParser:
    """AI-powered transaction parser using OpenAI."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def check_limits(self, user, limit_type: str) -> bool:
        """
        Check if user has reached their limits.
        limit_type: 'request' (3-day), 'voice' (daily), 'image' (daily)
        """
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # 1. Reset Daily Counters
        if not user.last_daily_reset or user.last_daily_reset.date() < now.date():
            user.voice_usage_daily = 0
            user.image_usage_daily = 0
            user.last_daily_reset = now
            
        # 2. Reset/Check 3-Day Window (Recoil)
        # "Recoil" logic: simple reset every 3 days from first request of window
        if not user.last_3day_reset or (now - user.last_3day_reset.replace(tzinfo=None)) > timedelta(days=3):
            user.request_count_3day = 0
            user.last_3day_reset = now

        # 3. Define Limits based on Tier
        tier = user.subscription_tier
        
        # Limits: (3-day requests, daily voice, daily image)
        LIMITS = {
            "free":    (180, 5, 0),    # Free
            "plus":    (250, 20, 20),  # Plus
            "pro":     (400, 30, 50),  # Pro
            "premium": (1000, 100, 150) # Premium ("Infinite" -> high number)
        }
        
        limits = LIMITS.get(tier, LIMITS["free"])
        req_limit, voice_limit, img_limit = limits

        # 4. Check
        if limit_type == 'request':
            if user.request_count_3day >= req_limit:
                 return False
        elif limit_type == 'voice':
            if user.voice_usage_daily >= voice_limit:
                 return False
        elif limit_type == 'image':
            if user.image_usage_daily >= img_limit:
                 return False
                 
        return True

    async def update_usage(self, user, usage_type: str, db):
        """Increment usage counters."""
        if usage_type == 'voice':
            user.voice_usage_daily += 1
        elif usage_type == 'image':
            user.image_usage_daily += 1
        
        # Always increment general request count (recoil) for any AI action? 
        # Requirement said "Limits: 180 requests in 3 days". 
        # Usually voice/image also count as requests.
        user.request_count_3day += 1
        await db.commit()

    def get_model_for_tier(self, tier: str) -> str:
        """Select AI model based on subscription tier."""
        if tier == "free":
            return "gpt-5-nano"
        elif tier in ("plus", "pro"):
            # User requested 5.1 for Pro in latest message?
            # Re-read: "Premium - 5.1". "Pro - 5-mini" (original). 
            # LATEST REQUEST: "хотя в pro gpt-5.1 поставь лучше."
            # So: Pro = 5.1, Premium = 5.1
            if tier == "pro":
                return "gpt-5.1" 
            return "gpt-5-mini"
        elif tier == "premium":
            return "gpt-5.1"
        return "gpt-5-nano"
    
    async def parse_text(self, text: str, model_name: str = "gpt-5-nano") -> Dict[str, Any]:
        """
        Parse transaction from text message.
        """
        logger.info(f"AI parsing text: {text[:100]}... (Model: {model_name})")
        
        system_prompt = (
            "Ты умный финансовый ассистент. Задача: извлечь информацию о транзакции из сообщения пользователя.\n"
            "Верни ТОЛЬКО JSON с ключами:\n"
            "- amount (number): сумма транзакции\n"
            "- currency (string): валюта ISO код (uzs, usd, eur, rub, gbp, cny, kzt, aed, try, etc.)\n"
            "- description (string): краткое описание\n"
            "- type (string): 'income' или 'expense'\n"
            "- category_slug (string|null): категория из списка\n"
            "- confidence (number 0-1): уверенность в категории\n\n"
            f"Доступные категории: {', '.join(CATEGORY_SLUGS)}\n\n"
            "КРИТИЧЕСКИ ВАЖНО - Сокращения сумм:\n"
            "- '30к', '30к', '30 тыщ', '30 штук', '30 косарей' = 30000\n"
            "- '5к' = 5000, '100к' = 100000, '1кк' = 1000000\n"
            "- 'тыщ', 'тыща', 'тысяч' = умножить на 1000\n"
            "- 'млн', 'лям' = умножить на 1000000\n\n"
            "ВАЛЮТЫ (распознавай гибко!):\n"
            "- USD: доллар, $, dollar, dollar, бакс, зелёный\n"
            "- EUR: евро, €, euro\n"
            "- RUB: рубль, ₽, руб, ruble\n"
            "- GBP: фунт, £, pound\n"
            "- CNY: юань, ¥, yuan, жэньминьби\n"
            "- KZT: тенге, tenge\n"
            "- AED: дирхам, dirham\n"
            "- TRY: лира, lira\n"
            "- UZS: сум, сўм, so'm, sum (по умолчанию)\n\n"
            "Поддержка языков:\n"
            "- Русский: кофе, такси, зарплата, купил, потратил\n"
            "- Узбекский: 'qahva' (кофе), 'taksi', 'ish haqi' (зарплата), 'xarid' (покупка)\n"
            "- English: coffee, taxi, salary, bought\n\n"
            "Правила:\n"
            "- Если валюта не указана, используй 'uzs'\n"
            "- income: зарплата, аванс, премия, возврат, олды (получил), ish haqi\n"
            "- expense: все остальное (покупки, услуги, траты)\n"
            "- Описание должно быть кратким и понятным\n"
            "- Обязательно правильно распознавай СУММУ с учётом сокращений!\n\n"
            "Примеры:\n"
            "'Купил кофе 30к' → amount: 30000, currency: uzs\n"
            "'Потратил на такси 25 тыщ' → amount: 25000, currency: uzs\n"
            "'Qahvaga 20k' → amount: 20000, currency: uzs\n"
            "'Потратил 50 долларов на обед' → amount: 50, currency: usd\n"
            "'Зарплата $500' → amount: 500, currency: usd, type: income\n"
            "'Купил за 100 евро' → amount: 100, currency: eur"
        )

        
        try:
            completion = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Текст: {text}"},
                ],
                response_format={"type": "json_object"},
            )
            
            data = json.loads(completion.choices[0].message.content)
            
            # Validate and normalize
            result = {
                "type": data.get("type", "expense").lower(),
                "amount": Decimal(str(data.get("amount", 0))),
                "currency": (data.get("currency") or "uzs").lower(),
                "description": (data.get("description") or text).strip()[:500],
                "category_slug": data.get("category_slug"),
                "confidence": min(1.0, max(0.0, float(data.get("confidence", 0)))),
            }
            
            # Validate type
            if result["type"] not in ("income", "expense"):
                result["type"] = "expense"
            
            # Validate category
            if result["category_slug"] and result["category_slug"] not in CATEGORY_SLUGS:
                result["category_slug"] = None
                result["confidence"] = 0.0
            
            # Fallback to keyword matching if AI confidence is low
            if not result["category_slug"] or result["confidence"] < 0.5:
                keyword_cat, keyword_conf = self._guess_category_by_keywords(text)
                if keyword_conf > result["confidence"]:
                    result["category_slug"] = keyword_cat
                    result["confidence"] = keyword_conf
            
            logger.info(
                f"Parsed: type={result['type']}, amount={result['amount']} {result['currency']}, "
                f"category={result['category_slug']}, confidence={result['confidence']:.2f}"
            )
            
            return result
            
        except Exception as e:
            logger.exception("AI parsing failed, using fallback")
            return self._fallback_parse(text)
    
    def transcribe_voice(self, audio_data: bytes, filename: str = "audio.ogg") -> str:
        """
        Transcribe voice message using Whisper API.
        
        Args:
            audio_data: Audio file bytes
            filename: Filename with extension
        
        Returns:
            Transcribed text
        """
        logger.info(f"Transcribing voice: {filename}")
        
        try:
            fileobj = io.BytesIO(audio_data)
            fileobj.name = filename
            
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, fileobj),
                response_format="text",
            )
            
            logger.info(f"Transcription: {transcript[:100]}...")
            return transcript
            
        except Exception as e:
            logger.exception("Voice transcription failed")
            raise
    
    def parse_receipt_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Parse receipt from image using GPT Vision.
        
        Args:
            image_data: Image file bytes
        
        Returns:
            Same format as parse_text()
        """
        logger.info("Parsing receipt image with GPT Vision")
        
        try:
            # Encode image to base64
            import base64
            b64_image = base64.b64encode(image_data).decode('utf-8')
            
            system_prompt = (
                "Ты умный финансовый ассистент. Извлекаешь данные из чеков/квитанций.\\n"
                "Верни JSON с ключами: amount, currency, description, type, category_slug, confidence\\n\\n"
                f"Доступные категории: {', '.join(CATEGORY_SLUGS)}\\n\\n"
                "ПРАВИЛА:\\n"
                "- amount: сумма (число)\\n"
                "- currency: uzs, usd, eur, rub\\n"
                "- description: что куплено/оплачено\\n"
                "- type: 'expense' (почти всегда расход)\\n"
                "- category_slug: выбери из списка выше\\n"
                "- confidence: 0-1 (насколько уверен)\\n\\n"
                "КАТЕГОРИИ:\\n"
                "- Beeline, Click, телефон, связь, интернет → bills\\n"
                "- Кафе, ресторан, еда → food\\n"
                "- Такси, транспорт → transport\\n"
                "- Одежда, техника → shopping\\n"
                "- Если неясно → other"
            )
            
            completion = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Извлеки сумму, описание и категорию из этого чека/квитанции"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
            )
            
            data = json.loads(completion.choices[0].message.content)
            
            result = {
                "type": "expense",  # Receipts are usually expenses
                "amount": Decimal(str(data.get("amount", 0))),
                "currency": (data.get("currency") or "uzs").lower(),
                "description": (data.get("description") or "Receipt").strip()[:500],
                "category_slug": data.get("category_slug"),
                "confidence": min(1.0, max(0.0, float(data.get("confidence", 0.7)))),
            }
            
            logger.info(f"Receipt parsed: {result}")
            return result
            
        except Exception as e:
            logger.exception("Receipt parsing failed")
            raise
    
    def _guess_category_by_keywords(self, text: str) -> tuple[Optional[str], float]:
        """Fallback keyword-based categorization."""
        text_lower = text.lower()
        best_slug = None
        best_score = 0.0
        
        for keyword, slug in CATEGORY_KEYWORDS.items():
            if keyword in text_lower:
                # Longer keywords = higher confidence
                score = min(1.0, 0.5 + 0.05 * len(keyword))
                if score > best_score:
                    best_score = score
                    best_slug = slug
        
        return best_slug, best_score
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parser using regex when AI fails."""
        # Try to extract amount
        amount_match = re.search(r"(\d[\d\s,.]+)", text.replace(" ", ""))
        amount = Decimal(amount_match.group(1).replace(",", ".")) if amount_match else Decimal("0")
        
        # Try to detect currency
        currency = "uzs"
        if re.search(r"\b(usd|dollar|доллар)", text, re.I):
            currency = "usd"
        elif re.search(r"\b(eur|euro|евро)", text, re.I):
            currency = "eur"
        elif re.search(r"\b(rub|рубл)", text, re.I):
            currency = "rub"
        
        # Guess category by keywords
        category_slug, confidence = self._guess_category_by_keywords(text)
        
        # Detect income vs expense
        tx_type = "expense"
        income_keywords = ["зарплат", "аванс", "премия", "возврат", "перевод", "получ", "зачисл"]
        if any(kw in text.lower() for kw in income_keywords):
            tx_type = "income"
            if not category_slug:
                category_slug = "salary"
                confidence = 0.6
        
        return {
            "type": tx_type,
            "amount": amount,
            "currency": currency,
            "description": text.strip()[:500],
            "category_slug": category_slug,
            "confidence": confidence,
        }
