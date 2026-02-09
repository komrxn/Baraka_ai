from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.user import User
from ..models.category import Category
from ..models.transaction import Transaction
from ..schemas.ai import AIParseRequest, AIParseResponse, CategorySuggestRequest, CategorySuggestResponse, CategorySuggestion
from ..auth.jwt import get_current_user
from ..services.ai_parser import AITransactionParser
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/parse-transaction", response_model=AIParseResponse)
async def parse_transaction(
    text: Optional[str] = Form(None),
    voice: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    auto_create: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Parse transaction from text, voice, or image.
    
    - **text**: Text message (e.g., "купил бургер за 112000 сум")
    - **voice**: Voice message file (OGG, MP3, WAV)
    - **image**: Receipt/check image (JPG, PNG)
    - **auto_create**: If true, automatically create transaction if confidence > 0.7
    
    Returns parsed transaction data with AI confidence score.
    """
    
    parser = AITransactionParser(api_key=settings.openai_api_key)
    parsed_data = None
    
    # Priority: voice > image > text
    if voice:
        # Transcribe voice first
        audio_data = await voice.read()
        transcribed_text = parser.transcribe_voice(audio_data, voice.filename or "audio.ogg")
        # Then parse the transcribed text
        parsed_data = parser.parse_text(transcribed_text)
    elif image:
        # Parse receipt image
        image_data = await image.read()
        parsed_data = parser.parse_receipt_image(image_data)
    elif text:
        # Parse text message
        parsed_data = parser.parse_text(text)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide text, voice, or image"
        )
    
    # Find matching category in database
    category_id = None
    category_name = None
    
    if parsed_data["category_slug"]:
        result = await db.execute(
            select(Category).where(
                Category.slug == parsed_data["category_slug"],
                Category.is_default == True
            )
        )
        category = result.scalar_one_or_none()
        if category:
            category_id = category.id
            category_name = category.name
    
    # Auto-create transaction if requested and confidence is high
    auto_created = False
    conversion_error = False
    converted_from = None
    
    if auto_create and parsed_data["confidence"] >= 0.7:
        final_amount = parsed_data["amount"]
        final_currency = parsed_data["currency"]
        
        # Multi-currency conversion for Pro/Premium users
        if parsed_data["currency"].lower() != "uzs" and current_user.subscription_tier in ("pro", "premium"):
            from ..services.currency import convert_to_uzs
            
            converted_amount = await convert_to_uzs(
                float(parsed_data["amount"]), 
                parsed_data["currency"].upper()
            )
            
            if converted_amount is not None:
                converted_from = f"{parsed_data['amount']} {parsed_data['currency'].upper()}"
                final_amount = converted_amount
                final_currency = "uzs"
            else:
                # Conversion failed - still save but mark error
                conversion_error = True
        
        new_transaction = Transaction(
            user_id=current_user.id,
            category_id=category_id,
            type=parsed_data["type"],
            amount=final_amount,
            currency=final_currency,
            description=parsed_data["description"],
            ai_parsed_data=parsed_data,
            ai_confidence=parsed_data["confidence"],
        )
        db.add(new_transaction)
        await db.commit()
        auto_created = True
    
    return AIParseResponse(
        type=parsed_data["type"],
        amount=parsed_data["amount"],
        currency=parsed_data["currency"],
        description=parsed_data["description"],
        suggested_category_id=category_id,
        suggested_category_name=category_name,
        confidence=parsed_data["confidence"],
        ai_parsed_data=parsed_data,
        auto_created=auto_created,
    )


@router.post("/suggest-category", response_model=CategorySuggestResponse)
async def suggest_category(
    request: CategorySuggestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get category suggestions for a transaction description.
    
    Uses AI to suggest the most appropriate category.
    """
    
    parser = AITransactionParser(api_key=settings.openai_api_key)
    
    # Create a fake transaction text for parsing
    fake_text = f"{request.description} 100 uzs"
    parsed = parser.parse_text(fake_text)
    
    suggestions = []
    
    if parsed["category_slug"]:
        # Find category in database
        result = await db.execute(
            select(Category).where(
                Category.slug == parsed["category_slug"],
                Category.type == request.transaction_type,
                Category.is_default == True
            )
        )
        category = result.scalar_one_or_none()
        
        if category:
            suggestions.append(CategorySuggestion(
                category_id=category.id,
                category_name=category.name,
                category_slug=category.slug,
                confidence=parsed["confidence"]
            ))
    
    best_match = suggestions[0] if suggestions else None
    
    return CategorySuggestResponse(
        suggestions=suggestions,
        best_match=best_match
    )
