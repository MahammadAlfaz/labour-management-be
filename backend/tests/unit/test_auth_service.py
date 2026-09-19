import pytest
from mongomock_motor import AsyncMongoMockClient

from app.config import get_settings
from app.core.errors import ForbiddenError
from app.modules.admins import repository as admin_repository_module
from app.modules.admins.repository import AdminRepository
from app.modules.auth import service as auth_service_module
from app.modules.auth.service import AuthService


@pytest.fixture
def admin_repo(monkeypatch):
    db = AsyncMongoMockClient()["test_auth"]
    monkeypatch.setattr(admin_repository_module, "get_database", lambda: db)
    return AdminRepository()


def _fake_claims(email: str, sub: str = "google-sub-1", email_verified: bool = True) -> dict:
    return {"email": email, "sub": sub, "email_verified": email_verified, "name": "Test Admin"}


def _mock_google_verify(monkeypatch, claims: dict) -> None:
    monkeypatch.setattr(
        auth_service_module.google_id_token,
        "verify_oauth2_token",
        lambda *args, **kwargs: claims,
    )


async def test_bootstrap_admin_is_created_on_first_login(admin_repo, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_emails", "boss@example.com")
    _mock_google_verify(monkeypatch, _fake_claims("boss@example.com"))

    admin, access_token, refresh_token = await AuthService(admin_repo).authenticate_with_google(
        "fake-id-token"
    )

    assert admin.email == "boss@example.com"
    assert access_token and refresh_token


async def test_second_login_reuses_existing_admin_record(admin_repo, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_emails", "boss@example.com")
    _mock_google_verify(monkeypatch, _fake_claims("boss@example.com"))

    first, _, _ = await AuthService(admin_repo).authenticate_with_google("token-1")
    second, _, _ = await AuthService(admin_repo).authenticate_with_google("token-2")

    assert first.id == second.id
    assert len(await admin_repo.list_all()) == 1


async def test_unlisted_email_is_rejected(admin_repo, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_emails", "boss@example.com")
    _mock_google_verify(monkeypatch, _fake_claims("stranger@example.com"))

    with pytest.raises(ForbiddenError):
        await AuthService(admin_repo).authenticate_with_google("fake-id-token")

    assert await admin_repo.list_all() == []


async def test_deactivated_admin_is_rejected(admin_repo, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "admin_emails", "boss@example.com")
    created = await admin_repo.create(google_sub="google-sub-1", email="boss@example.com", name="Boss")
    await admin_repo.set_active(created.id, False)
    _mock_google_verify(monkeypatch, _fake_claims("boss@example.com"))

    with pytest.raises(ForbiddenError):
        await AuthService(admin_repo).authenticate_with_google("fake-id-token")
