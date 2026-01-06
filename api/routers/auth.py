from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from ..database import get_db
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from ..schemas.telegram import TelegramAuthRequest
from ..auth.jwt import create_access_token, get_password_hash, verify_password, get_current_user

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Normalize phone number to 998XXXXXXXXX format (Uzbekistan)."""
    # Remove all non-digits (removes +, spaces, dashes, etc)
    digits = ''.join(filter(str.isdigit, phone))
    
    # If already starts with 998, return as is
    if digits.startswith('998'):
        return digits
    
    # Add 998 prefix for local numbers
    return f"998{digits}"


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with phone number."""
    
    # Normalize phone number (998XXXXXXXXX format)
    normalized_phone = normalize_phone(user_data.phone_number)
    
    # Check if user with this telegram_id already exists
    result = await db.execute(
        select(User).where(User.telegram_id == user_data.telegram_id)
    )
    existing_by_telegram = result.scalar_one_or_none()
    
    if existing_by_telegram:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this Telegram account already registered"
        )
    
    # Check if phone number already exists
    result = await db.execute(
        select(User).where(User.phone_number == normalized_phone)
    )
    existing_by_phone = result.scalar_one_or_none()
    
    if existing_by_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create new user with normalized phone
    new_user = User(
        telegram_id=user_data.telegram_id,
        phone_number=normalized_phone,  # Store without +
        name=user_data.name,
        language=user_data.language,  # Use language from request
        is_premium=False,
        subscription_type=None,
        is_trial_used=False,
    )
    
    # No trial by default - user must activate it manually
    new_user.subscription_ends_at = None
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "telegram_id": new_user.telegram_id}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user with phone number."""
    
    # Normalize phone number
    normalized_phone = normalize_phone(credentials.phone_number)
    
    # Find user by normalized phone
    result = await db.execute(
        select(User).where(User.phone_number == normalized_phone)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Optional: validate telegram_id if provided
    if credentials.telegram_id and user.telegram_id != credentials.telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "telegram_id": user.telegram_id}
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)


@router.patch("/me/language", response_model=UserResponse)
async def update_user_language(
    language: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's language preference."""
    # Validate language
    if language not in ["uz", "ru", "en"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be one of: uz, ru, en"
        )
    
    # Update user language
    current_user.language = language
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/telegram-auth", response_model=TokenResponse)
async def telegram_auth(
    telegram_data: TelegramAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user via Telegram Mini App initData.
    
    This endpoint validates Telegram Web App initData, creates a user if needed,
    and returns a JWT token for API access.
    
    Flow:
    1. Validate HMAC signature (crypto verification)
    2. Check timestamp freshness (anti-replay)
    3. Parse user data
    4. Find or create user by telegram_id
    5. Generate JWT token
    
    Security:
    - HMAC-SHA256 signature validation
    - 5-minute timestamp window
    - Constant-time comparison
    """
    from ..config import get_settings
    from ..services.telegram_auth import (
        validate_telegram_init_data,
        parse_telegram_user,
        InvalidSignatureError,
        ExpiredInitDataError,
        MalformedInitDataError
    )
    
    settings = get_settings()
    
    # Validate Telegram initData
    try:
        validated_data = validate_telegram_init_data(
            telegram_data.init_data,
            settings.telegram_bot_token
        )
    except InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Telegram signature"
        )
    except ExpiredInitDataError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telegram data expired, please reopen the app"
        )
    except MalformedInitDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Telegram data: {str(e)}"
        )
    
    # Parse Telegram user data
    try:
        tg_user = parse_telegram_user(validated_data)
    except MalformedInitDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid user data: {str(e)}"
        )
    
    # Find or create user
    result = await db.execute(
        select(User).where(User.telegram_id == tg_user["id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered. Please register via bot first."
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )
