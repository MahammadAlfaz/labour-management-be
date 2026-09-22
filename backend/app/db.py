import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import OperationFailure

from app.config import get_settings

logger = logging.getLogger(__name__)

_INDEX_OPTION_CONFLICT_CODES = {85, 86}  # IndexOptionsConflict, IndexKeySpecsConflict


def _is_index_conflict(exc: OperationFailure) -> bool:
    # Real MongoDB sets .code to 85/86; mongomock-motor (used in tests)
    # leaves .code unset and only differs by message text, so check both.
    return exc.code in _INDEX_OPTION_CONFLICT_CODES or "already exists" in str(exc)


async def _create_index(collection: AsyncIOMotorCollection, keys, **kwargs) -> None:
    """Create an index, migrating in place if an index on the same keys
    already exists with different options (e.g. adding unique=True to an
    index that was previously non-unique) -- create_index alone rejects
    that as a name conflict instead of altering the existing index.
    """
    try:
        await collection.create_index(keys, **kwargs)
        return
    except OperationFailure as exc:
        if not _is_index_conflict(exc):
            raise

    normalized_keys = [(keys, 1)] if isinstance(keys, str) else list(keys)
    async for existing in collection.list_indexes():
        if list(existing["key"].items()) == normalized_keys:
            await collection.drop_index(existing["name"])
            break
    await collection.create_index(keys, **kwargs)

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

    await _create_index(db.admins, "google_sub", unique=True)
    await _create_index(db.admins, "email", unique=True)

    await _create_index(db.labourers, "status")

    await _create_index(db.sites, "status")
    await _create_index(db.site_client_receipts, [("site_id", 1), ("received_on", -1)])
    await _create_index(db.site_expenses, [("site_id", 1), ("expense_date", -1)])

    await _create_index(db.wage_history, [("labourer_id", 1), ("effective_from", -1)], unique=True)

    # Core invariant: one labourer can only have one work record per date.
    await _create_index(db.daily_work_records, [("labourer_id", 1), ("work_date", 1)], unique=True)
    await _create_index(db.daily_work_records, [("site_id", 1), ("work_date", 1)])

    await _create_index(db.travel_expenses, "daily_work_record_id")

    await _create_index(db.payments, [("labourer_id", 1), ("period_end", -1)])
    await _create_index(db.payments, "idempotency_key", unique=True, sparse=True)

    await _create_index(db.advances, [("labourer_id", 1), ("given_at", -1)])
    await _create_index(db.deductions, [("labourer_id", 1), ("created_at", -1)])
    await _create_index(db.adjustments, [("labourer_id", 1), ("created_at", -1)])

    await _create_index(db.audit_logs, [("entity_type", 1), ("entity_id", 1), ("at", -1)])

    await _create_index(db.wall_calculations, [("site_id", 1), ("created_at", -1)])
    await _create_index(db.wall_calculations, "created_at")

    logger.info("MongoDB indexes ensured")
