import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional

from ...models.payme_transaction import PaymeTransaction
from ...models.user import User
from ...services.notification import send_subscription_success_message
from .exceptions import PaymeException

class PaymeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Amount in Tiyins. 1 UZS = 100 Tiyin.

    async def _get_user(self, user_id_str: str) -> Optional[User]:
        # 'account[order_id]' could be UUID or int (telegram_id).
        # Assuming UUID string based on `account[order_id]` plan.
        try:
            from uuid import UUID
            uid = UUID(user_id_str)
            result = await self.db.execute(select(User).where(User.id == uid))
            return result.scalar_one_or_none()
        except ValueError:
            return None

    def _make_error(self, code: int, message: str, data: str = None) -> PaymeException:
        # JSON-RPC 2.0 requires message to be a String.
        # -31050 requires data to be the field name.
        return PaymeException(
            code=code,
            message=message,
            data=data
        )
    
    # ---------------------------------------------------------
    # Methods
    # ---------------------------------------------------------

    async def check_perform_transaction(self, params: dict) -> dict:
        amount = params.get("amount")
        account = params.get("account", {})
        
        # Payme might send "order_id" inside account, or custom field names.
        # We enforce "order_id".
        order_id = account.get("order_id")

        if not order_id:
            # -31050 requires 'data' to be the name of the missing/invalid field
            raise self._make_error(-31050, "Order ID not found", "order_id")

        # 1. Validate User
        user = await self._get_user(str(order_id))
        if not user:
            raise self._make_error(-31050, "User not found", "order_id")

        # 2. Validate Amount
        if amount <= 0:
            raise self._make_error(-31001, "Invalid amount")

        return {"allow": True}

    async def create_transaction(self, params: dict) -> dict:
        paycom_id = params.get("id")
        paycom_time = params.get("time")
        amount = params.get("amount")
        account = params.get("account", {})
        order_id = account.get("order_id")

        # Check if transaction exists
        stmt = select(PaymeTransaction).where(PaymeTransaction.paycom_transaction_id == paycom_id)
        result = await self.db.execute(stmt)
        tx = result.scalar_one_or_none()

        if tx:
            # Idempotency check
            # If state != 1 (Waiting) -> Error -31008
            if tx.state != 1:
                raise self._make_error(-31008, "Transaction already processed")
            
            # Check timeout (12h = 43200000 ms)
            if (int(time.time() * 1000) - tx.create_time) > 43200000:
                tx.state = -1
                tx.reason = 4
                await self.db.commit()
                raise self._make_error(-31008, "Transaction timed out")

            return {
                "create_time": tx.create_time,
                "transaction": str(tx.id),
                "state": tx.state
            }
        
        # New Transaction
        # Re-validate (CheckPerformTransaction logic)
        try:
            await self.check_perform_transaction(params)
        except Exception as e:
            # Re-raise error if it's already a defined PaymeError, else wrap
            if isinstance(e, PaymeException): raise e
            raise self._make_error(-31008, "Validation failed")

        # Create
        new_tx = PaymeTransaction(
            paycom_transaction_id=paycom_id,
            paycom_time=paycom_time,
            paycom_time_datetime=datetime.fromtimestamp(paycom_time / 1000),
            create_time=int(time.time() * 1000),
            amount=amount,
            order_id=order_id,
            state=1
        )
        self.db.add(new_tx)
        await self.db.commit()
        await self.db.refresh(new_tx)

        return {
            "create_time": new_tx.create_time,
            "transaction": str(new_tx.id),
            "state": new_tx.state
        }

    async def perform_transaction(self, params: dict) -> dict:
        paycom_id = params.get("id")
        
        stmt = select(PaymeTransaction).where(PaymeTransaction.paycom_transaction_id == paycom_id)
        result = await self.db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
            raise self._make_error(-31003, "Transaction not found")
        
        if tx.state == 1:
            # Check timeout
            if (int(time.time() * 1000) - tx.create_time) > 43200000:
                tx.state = -1
                tx.reason = 4
                await self.db.commit()
                raise self._make_error(-31008, "Transaction timed out")
            
            # Perform
            tx.state = 2
            tx.perform_time = int(time.time() * 1000)
            await self.db.commit()

            # GRANT SUBSCRIPTION
            try:
                user = await self._get_user(str(tx.order_id))
                if user:
                    # Amount Logic (Tiyins to UZS)
                    amount_uzs = tx.amount / 100.0
                    
                    from dateutil.relativedelta import relativedelta
                    current_end = user.subscription_ends_at
                    if not current_end or current_end.replace(tzinfo=None) < datetime.now():
                        current_end = datetime.now()

                    # Thresholds (matching Click logic)
                    if amount_uzs > 150000:
                         user.subscription_type = "annual"
                         user.subscription_ends_at = current_end + relativedelta(years=1)
                    elif amount_uzs > 50000:
                         user.subscription_type = "quarterly"
                         user.subscription_ends_at = current_end + relativedelta(months=3)
                    else:
                         user.subscription_type = "monthly"
                         user.subscription_ends_at = current_end + relativedelta(months=1)
                    
                    user.is_premium = True
                    await self.db.commit()
                    
                    # Notify
                    try:
                        await send_subscription_success_message(user)
                    except Exception:
                        pass
            except Exception as e:
                # If grant fails, we still completed payment technically?
                # Or should we rollback? Payme expects success.
                # Log error.
                print(f"Failed to grant sub: {e}")

            return {
                "perform_time": tx.perform_time,
                "transaction": str(tx.id),
                "state": tx.state
            }

        elif tx.state == 2:
            # Idempotent
            return {
                "perform_time": tx.perform_time,
                "transaction": str(tx.id),
                "state": tx.state
            }
        else:
             raise self._make_error(-31008, "Transaction in invalid state")

    async def cancel_transaction(self, params: dict) -> dict:
        paycom_id = params.get("id")
        reason = params.get("reason")

        stmt = select(PaymeTransaction).where(PaymeTransaction.paycom_transaction_id == paycom_id)
        result = await self.db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
             raise self._make_error(-31003, "Transaction not found")

        if tx.state == 1:
            tx.state = -1
            tx.reason = reason
            tx.cancel_time = int(time.time() * 1000)
            await self.db.commit()
            return {
                "cancel_time": tx.cancel_time,
                "transaction": str(tx.id),
                "state": tx.state
            }
        
        elif tx.state == 2:
            # Refund
            # Check if we can refund (e.g. balance check). Assuming yes.
            tx.state = -2
            tx.reason = reason
            tx.cancel_time = int(time.time() * 1000)
            
            # REVOKE SUBSCRIPTION?
            # Ideally yes. But complex logic. For now just mark transaction cancelled.
            
            await self.db.commit()
            return {
                "cancel_time": tx.cancel_time,
                "transaction": str(tx.id),
                "state": tx.state
            }
        
        else:
             # Already cancelled
             return {
                "cancel_time": tx.cancel_time,
                "transaction": str(tx.id),
                "state": tx.state
            }

    async def check_transaction(self, params: dict) -> dict:
        paycom_id = params.get("id")
        stmt = select(PaymeTransaction).where(PaymeTransaction.paycom_transaction_id == paycom_id)
        result = await self.db.execute(stmt)
        tx = result.scalar_one_or_none()

        if not tx:
             raise self._make_error(-31003, "Transaction not found", "Tranzaksiya topilmadi")

        return {
            "create_time": tx.create_time,
            "perform_time": tx.perform_time,
            "cancel_time": tx.cancel_time,
            "transaction": str(tx.id),
            "state": tx.state,
            "reason": tx.reason
        }
    
    async def get_statement(self, params: dict) -> dict:
        from_time = params.get("from")
        to_time = params.get("to")
        
        stmt = select(PaymeTransaction).where(
            and_(
                PaymeTransaction.paycom_time >= from_time,
                PaymeTransaction.paycom_time <= to_time
            )
        )
        result = await self.db.execute(stmt)
        txs = result.scalars().all()
        
        return {
            "transactions": [
                {
                    "id": t.paycom_transaction_id,
                    "time": t.paycom_time,
                    "amount": t.amount,
                    "account": {"order_id": t.order_id},
                    "create_time": t.create_time,
                    "perform_time": t.perform_time,
                    "cancel_time": t.cancel_time,
                    "transaction": str(t.id),
                    "state": t.state,
                    "reason": t.reason
                }
                for t in txs
            ]
        }
