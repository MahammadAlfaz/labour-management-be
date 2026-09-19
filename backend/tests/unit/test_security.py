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
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(TokenError):
        decode_token(tampered, expected_type="access")


def test_decode_rejects_expired_token(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "jwt_access_token_expire_minutes", -1)
    token = create_access_token("abc123", "admin@example.com")
    with pytest.raises(TokenError):
        decode_token(token, expected_type="access")
