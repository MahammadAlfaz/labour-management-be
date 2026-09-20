from datetime import date
from decimal import Decimal

from pymongo.errors import DuplicateKeyError

from app.core.audit import record_audit_log
from app.core.errors import ConflictError, NotFoundError
from app.core.money import to_money, zero
from app.modules.adjustments.service import AdjustmentService
from app.modules.attendance.repository import WorkRecordRepository
from app.modules.attendance.schemas import (
    AmountAdjustment,
    AttendanceStatus,
    AvailableLabourer,
    LabourerBoardEntry,
    WorkRecordAssign,
    WorkRecordDetail,
    WorkRecordOut,
    WorkRecordUpdate,
)
from app.modules.expenses.repository import ExpenseRepository
from app.modules.labourers.repository import LabourerRepository
from app.modules.sites.repository import SiteRepository
from app.modules.wages.service import WageService


class AttendanceService:
    """Site assignment and attendance marking are two explicit steps on the
    same record: `assign` creates it with status=None (assigned, unmarked);
    `update` sets the actual attendance status/amount. Keeping both on one
    record (rather than two collections) means there's nothing to keep in
    sync -- a labourer has at most one record per work_date, enforced here
    for a friendly error and by a unique DB index as the hard guarantee
    against concurrent duplicate writes.
    """

    def __init__(
        self,
        repo: WorkRecordRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
        site_repo: SiteRepository | None = None,
        wage_service: WageService | None = None,
        expense_repo: ExpenseRepository | None = None,
        adjustment_service: AdjustmentService | None = None,
    ):
        self._repo = repo or WorkRecordRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()
        self._site_repo = site_repo or SiteRepository()
        self._wage_service = wage_service or WageService()
        self._expense_repo = expense_repo or ExpenseRepository()
        self._adjustment_service = adjustment_service or AdjustmentService()

    async def _record_post_payment_difference(
        self, existing: WorkRecordOut, new_amount: Decimal, admin_id: str, reason: str
    ) -> None:
        if existing.payment_id is None:
            return
        delta = new_amount - existing.amount
        if delta == 0:
            return
        await self._adjustment_service.record_correction(
            labourer_id=existing.labourer_id,
            amount=delta,
            reason=reason,
            related_record_type="daily_work_record",
            related_record_id=existing.id,
            admin_id=admin_id,
        )

    async def _resolve_amount_and_snapshot(
        self,
        labourer_id: str,
        work_date: date,
        status: AttendanceStatus,
        submitted_amount: Decimal | None,
    ) -> tuple[Decimal | None, Decimal]:
        wage_snapshot = await self._wage_service.resolve_for_date(labourer_id, work_date)

        if status == AttendanceStatus.ABSENT:
            return wage_snapshot, zero()

        if status == AttendanceStatus.FULL_DAY:
            if wage_snapshot is None:
                raise ConflictError(
                    "No wage has been set for this labourer yet -- "
                    "add a wage before recording FULL_DAY attendance"
                )
            return wage_snapshot, wage_snapshot

        # HALF_DAY: never auto-derived (e.g. as 50%) -- always manually entered.
        if submitted_amount is None:
            raise ConflictError("HALF_DAY attendance requires a manually entered amount")
        return wage_snapshot, to_money(submitted_amount)

    async def assign(self, payload: WorkRecordAssign, admin_id: str) -> WorkRecordOut:
        labourer = await self._labourer_repo.get_by_id(payload.labourer_id)
        if labourer is None:
            raise NotFoundError("Labourer not found")
        if labourer.status != "active":
            raise ConflictError(
                f"{labourer.name} is inactive and cannot be assigned -- reactivate them first"
            )
        site = await self._site_repo.get_by_id(payload.site_id)
        if site is None:
            raise NotFoundError("Site not found")
        if site.status != "active":
            raise ConflictError("This site is closed and cannot receive new assignments")

        existing = await self._repo.find_for_labourer_and_date(
            payload.labourer_id, payload.work_date
        )
        if existing is not None:
            other_site = await self._site_repo.get_by_id(existing.site_id)
            site_name = other_site.name if other_site else "another site"
            raise ConflictError(f"{labourer.name} is already assigned to {site_name} on this date")

        # Best-effort: shown on the card for context, but assignment doesn't
        # require a wage to exist yet -- that's only enforced when marking
        # FULL_DAY attendance.
        wage_snapshot = await self._wage_service.resolve_for_date(
            payload.labourer_id, payload.work_date
        )

        try:
            record = await self._repo.assign(
                labourer_id=payload.labourer_id,
                site_id=payload.site_id,
                work_date=payload.work_date,
                wage_snapshot=wage_snapshot,
                admin_id=admin_id,
            )
        except DuplicateKeyError as exc:
            raise ConflictError(f"{labourer.name} is already assigned for this date") from exc

        await record_audit_log(
            entity_type="daily_work_record",
            entity_id=record.id,
            action="assign",
            admin_id=admin_id,
            after=record.model_dump(mode="json"),
        )
        return record

    async def unassign(self, record_id: str, admin_id: str) -> None:
        """Remove a labourer from a day entirely -- a pending assignment or an
        already-marked (but not yet paid) attendance record.

        Once a record has been paid, it can no longer be deleted: that would
        erase the historical basis for money already recorded as paid. A
        correction at that point must go through `update`/`adjust_amount`,
        which raise an adjustment ledger entry instead of touching the past.
        """
        existing = await self._repo.get_by_id(record_id)
        if existing is None:
            raise NotFoundError("Work record not found")
        if existing.payment_id is not None:
            raise ConflictError(
                "This record has already been paid -- correct the attendance or amount instead of removing it"
            )

        await self._repo.delete(record_id)
        await record_audit_log(
            entity_type="daily_work_record",
            entity_id=record_id,
            action="remove" if existing.status is not None else "unassign",
            admin_id=admin_id,
            before=existing.model_dump(mode="json"),
        )

    async def clear_attendance(self, record_id: str, admin_id: str) -> WorkRecordOut:
        """Clear a non-paid attendance result without removing the site assignment."""
        existing = await self._repo.get_by_id(record_id)
        if existing is None:
            raise NotFoundError("Work record not found")
        if existing.status is None:
            raise ConflictError("Attendance has not been marked yet")
        if existing.payment_id is not None:
            raise ConflictError(
                "This attendance has already been paid -- correct it instead of clearing it"
            )

        cleared = await self._repo.clear_attendance(record_id, admin_id)
        await record_audit_log(
            entity_type="daily_work_record",
            entity_id=record_id,
            action="clear_attendance",
            admin_id=admin_id,
            before=existing.model_dump(mode="json"),
            after=cleared.model_dump(mode="json") if cleared else None,
        )
        return cleared  # type: ignore[return-value]

    async def update(self, record_id: str, payload: WorkRecordUpdate, admin_id: str) -> WorkRecordOut:
        existing = await self._repo.get_by_id(record_id)
        if existing is None:
            raise NotFoundError("Work record not found")

        wage_snapshot, amount = await self._resolve_amount_and_snapshot(
            existing.labourer_id, existing.work_date, payload.status, payload.amount
        )

        await self._record_post_payment_difference(
            existing, amount, admin_id, "Attendance correction after payment"
        )

        updated = await self._repo.update(
            record_id,
            status=payload.status.value,
            wage_snapshot=wage_snapshot,
            amount=amount,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="daily_work_record",
            entity_id=record_id,
            action="mark_attendance" if existing.status is None else "update",
            admin_id=admin_id,
            before=existing.model_dump(mode="json"),
            after=updated.model_dump(mode="json") if updated else None,
        )
        return updated  # type: ignore[return-value]

    async def get_detail(self, record_id: str) -> WorkRecordDetail:
        record = await self._repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Work record not found")

        expenses = await self._expense_repo.list_for_record(record_id)
        total_earnings = record.amount + sum((e.amount for e in expenses), start=to_money(0))

        return WorkRecordDetail(**record.model_dump(), expenses=expenses, total_earnings=total_earnings)

    async def adjust_amount(
        self, record_id: str, payload: AmountAdjustment, admin_id: str
    ) -> WorkRecordOut:
        """Manually override a record's amount (e.g. a full-day wage adjustment).

        Preserves original_amount and status; only the effective amount and
        the adjustment audit trail (reason, admin, timestamp) change. Use
        `update` instead for a full attendance correction (status change).
        """
        existing = await self._repo.get_by_id(record_id)
        if existing is None:
            raise NotFoundError("Work record not found")

        new_amount = to_money(payload.amount)
        await self._record_post_payment_difference(
            existing,
            new_amount,
            admin_id,
            payload.reason or "Amount adjustment after payment",
        )

        updated = await self._repo.adjust_amount(
            record_id, amount=new_amount, reason=payload.reason, admin_id=admin_id
        )
        await record_audit_log(
            entity_type="daily_work_record",
            entity_id=record_id,
            action="adjust_amount",
            admin_id=admin_id,
            before=existing.model_dump(mode="json"),
            after=updated.model_dump(mode="json") if updated else None,
        )
        return updated  # type: ignore[return-value]

    async def get_board(self, site_id: str, work_date: date) -> list[LabourerBoardEntry]:
        """Today's crew for this site: only labourers assigned and/or marked here."""
        if await self._site_repo.get_by_id(site_id) is None:
            raise NotFoundError("Site not found")

        records = await self._repo.list_for_site_and_date(site_id, work_date)

        entries: list[LabourerBoardEntry] = []
        for record in records:
            labourer = await self._labourer_repo.get_by_id(record.labourer_id)
            entries.append(
                LabourerBoardEntry(
                    labourer_id=record.labourer_id,
                    labourer_name=labourer.name if labourer else "Unknown labourer",
                    record=record,
                )
            )
        return entries

    async def search_available_labourers(
        self, work_date: date, search: str | None
    ) -> list[AvailableLabourer]:
        """Active labourers for the '+ Add labourer' picker.

        Everyone matching the search shows up, but anyone already
        assigned/marked elsewhere that date is flagged (not hidden), so the
        admin understands why they can't be added rather than wondering
        where they went.
        """
        labourers = await self._labourer_repo.list(status="active", search=search)

        results: list[AvailableLabourer] = []
        for labourer in labourers:
            existing = await self._repo.find_for_labourer_and_date(labourer.id, work_date)
            unavailable_reason = None
            if existing is not None:
                site = await self._site_repo.get_by_id(existing.site_id)
                site_name = site.name if site else "another site"
                unavailable_reason = f"Already assigned to {site_name} today"
            results.append(
                AvailableLabourer(
                    labourer_id=labourer.id,
                    labourer_name=labourer.name,
                    unavailable_reason=unavailable_reason,
                )
            )
        return results
