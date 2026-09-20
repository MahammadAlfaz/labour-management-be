import pytest

from app.config import get_settings
from app.core.security import TokenError, create_access_token, create_refresh_token, decode_token


def test_access_token_round_trip():
    token = create_access_token("abc123", "admin@example.com")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "abc123"
    assert payload["email"] == "admin@example.com"


def test_refresh_token_round_trip():
    token = create_refresh_token("abc123")
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "abc123"


def test_decode_rejects_wrong_token_type():
    token = create_access_token("abc123", "admin@example.com")
    with pytest.raises(TokenError):
        decode_token(token, expected_type="refresh")


def test_decode_rejects_tampered_token():
    token = create_access_token("abc123", "admin@example.com")
    # Flip a character in the middle of the signature, not the last one --
    # base64url's final symbol can have unused padding bits, so tampering
    # only the last character can coincidentally decode to the same bytes.
    mid = len(token) // 2
    tampered = token[:mid] + ("A" if token[mid] != "A" else "B") + token[mid + 1 :]
    with pytest.raises(TokenError):
        decode_token(tampered, expected_type="access")


def test_decode_rejects_expired_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_access_token_expire_minutes", -1)
    token = create_access_token("abc123", "admin@example.com")
    with pytest.raises(TokenError):
        decode_token(token, expected_type="access")
