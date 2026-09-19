"""Sanity-checks the developer's local backend/.env file.

These tests deliberately read backend/.env directly with dotenv_values instead
of going through app.config.get_settings(), because tests/conftest.py sets
safe fallback values (JWT_SECRET_KEY, ADMIN_EMAILS, ...) via os.environ so the
rest of the suite can run without real credentials -- and an environment
variable always takes priority over the .env file for the same key. Reading
the file directly is the only way to actually verify what's in it.

Requires backend/.env to exist (copy backend/.env.example and fill it in).
Not meant to run in CI, which has no .env file -- this is a local checklist.
"""

from pathlib import Path

import pytest
from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

PLACEHOLDER_JWT_SECRET = "change-me-to-a-long-random-string"
PLACEHOLDER_ADMIN_EMAILS = {"admin1@example.com", "admin2@example.com", "admin3@example.com"}

pytestmark = pytest.mark.skipif(
    not ENV_PATH.exists(), reason="backend/.env not present (expected outside local dev)"
)


@pytest.fixture(scope="module")
def env() -> dict[str, str | None]:
    return dotenv_values(ENV_PATH)


def test_mongodb_url_is_configured(env: dict[str, str | None]):
    url = env.get("MONGODB_URL") or ""
    assert url.startswith("mongodb"), "MONGODB_URL is missing or not a mongodb:// / mongodb+srv:// URI"


def test_google_oauth_credentials_are_configured(env: dict[str, str | None]):
    client_id = env.get("GOOGLE_CLIENT_ID") or ""
    client_secret = env.get("GOOGLE_CLIENT_SECRET") or ""
    assert client_id, "GOOGLE_CLIENT_ID is empty in backend/.env"
    assert client_id.endswith(".apps.googleusercontent.com"), (
        "GOOGLE_CLIENT_ID doesn't look like a Google OAuth client ID"
    )
    assert client_secret.startswith("GOCSPX-"), (
        "GOOGLE_CLIENT_SECRET is empty or doesn't look like a Google client secret"
    )


def test_supabase_credentials_are_configured(env: dict[str, str | None]):
    url = env.get("SUPABASE_URL") or ""
    assert url.startswith("https://") and url.endswith(".supabase.co"), (
        "SUPABASE_URL is missing or malformed"
    )
    assert (env.get("SUPABASE_PUBLISHABLE_KEY") or "").startswith("sb_publishable_"), (
        "SUPABASE_PUBLISHABLE_KEY is missing or doesn't match the expected format"
    )
    assert (env.get("SUPABASE_SECRET_KEY") or "").startswith("sb_secret_"), (
        "SUPABASE_SECRET_KEY is missing or doesn't match the expected format"
    )
    assert env.get("SUPABASE_JWKS_URL") == f"{url}/auth/v1/.well-known/jwks.json", (
        "SUPABASE_JWKS_URL should be <SUPABASE_URL>/auth/v1/.well-known/jwks.json"
    )


def test_bootstrap_secrets_have_been_changed_from_placeholders(env: dict[str, str | None]):
    jwt_secret = env.get("JWT_SECRET_KEY") or ""
    assert jwt_secret and jwt_secret != PLACEHOLDER_JWT_SECRET, (
        "JWT_SECRET_KEY is still the example placeholder -- generate a real random secret "
        "before Phase 2 (auth) work relies on it"
    )

    admin_emails = {e.strip().lower() for e in (env.get("ADMIN_EMAILS") or "").split(",") if e.strip()}
    assert admin_emails, "ADMIN_EMAILS is empty in backend/.env"
    assert not (admin_emails & PLACEHOLDER_ADMIN_EMAILS), (
        "ADMIN_EMAILS still contains placeholder addresses -- set the 3 real admin Google emails"
    )
