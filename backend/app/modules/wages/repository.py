from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.money import from_decimal128, to_decimal128
from app.db import get_database
from app.modules.wages.schemas import WageOut


def _to_out(doc: dict) -> WageOut:
    return WageOut(
        id=str(doc["_id"]),
        labourer_id=doc["labourer_id"],
        daily_wage=from_decimal128(doc["daily_wage"]),
        effective_from=date.fromisoformat(doc["effective_from"]),
        created_by=doc["created_by"],
        created_at=doc["created_at"],
    )


class WageRepository:
    """Append-only: wage entries are never edited or deleted, only added."""

    def __init__(self) -> None:
        self._collection = get_database().wage_history

    async def create(
        self, *, labourer_id: str, daily_wage: Decimal, effective_from: date, admin_id: str
    ) -> WageOut:
        doc = {
            "labourer_id": labourer_id,
            "daily_wage": to_decimal128(daily_wage),
            "effective_from": effective_from.isoformat(),
            "created_by": admin_id,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def exists_for_effective_date(self, labourer_id: str, effective_from: date) -> bool:
        doc = await self._collection.find_one(
            {"labourer_id": labourer_id, "effective_from": effective_from.isoformat()}
        )
        return doc is not None

    async def list_for_labourer(self, labourer_id: str) -> list[WageOut]:
        cursor = self._collection.find({"labourer_id": labourer_id}).sort("effective_from", -1)
        return [_to_out(doc) async for doc in cursor]

    async def resolve_for_date(self, labourer_id: str, work_date: date) -> Decimal | None:
        doc = await self._collection.find_one(
            {"labourer_id": labourer_id, "effective_from": {"$lte": work_date.isoformat()}},
            sort=[("effective_from", -1)],
        )
        return from_decimal128(doc["daily_wage"]) if doc else None
