from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.core.money import to_decimal128
from app.modules.adjustments.service import AdjustmentService
from app.modules.attendance.repository import WorkRecordRepository
from app.modules.attendance.schemas import WorkRecordOut
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate


class ExpenseService:
    def __init__(
        self,
        repo: ExpenseRepository | None = None,
        work_record_repo: WorkRecordRepository | None = None,
        adjustment_service: AdjustmentService | None = None,
    ):
        self._repo = repo or ExpenseRepository()
        self._work_record_repo = work_record_repo or WorkRecordRepository()
        self._adjustment_service = adjustment_service or AdjustmentService()

    async def _get_work_record(self, record_id: str) -> WorkRecordOut:
        record = await self._work_record_repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Work record not found")
        return record

    async def _record_post_payment_difference(self, record: WorkRecordOut, delta, admin_id: str, reason: str) -> None:
        if record.payment_id is None or delta == 0:
            return
        await self._adjustment_service.record_correction(
            labourer_id=record.labourer_id,
            amount=delta,
            reason=reason,
            related_record_type="daily_work_record",
            related_record_id=record.id,
            admin_id=admin_id,
        )

    async def add(self, record_id: str, payload: ExpenseCreate, admin_id: str) -> ExpenseOut:
        record = await self._get_work_record(record_id)
        expense = await self._repo.create(
            daily_work_record_id=record_id,
            category=payload.category.value,
            amount=payload.amount,
            note=payload.note,
            admin_id=admin_id,
        )
        await self._record_post_payment_difference(
            record, expense.amount, admin_id, f"Expense added after payment: {expense.category}"
        )
        await record_audit_log(
            entity_type="travel_expense",
            entity_id=expense.id,
            action="create",
            admin_id=admin_id,
            after=expense.model_dump(mode="json"),
        )
        return expense

    async def list_for_record(self, record_id: str) -> list[ExpenseOut]:
        await self._get_work_record(record_id)
        return await self._repo.list_for_record(record_id)

    async def get(self, expense_id: str) -> ExpenseOut:
        expense = await self._repo.get_by_id(expense_id)
        if expense is None:
            raise NotFoundError("Expense not found")
        return expense

    async def update(
        self, record_id: str, expense_id: str, payload: ExpenseUpdate, admin_id: str
    ) -> ExpenseOut:
        before = await self.get(expense_id)
        if before.daily_work_record_id != record_id:
            raise NotFoundError("Expense not found for this work record")
        record = await self._get_work_record(record_id)

        updates = {
            k: v
            for k, v in payload.model_dump(mode="json", exclude_unset=True).items()
            if v is not None
        }
        if payload.amount is not None:
            # model_dump(mode="json") stringifies Decimal; the repository's
            # generic $set needs the actual BSON-encodable Decimal128.
            updates["amount"] = to_decimal128(payload.amount)
        updated = await self._repo.update(expense_id, updates=updates, admin_id=admin_id)

        if updated is not None and payload.amount is not None:
            await self._record_post_payment_difference(
                record,
                updated.amount - before.amount,
                admin_id,
                f"Expense amount changed after payment: {before.category}",
            )

        await record_audit_log(
            entity_type="travel_expense",
            entity_id=expense_id,
            action="update",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
            after=updated.model_dump(mode="json") if updated else None,
        )
        return updated  # type: ignore[return-value]

    async def delete(self, record_id: str, expense_id: str, admin_id: str) -> None:
        before = await self.get(expense_id)
        if before.daily_work_record_id != record_id:
            raise NotFoundError("Expense not found for this work record")
        record = await self._get_work_record(record_id)

        await self._repo.delete(expense_id)
        await self._record_post_payment_difference(
            record, -before.amount, admin_id, f"Expense removed after payment: {before.category}"
        )
        await record_audit_log(
            entity_type="travel_expense",
            entity_id=expense_id,
            action="delete",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
        )
