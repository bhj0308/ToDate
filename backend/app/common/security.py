import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import get_settings

_settings = get_settings()


def generate_otp_code() -> str:
    """6-digit numeric OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def verify_otp(code: str, code_hash: str) -> bool:
    return secrets.compare_digest(hash_otp(code), code_hash)


def _encode(subject: str, token_type: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def issue_access_token(user_id: uuid.UUID) -> str:
    return _encode(
        str(user_id),
        "access",
        timedelta(minutes=_settings.access_token_ttl_minutes),
    )


def issue_refresh_token(user_id: uuid.UUID) -> str:
    return _encode(
        str(user_id),
        "refresh",
        timedelta(days=_settings.refresh_token_ttl_days),
    )


def decode_token(token: str, expected_type: str) -> uuid.UUID:
    """Return the subject user id, or raise jwt exceptions / ValueError."""
    payload = jwt.decode(
        token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm]
    )
    if payload.get("type") != expected_type:
        raise ValueError("unexpected token type")
    return uuid.UUID(payload["sub"])
