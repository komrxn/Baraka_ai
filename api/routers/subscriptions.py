from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid
import base64

from ..database import get_db
from ..models.user import User
from ..models.click_transaction import ClickTransaction
from ..payment.schemas import PaymentLinkRequest, PaymentLinkResponse
from ..schemas.auth import UserResponse
from ..payment.click.services import ClickService
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
    # is_active represents if the subscription logic considers it valid
    # But now UserResponse computes it via property, so we might just return user?
    # Actually, the UserResponse schema handles computation now.
    return UserResponse.model_validate(current_user)

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
    # Grant 3 days of Pro features
    current_user.subscription_type = "pro" 
    current_user.is_trial_used = True
    current_user.subscription_ends_at = datetime.now() + timedelta(days=3)
    
    await db.commit()
    
    # Send success notification
    from ..services.notification import send_subscription_success_message
    try:
        await send_subscription_success_message(current_user)
    except Exception as e:
        # Don't fail request if notification fails
        pass

    return {"message": "Trial activated", "ends_at": current_user.subscription_ends_at}

@router.post("/pay", response_model=PaymentLinkResponse)
async def generate_payment_link(
    request: PaymentLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Click.uz or Payme payment link.
    """
    # 1. Determine amount & plan
    # Plus: 34,999 (1 mo) / 94,999 (3 mo)
    # Pro: 49,999 (1 mo) / 119,999 (3 mo)
    # Premium: 89,999 (1 mo) / 229,999 (3 mo)
    
    amount = 0.0
    
    if request.plan_id == "plus_1":
        amount = 34999.00
    elif request.plan_id == "plus_3":
        amount = 94999.00
    elif request.plan_id == "pro_1":
        amount = 49999.00
    elif request.plan_id == "pro_3":
        amount = 119999.00
    elif request.plan_id == "premium_1":
        amount = 89999.00
    elif request.plan_id == "premium_3":
        amount = 229999.00
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
    if request.provider == "payme":
        # Payme Link Generation
        # Params: m=merchant_id; ac.order_id=user_id; a=amount_tiyin
        amount_tiyin = int(amount * 100)
        params_str = f"m={settings.payme_merchant_id};ac.order_id={current_user.id};a={amount_tiyin}"
        b64_params = base64.b64encode(params_str.encode()).decode()
        
        base_url = "https://test.paycom.uz" if settings.payme_test_mode else "https://checkout.paycom.uz"
        url = f"{base_url}/{b64_params}"
    else:
        # Click Link Generation
        url = f"https://my.click.uz/services/pay?service_id={settings.click_service_id}&merchant_id={settings.click_merchant_id}&amount={amount}&transaction_param={merchant_trans_id}"
    
    return {"url": url}
