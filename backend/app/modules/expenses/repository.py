from datetime import datetime, timezone
from decimal import Decimal

from bson import ObjectId

from app.core.money import from_decimal128, to_decimal128
from app.db import get_database
from app.modules.expenses.schemas import ExpenseOut


def _to_out(doc: dict) -> ExpenseOut:
    return ExpenseOut(
        id=str(doc["_id"]),
        daily_work_record_id=doc["daily_work_record_id"],
        category=doc["category"],
        amount=from_decimal128(doc["amount"]),
        note=doc.get("note"),
        created_by=doc["created_by"],
        updated_by=doc["updated_by"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class ExpenseRepository:
    def __init__(self) -> None:
        self._collection = get_database().travel_expenses

    async def create(
        self,
        *,
        daily_work_record_id: str,
        category: str,
        amount: Decimal,
        note: str | None,
        admin_id: str,
    ) -> ExpenseOut:
        now = datetime.now(timezone.utc)
        doc = {
            "daily_work_record_id": daily_work_record_id,
            "category": category,
            "amount": to_decimal128(amount),
            "note": note,
            "created_by": admin_id,
            "updated_by": admin_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def get_by_id(self, expense_id: str) -> ExpenseOut | None:
        if not ObjectId.is_valid(expense_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(expense_id)})
        return _to_out(doc) if doc else None

    async def list_for_record(self, daily_work_record_id: str) -> list[ExpenseOut]:
        cursor = self._collection.find({"daily_work_record_id": daily_work_record_id}).sort(
            "created_at", 1
        )
        return [_to_out(doc) async for doc in cursor]

    async def update(self, expense_id: str, *, updates: dict, admin_id: str) -> ExpenseOut | None:
        updates_with_meta = {
            **updates,
            "updated_by": admin_id,
            "updated_at": datetime.now(timezone.utc),
        }
        await self._collection.update_one({"_id": ObjectId(expense_id)}, {"$set": updates_with_meta})
        return await self.get_by_id(expense_id)

    async def delete(self, expense_id: str) -> None:
        await self._collection.delete_one({"_id": ObjectId(expense_id)})

    async def sum_for_record(self, daily_work_record_id: str) -> Decimal:
        expenses = await self.list_for_record(daily_work_record_id)
        total = Decimal("0.00")
        for expense in expenses:
            total += expense.amount
        return total
