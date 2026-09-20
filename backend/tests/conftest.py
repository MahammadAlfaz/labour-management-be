import importlib
import os

import pytest
from mongomock_motor import AsyncMongoMockClient

os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "labour_management_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("ADMIN_EMAILS", "admin@example.com")

_REPOSITORY_MODULES = [
    "app.core.audit",
    "app.modules.admins.repository",
    "app.modules.labourers.repository",
    "app.modules.sites.repository",
    "app.modules.wages.repository",
    "app.modules.attendance.repository",
    "app.modules.expenses.repository",
    "app.modules.advances.repository",
    "app.modules.deductions.repository",
    "app.modules.adjustments.repository",
    "app.modules.payments.repository",
    "app.modules.wall_calculations.repository",
]


@pytest.fixture
async def mongo_db(monkeypatch):
    """An isolated in-memory Mongo database shared across repositories for one test.

    Patches get_database in every repository module so services that touch
    multiple collections (e.g. AttendanceService touching labourers, sites,
    wages, and work records) all see the same fake database. Also creates the
    real production indexes (including the unique ones) so "duplicate" tests
    exercise the actual DB-level constraint, not just an application-level
    pre-check that could race under concurrent writers.
    """
    import app.db as db_module

    db = AsyncMongoMockClient()["test_db"]
    monkeypatch.setattr(db_module, "get_database", lambda db=db: db)
    for module_path in _REPOSITORY_MODULES:
        module = importlib.import_module(module_path)
        monkeypatch.setattr(module, "get_database", lambda db=db: db)
    await db_module.ensure_indexes()
    return db
