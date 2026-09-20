from datetime import date, datetime, timezone
from decimal import Decimal

from bson import ObjectId

from app.core.money import from_decimal128, to_decimal128
from app.db import get_database
from app.modules.attendance.schemas import WorkRecordOut


def _to_out(doc: dict) -> WorkRecordOut:
    return WorkRecordOut(
        id=str(doc["_id"]),
        labourer_id=doc["labourer_id"],
        site_id=doc["site_id"],
        work_date=date.fromisoformat(doc["work_date"]),
        status=doc["status"],
        wage_snapshot=from_decimal128(doc.get("wage_snapshot")),
        original_amount=from_decimal128(doc["original_amount"]),
        amount=from_decimal128(doc["amount"]),
        adjustment_reason=doc.get("adjustment_reason"),
        adjusted_by=doc.get("adjusted_by"),
        adjusted_at=doc.get("adjusted_at"),
        payment_id=doc.get("payment_id"),
        created_by=doc["created_by"],
        updated_by=doc["updated_by"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class WorkRecordRepository:
    def __init__(self) -> None:
        self._collection = get_database().daily_work_records

    async def find_for_labourer_and_date(
        self, labourer_id: str, work_date: date
    ) -> WorkRecordOut | None:
        doc = await self._collection.find_one(
            {"labourer_id": labourer_id, "work_date": work_date.isoformat()}
        )
        return _to_out(doc) if doc else None

    async def assign(
        self,
        *,
        labourer_id: str,
        site_id: str,
        work_date: date,
        wage_snapshot: Decimal | None,
        admin_id: str,
    ) -> WorkRecordOut:
        """Create a pending record: assigned to a site/date, no attendance status yet."""
        now = datetime.now(timezone.utc)
        zero128 = to_decimal128(Decimal("0"))
        doc = {
            "labourer_id": labourer_id,
            "site_id": site_id,
            "work_date": work_date.isoformat(),
            "status": None,
            "wage_snapshot": to_decimal128(wage_snapshot) if wage_snapshot is not None else None,
            "original_amount": zero128,
            "amount": zero128,
            "adjustment_reason": None,
            "adjusted_by": None,
            "adjusted_at": None,
            "payment_id": None,
            "created_by": admin_id,
            "updated_by": admin_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def delete(self, record_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(record_id)})

    async def get_by_id(self, record_id: str) -> WorkRecordOut | None:
        if not ObjectId.is_valid(record_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(record_id)})
        return _to_out(doc) if doc else None

    async def update(
        self,
        record_id: str,
        *,
        status: str,
        wage_snapshot: Decimal | None,
        amount: Decimal,
        admin_id: str,
    ) -> WorkRecordOut | None:
        """Full correction: re-marks attendance, recomputing amounts from scratch.

        Clears any previous manual adjustment, since a fresh correction makes
        the old adjustment note stale (see adjust_amount for tweaking just
        the amount on an otherwise-correct record).
        """
        updates = {
            "status": status,
            "wage_snapshot": to_decimal128(wage_snapshot) if wage_snapshot is not None else None,
            "original_amount": to_decimal128(amount),
            "amount": to_decimal128(amount),
            "adjustment_reason": None,
            "adjusted_by": None,
            "adjusted_at": None,
            "updated_by": admin_id,
            "updated_at": datetime.now(timezone.utc),
        }
        await self._collection.update_one({"_id": ObjectId(record_id)}, {"$set": updates})
        return await self.get_by_id(record_id)

    async def adjust_amount(
        self, record_id: str, *, amount: Decimal, reason: str | None, admin_id: str
    ) -> WorkRecordOut | None:
        """Override just the amount, preserving original_amount and status."""
        now = datetime.now(timezone.utc)
        updates = {
            "amount": to_decimal128(amount),
            "adjustment_reason": reason,
            "adjusted_by": admin_id,
            "adjusted_at": now,
            "updated_by": admin_id,
            "updated_at": now,
        }
        await self._collection.update_one({"_id": ObjectId(record_id)}, {"$set": updates})
        return await self.get_by_id(record_id)

    async def clear_attendance(self, record_id: str, admin_id: str) -> WorkRecordOut | None:
        """Keep the site assignment but return it to the unmarked state."""
        updates = {
            "status": None,
            "original_amount": to_decimal128(Decimal("0")),
            "amount": to_decimal128(Decimal("0")),
            "adjustment_reason": None,
            "adjusted_by": None,
            "adjusted_at": None,
            "updated_by": admin_id,
            "updated_at": datetime.now(timezone.utc),
        }
        await self._collection.update_one({"_id": ObjectId(record_id)}, {"$set": updates})
        return await self.get_by_id(record_id)

    async def list_for_site_and_date(self, site_id: str, work_date: date) -> list[WorkRecordOut]:
        cursor = self._collection.find({"site_id": site_id, "work_date": work_date.isoformat()})
        return [_to_out(doc) async for doc in cursor]

    async def list_for_labourer_in_range(
        self, labourer_id: str, start: date, end: date
    ) -> list[WorkRecordOut]:
        cursor = self._collection.find(
            {
                "labourer_id": labourer_id,
                "work_date": {"$gte": start.isoformat(), "$lte": end.isoformat()},
            }
        ).sort("work_date", 1)
        return [_to_out(doc) async for doc in cursor]

    async def list_for_site_in_range(self, site_id: str, start: date, end: date) -> list[WorkRecordOut]:
        cursor = self._collection.find(
            {
                "site_id": site_id,
                "work_date": {"$gte": start.isoformat(), "$lte": end.isoformat()},
            }
        ).sort("work_date", 1)
        return [_to_out(doc) async for doc in cursor]

    async def list_unpaid_for_labourer_in_range(
        self, labourer_id: str, start: date, end: date
    ) -> list[WorkRecordOut]:
        cursor = self._collection.find(
            {
                "labourer_id": labourer_id,
                "payment_id": None,
                # Pending (unmarked) records have no finalized attendance yet and
                # must never be swept into a payment -- that would lock in a ₹0
                # earning for a day that should still be markable.
                "status": {"$ne": None},
                "work_date": {"$gte": start.isoformat(), "$lte": end.isoformat()},
            }
        )
        return [_to_out(doc) async for doc in cursor]

    async def mark_paid(self, record_ids: list[str], payment_id: str) -> None:
        if not record_ids:
            return
        await self._collection.update_many(
            {"_id": {"$in": [ObjectId(r) for r in record_ids]}},
            {"$set": {"payment_id": payment_id}},
        )
