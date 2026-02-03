import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from api.services.ai_parser import AITransactionParser
from api.models.user import User

# Mock DB Session
@pytest.fixture
def mock_db():
    return AsyncMock()

# Fixture for Parser
@pytest.fixture
def parser():
    return AITransactionParser(api_key="fake-key")

# Helper to create user with specific state
def create_test_user(tier="free", req_3day=0, voice_daily=0, img_daily=0, last_3day=None, last_daily=None):
    user = User()
    user.subscription_type = tier
    user.request_count_3day = req_3day
    user.voice_usage_daily = voice_daily
    user.image_usage_daily = img_daily
    user.last_3day_reset = last_3day
    user.last_daily_reset = last_daily
    return user

@pytest.mark.asyncio
async def test_get_model_for_tier(parser):
    """Verify correct AI model is selected for each tier."""
    assert parser.get_model_for_tier("free") == "gpt-5-nano"
    assert parser.get_model_for_tier("plus") == "gpt-5-mini"
    assert parser.get_model_for_tier("pro") == "gpt-5.1"
    assert parser.get_model_for_tier("premium") == "gpt-5.1"
    # Fallback
    assert parser.get_model_for_tier("unknown") == "gpt-5-nano"

@pytest.mark.asyncio
async def test_check_limits_request_free_tier(parser):
    """Test 3-day request limits for Free tier (180 limit)."""
    # 1. Under limit
    user = create_test_user(tier="free", req_3day=179, last_3day=datetime.now())
    allowed = await parser.check_limits(user, "request")
    assert allowed is True

    # 2. At limit
    user.request_count_3day = 180
    allowed = await parser.check_limits(user, "request")
    assert allowed is False

    # 3. Over limit
    user.request_count_3day = 181
    allowed = await parser.check_limits(user, "request")
    assert allowed is False

@pytest.mark.asyncio
async def test_check_limits_voice_premium_tier(parser):
    """Test daily voice limits for Premium tier (100 limit)."""
    # 1. Under limit
    user = create_test_user(tier="premium", voice_daily=99, last_daily=datetime.now())
    allowed = await parser.check_limits(user, "voice")
    assert allowed is True

    # 2. At limit
    user.voice_usage_daily = 100
    allowed = await parser.check_limits(user, "voice")
    assert allowed is False

@pytest.mark.asyncio
async def test_3day_reset_logic(parser):
    """Test validity of 3-day Recoil reset."""
    # Setup: User was reset 4 days ago (should trigger reset)
    four_days_ago = datetime.now() - timedelta(days=4)
    user = create_test_user(tier="free", req_3day=180, last_3day=four_days_ago) # Usage is full

    # Action: Check limits
    # Should trigger reset inside check_limits before checking count
    allowed = await parser.check_limits(user, "request")
    
    # Assertions
    assert allowed is True # Should be allowed now
    assert user.request_count_3day == 0 # Count should be reset
    assert user.last_3day_reset.date() == datetime.now().date() # Reset time updated

@pytest.mark.asyncio
async def test_daily_reset_logic(parser):
    """Test daily usage reset."""
    yesterday = datetime.now() - timedelta(days=1)
    user = create_test_user(tier="free", voice_daily=5, last_daily=yesterday) # Full usage
    
    allowed = await parser.check_limits(user, "voice")
    
    assert allowed is True
    assert user.voice_usage_daily == 0
    assert user.last_daily_reset.date() == datetime.now().date()

@pytest.mark.asyncio
async def test_update_usage(parser, mock_db):
    """Test incrementing usage counters."""
    user = create_test_user(tier="free")
    
    await parser.update_usage(user, "voice", mock_db)
    
    assert user.voice_usage_daily == 1
    assert user.request_count_3day == 1 # Voice also counts as request (Recoil)
    mock_db.commit.assert_called_once()
