from datetime import datetime, timezone
from decimal import Decimal

from bson import ObjectId

from app.core.money import from_decimal128, to_decimal128, zero
from app.db import get_database
from app.modules.adjustments.schemas import AdjustmentOut


def _to_out(doc: dict) -> AdjustmentOut:
    return AdjustmentOut(
        id=str(doc["_id"]),
        labourer_id=doc["labourer_id"],
        amount=from_decimal128(doc["amount"]),
        reason=doc["reason"],
        related_record_type=doc.get("related_record_type"),
        related_record_id=doc.get("related_record_id"),
        settled=doc["settled"],
        settled_in_payment_id=doc.get("settled_in_payment_id"),
        created_by=doc["created_by"],
        created_at=doc["created_at"],
    )


class AdjustmentRepository:
    def __init__(self) -> None:
        self._collection = get_database().adjustments

    async def create(
        self,
        *,
        labourer_id: str,
        amount: Decimal,
        reason: str,
        admin_id: str,
        related_record_type: str | None = None,
        related_record_id: str | None = None,
    ) -> AdjustmentOut:
        doc = {
            "labourer_id": labourer_id,
            "amount": to_decimal128(amount),
            "reason": reason,
            "related_record_type": related_record_type,
            "related_record_id": related_record_id,
            "settled": False,
            "settled_in_payment_id": None,
            "created_by": admin_id,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def list_for_labourer(self, labourer_id: str) -> list[AdjustmentOut]:
        cursor = self._collection.find({"labourer_id": labourer_id}).sort("created_at", -1)
        return [_to_out(doc) async for doc in cursor]

    async def list_unsettled(self, labourer_id: str) -> list[AdjustmentOut]:
        cursor = self._collection.find({"labourer_id": labourer_id, "settled": False})
        return [_to_out(doc) async for doc in cursor]

    async def sum_unsettled(self, labourer_id: str) -> Decimal:
        total = zero()
        for adjustment in await self.list_unsettled(labourer_id):
            total += adjustment.amount
        return total

    async def mark_settled(self, labourer_id: str, payment_id: str) -> None:
        await self._collection.update_many(
            {"labourer_id": labourer_id, "settled": False},
            {"$set": {"settled": True, "settled_in_payment_id": payment_id}},
        )

    async def get_by_id(self, adjustment_id: str) -> AdjustmentOut | None:
        if not ObjectId.is_valid(adjustment_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(adjustment_id)})
        return _to_out(doc) if doc else None
