import pytest
from mongomock_motor import AsyncMongoMockClient

from app.modules.admins import repository as admin_repository_module
from app.modules.admins.repository import AdminRepository


@pytest.fixture
def admin_repo(monkeypatch):
    db = AsyncMongoMockClient()["test_admins"]
    monkeypatch.setattr(admin_repository_module, "get_database", lambda: db)
    return AdminRepository()


async def test_create_and_find_by_google_sub(admin_repo):
    created = await admin_repo.create(google_sub="sub-1", email="Admin@Example.com", name="Admin One")

    found = await admin_repo.find_by_google_sub("sub-1")

    assert found is not None
    assert found.id == created.id
    assert found.email == "admin@example.com"


async def test_find_by_email_is_case_insensitive(admin_repo):
    await admin_repo.create(google_sub="sub-2", email="person@example.com", name="Person")

    found = await admin_repo.find_by_email("PERSON@example.com")

    assert found is not None


async def test_get_by_id_returns_none_for_invalid_id(admin_repo):
    assert await admin_repo.get_by_id("not-an-object-id") is None


async def test_set_active_deactivates_admin(admin_repo):
    created = await admin_repo.create(google_sub="sub-3", email="deactivate@example.com", name="X")

    await admin_repo.set_active(created.id, False)

    found = await admin_repo.get_by_id(created.id)
    assert found is not None
    assert found.is_active is False
