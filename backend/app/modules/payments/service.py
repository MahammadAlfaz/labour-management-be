from datetime import date

from pymongo.errors import DuplicateKeyError

from app.core.audit import record_audit_log
from app.core.errors import ConflictError, NotFoundError
from app.core.money import to_money, zero
from app.modules.adjustments.repository import AdjustmentRepository
from app.modules.advances.repository import AdvanceRepository
from app.modules.attendance.repository import WorkRecordRepository
from app.modules.deductions.repository import DeductionRepository
from app.modules.expenses.repository import ExpenseRepository
from app.modules.labourers.repository import LabourerRepository
from app.modules.payments.repository import PaymentRepository
from app.modules.payments.schemas import (
    PaymentCreate,
    PaymentOut,
    PaymentPreview,
    PaymentSnapshot,
    PeriodType,
)


class PaymentService:
    """Computes a labourer's settlement position and records payments.

    A payment is immutable once created -- corrections after the fact never
    edit it; they flow through the adjustments ledger into the next payment
    (see AdjustmentService.record_correction, called from attendance/expenses
    services when a paid record changes).
    """

    def __init__(
        self,
        payment_repo: PaymentRepository | None = None,
        work_record_repo: WorkRecordRepository | None = None,
        expense_repo: ExpenseRepository | None = None,
        advance_repo: AdvanceRepository | None = None,
        deduction_repo: DeductionRepository | None = None,
        adjustment_repo: AdjustmentRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
    ):
        self._payment_repo = payment_repo or PaymentRepository()
        self._work_record_repo = work_record_repo or WorkRecordRepository()
        self._expense_repo = expense_repo or ExpenseRepository()
        self._advance_repo = advance_repo or AdvanceRepository()
        self._deduction_repo = deduction_repo or DeductionRepository()
        self._adjustment_repo = adjustment_repo or AdjustmentRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()

    async def preview(
        self, labourer_id: str, period_type: PeriodType, period_start: date, period_end: date
    ) -> PaymentPreview:
        if await self._labourer_repo.get_by_id(labourer_id) is None:
            raise NotFoundError("Labourer not found")

        unpaid_records = await self._work_record_repo.list_unpaid_for_labourer_in_range(
            labourer_id, period_start, period_end
        )
        wages = zero()
        travel_expenses = zero()
        record_ids = []
        for record in unpaid_records:
            expenses_total = await self._expense_repo.sum_for_record(record.id)
            wages += record.amount
            travel_expenses += expenses_total
            record_ids.append(record.id)

        earnings = to_money(wages + travel_expenses)

        unsettled_advances = await self._advance_repo.sum_unsettled(labourer_id)
        unsettled_deductions = await self._deduction_repo.sum_unsettled(labourer_id)
        adjustments = await self._adjustment_repo.list_unsettled(labourer_id)
        unsettled_adjustments = sum((adjustment.amount for adjustment in adjustments), start=zero())
        prior_balance = await self._payment_repo.sum_balance(labourer_id)

        suggested_amount = to_money(
            earnings
            - unsettled_advances
            - unsettled_deductions
            + unsettled_adjustments
            + prior_balance
        )

        return PaymentPreview(
            labourer_id=labourer_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            wages=wages,
            travel_expenses=travel_expenses,
            earnings=earnings,
            unsettled_advances=unsettled_advances,
            unsettled_deductions=unsettled_deductions,
            unsettled_adjustments=unsettled_adjustments,
            prior_balance=prior_balance,
            suggested_amount=suggested_amount,
            unpaid_work_record_ids=record_ids,
            adjustments=adjustments,
        )

    async def create_payment(
        self, payload: PaymentCreate, admin_id: str, idempotency_key: str | None
    ) -> PaymentOut:
        if idempotency_key:
            existing = await self._payment_repo.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing

        preview = await self.preview(
            payload.labourer_id, payload.period_type, payload.period_start, payload.period_end
        )

        paid_amount = to_money(payload.paid_amount)
        if paid_amount != preview.suggested_amount and not payload.adjustment_reason:
            raise ConflictError(
                "A reason is required when the paid amount differs from the suggested amount"
            )

        if paid_amount == preview.suggested_amount:
            status = "paid"
        elif paid_amount < preview.suggested_amount:
            status = "partial"
        else:
            status = "overpaid"

        snapshot = PaymentSnapshot(
            wages=preview.wages,
            travel_expenses=preview.travel_expenses,
            earnings=preview.earnings,
            unsettled_advances=preview.unsettled_advances,
            unsettled_deductions=preview.unsettled_deductions,
            unsettled_adjustments=preview.unsettled_adjustments,
            prior_balance=preview.prior_balance,
            suggested_amount=preview.suggested_amount,
        )

        try:
            payment = await self._payment_repo.create(
                labourer_id=payload.labourer_id,
                period_type=payload.period_type.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                snapshot=snapshot,
                paid_amount=paid_amount,
                adjustment_reason=payload.adjustment_reason,
                status=status,
                admin_id=admin_id,
                idempotency_key=idempotency_key,
            )
        except DuplicateKeyError:
            # Concurrent retry with the same key raced us -- return the winner's record.
            existing = await self._payment_repo.find_by_idempotency_key(idempotency_key)  # type: ignore[arg-type]
            if existing is not None:
                return existing
            raise

        await self._work_record_repo.mark_paid(preview.unpaid_work_record_ids, payment.id)
        await self._advance_repo.mark_settled(payload.labourer_id, payment.id)
        await self._deduction_repo.mark_settled(payload.labourer_id, payment.id)
        await self._adjustment_repo.mark_settled(payload.labourer_id, payment.id)

        await record_audit_log(
            entity_type="payment",
            entity_id=payment.id,
            action="create",
            admin_id=admin_id,
            after=payment.model_dump(mode="json"),
        )
        return payment

    async def list_for_labourer(self, labourer_id: str) -> list[PaymentOut]:
        return await self._payment_repo.list_for_labourer(labourer_id)
