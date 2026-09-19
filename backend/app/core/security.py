from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import get_settings


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or of the wrong type."""


def _create_token(subject: str, expires_delta: timedelta, token_type: str, extra_claims: dict) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        **extra_claims,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(admin_id: str, email: str) -> str:
    settings = get_settings()
    return _create_token(
        admin_id,
        timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "access",
        {"email": email},
    )


def create_refresh_token(admin_id: str) -> str:
    settings = get_settings()
    return _create_token(
        admin_id,
        timedelta(days=settings.jwt_refresh_token_expire_days),
        "refresh",
        {},
    )


def decode_token(token: str, expected_type: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    return payload
