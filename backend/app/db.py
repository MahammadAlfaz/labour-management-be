import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.mongodb_url)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    settings = get_settings()
    return get_client()[settings.mongodb_db_name]


async def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping() -> bool:
    await get_client().admin.command("ping")
    return True


async def ensure_indexes() -> None:
    """Create indexes required for business invariants and query performance.

    Safe to call on every startup: create_index is idempotent for an
    unchanged index definition.
    """
    db = get_database()

    await db.admins.create_index("google_sub", unique=True)
    await db.admins.create_index("email", unique=True)

    await db.labourers.create_index("status")

    await db.sites.create_index("status")

    await db.wage_history.create_index([("labourer_id", 1), ("effective_from", -1)])

    # Core invariant: one labourer can only have one work record per date.
    await db.daily_work_records.create_index(
        [("labourer_id", 1), ("work_date", 1)], unique=True
    )
    await db.daily_work_records.create_index([("site_id", 1), ("work_date", 1)])

    await db.travel_expenses.create_index("daily_work_record_id")

    await db.payments.create_index([("labourer_id", 1), ("period_end", -1)])
    await db.payments.create_index("idempotency_key", unique=True, sparse=True)

    await db.advances.create_index([("labourer_id", 1), ("given_at", -1)])
    await db.deductions.create_index([("labourer_id", 1), ("created_at", -1)])
    await db.adjustments.create_index([("labourer_id", 1), ("created_at", -1)])

    await db.audit_logs.create_index([("entity_type", 1), ("entity_id", 1), ("at", -1)])

    logger.info("MongoDB indexes ensured")
