import hashlib
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from ..models.click_transaction import ClickTransaction
from ..models.user import User
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class ClickService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_md5(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def validate_signature(self, params: dict, is_complete: bool = False) -> bool:
        """
        Validate MD5 signature from Click.uz.
        Formula Prepare: click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time
        Formula Complete: ... + merchant_prepare_id + amount ...
        """
        # Ensure values are strings for concatenation
        secret = settings.click_secret_key
        
        # Prepare string
        sign_str = f"{params['click_trans_id']}{params['service_id']}{secret}{params['merchant_trans_id']}"
        
        if is_complete:
            # Complete needs merchant_prepare_id before amount
            sign_str += f"{params.get('merchant_prepare_id', '')}"
            
        sign_str += f"{params['amount']}{params['action']}{params['sign_time']}"
        
        generated_sign = self._generate_md5(sign_str)
        
        if generated_sign != params["sign_string"]:
            logger.error(f"Sign check failed. Generated: {generated_sign}, Received: {params['sign_string']}")
            return False
        return True

    async def prepare(self, data: dict) -> dict:
        """
        Handle 'Prepare' request (Action=0).
        Checks if user exists and amount is correct.
        """
        # 1. Validate Signature
        if not self.validate_signature(data, is_complete=False):
            return {"error": -1, "error_note": "SIGN CHECK FAILED!"}

        # 2. Extract internal IDs
        # merchant_trans_id is our click_transaction.merchant_trans_id OR user_id/plan_id string?
        # Let's assume passed transaction_param is 'user_id:plan_id' or a unique Order ID we generated. 
        # For simplicity, let's assume it IS the user_id for now, or we store a pending order.
        # But Click requires unique IDs.
        
        # Strategy: merchant_trans_id = ClickTransaction.merchant_trans_id
        # We should have created this record when generating the link.
        
        merchant_trans_id = data["merchant_trans_id"]
        
        # Check if transaction exists (already created via Generate Link)
        result = await self.db.execute(select(ClickTransaction).where(ClickTransaction.merchant_trans_id == merchant_trans_id))
        transaction = result.scalar_one_or_none()

        if not transaction:
             # Or maybe we allow implicit creation? No, safer to require pre-generation.
             return {"error": -6, "error_note": "Transaction does not exist"}

        # Check amount
        if float(transaction.amount) != float(data['amount']):
            return {"error": -2, "error_note": "Incorrect parameter amount"}

        # Update status to waiting
        transaction.click_trans_id = int(data["click_trans_id"])
        transaction.click_paydoc_id = int(data["click_paydoc_id"])
        transaction.status = "waiting"
        transaction.updated_at = datetime.now()
        
        await self.db.commit()
        
        return {
            "click_trans_id": data["click_trans_id"],
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": str(transaction.id), # Use our UUID as prepare_id
            "error": 0,
            "error_note": "Success"
        }

    async def complete(self, data: dict) -> dict:
        """
        Handle 'Complete' request (Action=1).
        Finalizes payment and grants subscription.
        """
        # 1. Validate Signature
        if not self.validate_signature(data, is_complete=True):
            return {"error": -1, "error_note": "SIGN CHECK FAILED!"}

        merchant_trans_id = data["merchant_trans_id"]
        merchant_prepare_id = data["merchant_prepare_id"] # This should be our UUID str

        # 2. Find transaction
        try:
             # Verify by UUID
             trans_uuid = UUID(merchant_prepare_id)
        except ValueError:
             return {"error": -6, "error_note": "Invalid merchant_prepare_id"}
            
        result = await self.db.execute(select(ClickTransaction).where(ClickTransaction.id == trans_uuid))
        transaction = result.scalar_one_or_none()

        if not transaction:
            return {"error": -6, "error_note": "Transaction does not exist"}
            
        if transaction.status == "confirmed":
             return {"error": -4, "error_note": "Already paid"}
             
        if transaction.status == "cancelled":
             return {"error": -9, "error_note": "Transaction cancelled"}

        if int(data['error']) < 0:
            # Click signals error
            transaction.status = "error"
            transaction.error = int(data['error'])
            await self.db.commit()
            return {"error": -9, "error_note": "Transaction cancelled"}

        # 3. Success -> Grant Subscription
        transaction.status = "confirmed"
        transaction.action = 1
        transaction.sign_time = data["sign_time"]
        
        # Grant Logic
        user_result = await self.db.execute(select(User).where(User.id == transaction.user_id))
        user = user_result.scalar_one()
        
        # Determine duration based on amount
        current_end = user.subscription_ends_at
        if not current_end or current_end.replace(tzinfo=None) < datetime.now():
            current_end = datetime.now()

        if transaction.amount > 150000:
             # Annual (approx 199k)
             user.subscription_type = "annual"
             from dateutil.relativedelta import relativedelta
             user.subscription_ends_at = current_end + relativedelta(years=1)
        else:
             user.subscription_type = "monthly"
             from dateutil.relativedelta import relativedelta
             user.subscription_ends_at = current_end + relativedelta(months=1)
        
        user.is_premium = True
        
        user.is_premium = True
        
        await self.db.commit()
        
        # Send success notification
        from .notification import send_subscription_success_message
        try:
             # Reload user to ensure latest state if needed, or pass current object
            await send_subscription_success_message(user)
        except Exception as e:
            logger.error(f"Failed to send success msg: {e}")
        
        return {
            "click_trans_id": data["click_trans_id"],
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": str(transaction.id),
            "error": 0,
            "error_note": "Success"
        }
