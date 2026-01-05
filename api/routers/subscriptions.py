from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from ..database import get_db
from ..models.user import User
from ..models.click_transaction import ClickTransaction
from ..schemas.click import PaymentLinkRequest, PaymentLinkResponse
from ..schemas.auth import UserResponse
from ..services.click import ClickService
from ..config import get_settings

from ..auth.jwt import get_current_user

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])
settings = get_settings()

@router.get("/status", response_model=UserResponse)
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Calculate active status
    is_active = False
    if current_user.is_premium and current_user.subscription_ends_at:
        if current_user.subscription_ends_at.timestamp() > datetime.now().timestamp():
            is_active = True
            
    # We can't just return current_user because we need to inject is_active
    # Pydantic v2 would use computed_field, but compatible way:
    return UserResponse(
        id=current_user.id,
        telegram_id=current_user.telegram_id,
        phone_number=current_user.phone_number,
        name=current_user.name,
        default_currency=current_user.default_currency,
        language=current_user.language,
        created_at=current_user.created_at,
        is_premium=current_user.is_premium,
        subscription_type=current_user.subscription_type,
        subscription_ends_at=current_user.subscription_ends_at,
        is_trial_used=current_user.is_trial_used,
        is_active=is_active
    )

@router.post("/trial")
async def activate_trial(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate 3-day free trial.
    """
    if current_user.is_trial_used:
        raise HTTPException(status_code=400, detail="Trial already used")
        
    # Grant 3 days
    current_user.subscription_type = "trial"
    current_user.is_premium = True
    current_user.is_trial_used = True
    current_user.subscription_ends_at = datetime.now() + timedelta(days=3)
    
    await db.commit()
    return {"message": "Trial activated", "ends_at": current_user.subscription_ends_at}

@router.post("/pay", response_model=PaymentLinkResponse)
async def generate_payment_link(
    request: PaymentLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Click.uz payment link.
    """
    # 1. Determine amount
    if request.plan_id == "monthly":
        amount = 19990.00
    elif request.plan_id == "quarterly":
        amount = 56990.00
    elif request.plan_id == "annual":
        amount = 199900.00
    else:
        raise HTTPException(status_code=400, detail="Invalid plan")

    # 2. Create pending transaction (Order)
    merchant_trans_id = str(uuid.uuid4())
    
    click_trans = ClickTransaction(
        click_trans_id=None, # Temporary, will be filled by Prepare
        service_id=int(settings.click_service_id) if settings.click_service_id.isdigit() else 0,
        click_paydoc_id=0,
        merchant_trans_id=merchant_trans_id,
        amount=amount,
        user_id=current_user.id,
        action=0,
        sign_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        status="input"
    )
    
    db.add(click_trans)
    await db.commit()
    
    # 3. Generate Link
    # https://my.click.uz/services/pay?service_id={service_id}&merchant_id={merchant_id}&amount={amount}&transaction_param={merchant_trans_id}
    
    url = f"https://my.click.uz/services/pay?service_id={settings.click_service_id}&merchant_id={settings.click_merchant_id}&amount={amount}&transaction_param={merchant_trans_id}"
    
    return {"url": url}
