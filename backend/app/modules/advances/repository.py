from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.money import from_decimal128, to_decimal128, zero
from app.db import get_database
from app.modules.advances.schemas import AdvanceOut


def _to_out(doc: dict) -> AdvanceOut:
    return AdvanceOut(
        id=str(doc["_id"]),
        labourer_id=doc["labourer_id"],
        amount=from_decimal128(doc["amount"]),
        note=doc.get("note"),
        given_at=date.fromisoformat(doc["given_at"]),
        settled=doc["settled"],
        settled_in_payment_id=doc.get("settled_in_payment_id"),
        created_by=doc["created_by"],
        created_at=doc["created_at"],
    )


class AdvanceRepository:
    def __init__(self) -> None:
        self._collection = get_database().advances

    async def create(
        self, *, labourer_id: str, amount: Decimal, note: str | None, given_at: date, admin_id: str
    ) -> AdvanceOut:
        doc = {
            "labourer_id": labourer_id,
            "amount": to_decimal128(amount),
            "note": note,
            "given_at": given_at.isoformat(),
            "settled": False,
            "settled_in_payment_id": None,
            "created_by": admin_id,
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def list_for_labourer(self, labourer_id: str) -> list[AdvanceOut]:
        cursor = self._collection.find({"labourer_id": labourer_id}).sort(
            [("given_at", -1), ("_id", -1)]
        )
        return [_to_out(doc) async for doc in cursor]

    async def list_unsettled(self, labourer_id: str) -> list[AdvanceOut]:
        cursor = self._collection.find({"labourer_id": labourer_id, "settled": False})
        return [_to_out(doc) async for doc in cursor]

    async def sum_unsettled(self, labourer_id: str) -> Decimal:
        total = zero()
        for advance in await self.list_unsettled(labourer_id):
            total += advance.amount
        return total

    async def mark_settled(self, labourer_id: str, payment_id: str) -> None:
        await self._collection.update_many(
            {"labourer_id": labourer_id, "settled": False},
            {"$set": {"settled": True, "settled_in_payment_id": payment_id}},
        )
