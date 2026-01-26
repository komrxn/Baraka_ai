from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete
from datetime import datetime, timedelta

from ..database import get_db
from ..models.user import User
from ..schemas import UserList, SubscriptionUpdateAction
from .auth import get_current_admin

router = APIRouter()

@router.get("/", response_model=UserList)
async def get_users(
    page: int = 1, 
    size: int = 10, 
    search: str = "", 
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    query = select(User)
    
    if search:
        search_fmt = f"%{search}%"
        query = query.where(
            (User.name.ilike(search_fmt)) | 
            (User.phone_number.ilike(search_fmt)) |
            (func.cast(User.telegram_id, String).ilike(search_fmt))
        )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get items
    query = query.order_by(desc(User.created_at)).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": users, # Pydantic will serialize this using UserBase with from_attributes=True
        "total": total,
        "page": page,
        "size": size
    }

@router.put("/{user_id}/subscription")
async def update_subscription(
    user_id: str,
    action: SubscriptionUpdateAction,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if action.action == "revoke":
        user.is_premium = False
        user.subscription_type = None
        user.subscription_ends_at = None
    elif action.action == "grant":
        user.is_premium = True
        user.subscription_type = action.plan or "manual"
        
        if action.duration_days:
            # Add to now
            user.subscription_ends_at = datetime.now() + timedelta(days=action.duration_days)
        elif action.plan == "monthly":
            user.subscription_ends_at = datetime.now() + timedelta(days=30)
        elif action.plan == "quarterly":
            user.subscription_ends_at = datetime.now() + timedelta(days=90)
        elif action.plan == "annual":
             user.subscription_ends_at = datetime.now() + timedelta(days=365)
        else:
             # Default 30 days if nothing specified
             user.subscription_ends_at = datetime.now() + timedelta(days=30)
             
    await db.commit()
    return {"status": "success", "user": {"is_premium": user.is_premium, "ends_at": user.subscription_ends_at}}

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin = Depends(get_current_admin)
):
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
         
    # Because validation confirmed cascade delete is configured in DB, 
    # we can just delete the user object.
    await db.delete(user)
    await db.commit()
    
    return {"status": "deleted"}
