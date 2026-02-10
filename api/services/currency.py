"""Currency exchange rates service using CBU (Central Bank of Uzbekistan) API."""
import httpx
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

CBU_API_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

# Popular currencies to show by default
DEFAULT_CURRENCIES = ["USD", "EUR", "RUB", "CNY", "KZT"]

# Currency flags for display
CURRENCY_FLAGS = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "RUB": "🇷🇺",
    "GBP": "🇬🇧",
    "JPY": "🇯🇵",
    "CNY": "🇨🇳",
    "KZT": "🇰🇿",
    "KGS": "🇰🇬",
    "TJS": "🇹🇯",
    "TMT": "🇹🇲",
    "AZN": "🇦🇿",
    "GEL": "🇬🇪",
    "AMD": "🇦🇲",
    "BYN": "🇧🇾",
    "UAH": "🇺🇦",
    "TRY": "🇹🇷",
    "AED": "🇦🇪",
    "SAR": "🇸🇦",
    "KRW": "🇰🇷",
    "INR": "🇮🇳",
    "PKR": "🇵🇰",
    "AFN": "🇦🇫",
    "CHF": "🇨🇭",
    "CAD": "🇨🇦",
    "AUD": "🇦🇺",
    "NZD": "🇳🇿",
    "SGD": "🇸🇬",
    "HKD": "🇭🇰",
    "MYR": "🇲🇾",
    "THB": "🇹🇭",
    "VND": "🇻🇳",
    "IDR": "🇮🇩",
    "PHP": "🇵🇭",
    "PLN": "🇵🇱",
    "CZK": "🇨🇿",
    "HUF": "🇭🇺",
    "SEK": "🇸🇪",
    "NOK": "🇳🇴",
    "DKK": "🇩🇰",
    "ILS": "🇮🇱",
    "EGP": "🇪🇬",
    "ZAR": "🇿🇦",
    "BRL": "🇧🇷",
    "MXN": "🇲🇽",
    "ARS": "🇦🇷",
}


class CurrencyRate:
    """Currency rate data."""
    def __init__(self, data: dict):
        self.code = data.get("Ccy", "")
        self.nominal = int(data.get("Nominal", "1"))
        self.rate = float(data.get("Rate", "0"))
        self.diff = float(data.get("Diff", "0"))
        self.date = data.get("Date", "")
        
        # Localized names
        self.name_ru = data.get("CcyNm_RU", self.code)
        self.name_uz = data.get("CcyNm_UZ", self.code)
        self.name_en = data.get("CcyNm_EN", self.code)
        
    @property
    def flag(self) -> str:
        return CURRENCY_FLAGS.get(self.code, "💱")
    
    def get_name(self, lang: str = "ru") -> str:
        if lang == "uz":
            return self.name_uz
        elif lang == "en":
            return self.name_en
        return self.name_ru
    
    def format_rate(self) -> str:
        """Format rate with thousand separators."""
        if self.rate >= 1000:
            return f"{self.rate:,.2f}".replace(",", " ")
        return f"{self.rate:.2f}"
    
    def format_diff(self) -> str:
        """Format diff with arrow indicator."""
        if self.diff > 0:
            return f"▲{self.diff}"
        elif self.diff < 0:
            return f"▼{abs(self.diff)}"
        return "—"


async def fetch_cbu_rates() -> List[CurrencyRate]:
    """
    Fetch current exchange rates from CBU API.
    
    Returns:
        List of CurrencyRate objects
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(CBU_API_URL)
            response.raise_for_status()
            data = response.json()
            
            rates = [CurrencyRate(item) for item in data]
            logger.info(f"Fetched {len(rates)} currency rates from CBU")
            return rates
            
    except Exception as e:
        logger.error(f"Failed to fetch CBU rates: {e}")
        raise


async def get_rate_for_currency(currency_code: str) -> Optional[CurrencyRate]:
    """
    Get rate for a specific currency.
    
    Args:
        currency_code: ISO 4217 currency code (e.g., "USD", "EUR")
        
    Returns:
        CurrencyRate object or None if not found
    """
    try:
        rates = await fetch_cbu_rates()
        currency_code = currency_code.upper()
        
        for rate in rates:
            if rate.code == currency_code:
                return rate
                
        return None
        
    except Exception as e:
        logger.error(f"Failed to get rate for {currency_code}: {e}")
        return None


async def convert_to_uzs(amount: float, from_currency: str) -> Optional[float]:
    """
    Convert amount from foreign currency to UZS.
    
    Args:
        amount: Amount in foreign currency
        from_currency: Source currency code
        
    Returns:
        Amount in UZS or None if conversion failed
    """
    if from_currency.upper() == "UZS":
        return amount
        
    rate = await get_rate_for_currency(from_currency)
    if not rate:
        return None
    
    # CBU rates are already per 1 unit (or per Nominal units)
    # Rate is how many UZS for 1 (or Nominal) unit of currency
    uzs_amount = amount * (rate.rate / rate.nominal)
    
    logger.info(f"Converted {amount} {from_currency} → {uzs_amount:.2f} UZS (rate: {rate.rate})")
    return uzs_amount


def format_rates_message(rates: List[CurrencyRate], date: str, lang: str = "ru") -> str:
    """
    Format currency rates for Telegram message.
    
    Args:
        rates: List of CurrencyRate to display
        date: Date string
        lang: Language code
        
    Returns:
        Formatted message string
    """
    titles = {
        "ru": "🏦 Курс валют ЦБ РУз",
        "uz": "🏦 O'zbekiston MB valyuta kurslari",
        "en": "🏦 CBU Exchange Rates"
    }
    
    title = titles.get(lang, titles["ru"])
    lines = [f"{title} — {date}\n"]
    
    for rate in rates:
        nominal_str = f"{rate.nominal} " if rate.nominal > 1 else "1 "
        line = f"{rate.flag} {nominal_str}{rate.code} = {rate.format_rate()} сум ({rate.format_diff()})"
        lines.append(line)
    
    return "\n".join(lines)
