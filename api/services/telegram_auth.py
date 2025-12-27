"""
Telegram Web App authentication service.

Provides secure authentication via Telegram Mini Apps using HMAC-SHA256 validation.
"""

import hmac
import hashlib
import time
from typing import Optional
from urllib.parse import parse_qsl, unquote


class TelegramAuthError(Exception):
    """Base exception for Telegram authentication errors."""
    pass


class InvalidSignatureError(TelegramAuthError):
    """HMAC signature validation failed."""
    pass


class ExpiredInitDataError(TelegramAuthError):
    """initData timestamp too old (replay attack prevention)."""
    pass


class MalformedInitDataError(TelegramAuthError):
    """initData format is invalid."""
    pass


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 300
) -> dict[str, str]:
    """
    Validates Telegram Web App initData using HMAC-SHA256.
    
    This implements the official Telegram validation algorithm:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Security guarantees:
    - Cryptographic signature verification (HMAC-SHA256)
    - Timestamp validation (default: 5 minutes window)
    - Data integrity check
    
    Args:
        init_data: Raw initData string from Telegram.WebApp.initData
        bot_token: Telegram bot token (used as secret key)
        max_age_seconds: Maximum age of initData in seconds (default: 300)
    
    Returns:
        Parsed initData as dictionary
    
    Raises:
        InvalidSignatureError: HMAC signature doesn't match
        ExpiredInitDataError: initData is too old
        MalformedInitDataError: initData format is invalid
    
    Example:
        >>> init_data = "user=%7B%22id%22%3A123%7D&auth_date=1234567890&hash=abc123"
        >>> data = validate_telegram_init_data(init_data, "7931558614:AAG...")
        >>> print(data['user'])  # {"id": 123}
    """
    try:
        # Parse query string
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception as e:
        raise MalformedInitDataError(f"Failed to parse initData: {e}")
    
    # Extract and remove hash
    received_hash = parsed_data.pop('hash', None)
    if not received_hash:
        raise MalformedInitDataError("Missing 'hash' in initData")
    
    # Check timestamp freshness
    auth_date_str = parsed_data.get('auth_date')
    if not auth_date_str:
        raise MalformedInitDataError("Missing 'auth_date' in initData")
    
    try:
        auth_date = int(auth_date_str)
    except ValueError:
        raise MalformedInitDataError("Invalid 'auth_date' format")
    
    current_time = int(time.time())
    if (current_time - auth_date) > max_age_seconds:
        raise ExpiredInitDataError(
            f"initData expired (age: {current_time - auth_date}s, max: {max_age_seconds}s)"
        )
    
    # Create data check string
    # According to Telegram docs: sort parameters alphabetically and join with \n
    data_check_string = '\n'.join(
        f"{k}={v}" for k, v in sorted(parsed_data.items())
    )
    
    # Compute secret key
    # secret_key = HMAC_SHA256(token, "WebAppData")
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    # Calculate expected hash
    # hash = HMAC_SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(calculated_hash, received_hash):
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Telegram Auth Failed: Signature Mismatch")
        logger.error(f"Received Hash: {received_hash}")
        logger.error(f"Calculated Hash: {calculated_hash}")
        logger.error(f"Bot Token (masked): {bot_token[:5]}...{bot_token[-5:]}")
        check_str_debug = data_check_string.replace('\n', '\\n')
        logger.error(f"Data Check String:\n{check_str_debug}")
        
        raise InvalidSignatureError("Telegram signature validation failed")
    
    # Signature valid, return parsed data
    return parsed_data


def parse_telegram_user(init_data: dict[str, str]) -> dict:
    """
    Extracts user information from validated initData.
    
    Args:
        init_data: Validated initData dictionary (from validate_telegram_init_data)
    
    Returns:
        Dictionary with user data:
        {
            "id": int,
            "first_name": str,
            "last_name": str | None,
            "username": str | None,
            "language_code": str | None
        }
    
    Raises:
        MalformedInitDataError: Missing or invalid user data
    """
    import json
    
    user_json = init_data.get('user')
    if not user_json:
        raise MalformedInitDataError("Missing 'user' in initData")
    
    try:
        # User data is URL-encoded JSON
        user_data = json.loads(unquote(user_json))
    except (json.JSONDecodeError, ValueError) as e:
        raise MalformedInitDataError(f"Invalid user JSON: {e}")
    
    # Extract required fields
    telegram_id = user_data.get('id')
    if not telegram_id or not isinstance(telegram_id, int):
        raise MalformedInitDataError("Missing or invalid 'id' in user data")
    
    first_name = user_data.get('first_name', '')
    if not first_name:
        raise MalformedInitDataError("Missing 'first_name' in user data")
    
    return {
        "id": telegram_id,
        "first_name": first_name,
        "last_name": user_data.get('last_name'),
        "username": user_data.get('username'),
        "language_code": user_data.get('language_code', 'en')
    }
