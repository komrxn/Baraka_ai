"""Currency rates API endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from ..database import get_db
from ..services.currency import fetch_cbu_rates, CURRENCY_FLAGS
from ..auth.jwt import get_current_user
from ..models.user import User

router = APIRouter(prefix="/currency", tags=["Currency"])


@router.get("/rates")
async def get_currency_rates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current exchange rates from CBU.
    
    Returns all available currencies with their rates relative to UZS.
    """
    rates = await fetch_cbu_rates()
    
    # Convert to dict format for API response
    rates_list = []
    for rate in rates:
        rates_list.append({
            "code": rate.code,
            "nominal": rate.nominal,
            "rate": rate.rate,
            "diff": rate.diff,
            "date": rate.date,
            "flag": rate.flag,
            "name_ru": rate.name_ru,
            "name_uz": rate.name_uz,
            "name_en": rate.name_en,
        })
    
    date = rates[0].date if rates else ""
    
    return {
        "date": date,
        "rates": rates_list
    }
