from fastapi import APIRouter, Depends, Form, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..services.click import ClickService
from ..schemas.click import ClickResponse

router = APIRouter(prefix="/click", tags=["Click.uz"])

@router.post("/prepare")
async def prepare_transaction(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    amount: str = Form(...),  # string to preserve exact format for md5
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Click Prepare request (Action=0).
    """
    service = ClickService(db)
    data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "amount": amount,
        "action": action,
        "error": error,
        "error_note": error_note,
        "sign_time": sign_time,
        "sign_string": sign_string
    }
    return await service.prepare(data)

@router.post("/complete")
async def complete_transaction(
    click_trans_id: int = Form(...),
    service_id: int = Form(...),
    click_paydoc_id: int = Form(...),
    merchant_trans_id: str = Form(...),
    merchant_prepare_id: str = Form(...),  # UUID string
    amount: str = Form(...),  # string
    action: int = Form(...),
    error: int = Form(...),
    error_note: str = Form(...),
    sign_time: str = Form(...),
    sign_string: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Click Complete request (Action=1).
    """
    service = ClickService(db)
    data = {
        "click_trans_id": click_trans_id,
        "service_id": service_id,
        "click_paydoc_id": click_paydoc_id,
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": str(merchant_prepare_id), # Ensure string for UUID check
        "amount": amount,
        "action": action,
        "error": error,
        "error_note": error_note,
        "sign_time": sign_time,
        "sign_string": sign_string
    }
    return await service.complete(data)
