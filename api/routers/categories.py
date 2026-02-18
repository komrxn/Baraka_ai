from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..database import get_db
from ..models.user import User
from ..models.category import Category
from ..schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryWithStats
from ..auth.jwt import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    type: str = None,  # expense, income, debt
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all categories available to the user.
    
    Returns both default (system) categories and user's custom categories.
    """
    
    query = select(Category).where(
        or_(
            Category.is_default == True,
            Category.user_id == current_user.id
        )
    )
    
    if type:
        query = query.where(Category.type == type)
    
    query = query.order_by(Category.name)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return [CategoryResponse.model_validate(cat) for cat in categories]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_custom_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a custom category for the user.
    
    Custom categories are user-specific and can be used for transactions.
    """
    
    # Check if slug already exists for this user
    result = await db.execute(
        select(Category).where(
            Category.slug == category_data.slug,
            or_(
                Category.user_id == current_user.id,
                Category.is_default == True
            )
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{category_data.slug}' already exists"
        )
    
    # Create category
    new_category = Category(
        user_id=current_user.id,
        **category_data.model_dump(),
        is_default=False
    )
    
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    return CategoryResponse.model_validate(new_category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    update_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a custom category.
    
    Only user's own custom categories can be updated (not default categories).
    """
    
    # First find the category without restrictive filters to check what it is
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
        
    # Check permissions
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot edit system default categories. Please create a new custom category."
        )
        
    if category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a custom category.
    
    Only custom categories with no associated transactions can be deleted.
    """
    
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == current_user.id,
            Category.is_default == False
        )
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or cannot be deleted"
        )
    
    # Check if category is used in transactions
    from ..models.transaction import Transaction
    tx_result = await db.execute(
        select(Transaction).where(Transaction.category_id == category_id).limit(1)
    )
    if tx_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category that has associated transactions"
        )
    
    await db.delete(category)
    await db.commit()
    
    return None
