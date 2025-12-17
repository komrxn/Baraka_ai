from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from ..schemas.telegram import TelegramAuthRequest
from ..auth.jwt import get_password_hash, verify_password, create_access_token, get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user with Telegram credentials."""
    
    # Check if telegram_id exists
    result = await db.execute(select(User).where(User.telegram_id == user_data.telegram_id))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this Telegram ID already exists"
        )
    
    # Check if phone number exists
    result = await db.execute(select(User).where(User.phone_number == user_data.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )
    
    # Create new user (no password!)
    new_user = User(
        telegram_id=user_data.telegram_id,
        phone_number=user_data.phone_number,
        name=user_data.name
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user with phone number."""
    
    # Find user by phone
    result = await db.execute(select(User).where(User.phone_number == credentials.phone_number))
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
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
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
        # Auto-create user from Telegram data
        username = tg_user["username"] or f"tg_{tg_user['id']}"
        email = f"tg_{tg_user['id']}@telegram.user"  # Dummy email
        
        # Ensure username is unique
        result = await db.execute(select(User).where(User.username == username))
        if result.scalar_one_or_none():
            username = f"tg_{tg_user['id']}_{tg_user['first_name'][:5]}"
        
        user = User(
            username=username,
            email=email,
            telegram_id=tg_user["id"],
            telegram_username=tg_user["username"],
            telegram_first_name=tg_user["first_name"],
            telegram_last_name=tg_user["last_name"],
            hashed_password=None  # No password for Telegram users
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )
