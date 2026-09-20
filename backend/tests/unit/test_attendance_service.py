from datetime import date

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.modules.attendance.repository import WorkRecordRepository
from app.modules.attendance.schemas import (
    AmountAdjustment,
    AttendanceStatus,
    WorkRecordAssign,
    WorkRecordUpdate,
)
from app.modules.attendance.service import AttendanceService
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate
from app.modules.labourers.service import LabourerService
from app.modules.payments.schemas import PaymentCreate, PeriodType
from app.modules.payments.service import PaymentService
from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import SiteCreate
from app.modules.sites.service import SiteService
from app.modules.wages.repository import WageRepository
from app.modules.wages.schemas import WageCreate
from app.modules.wages.service import WageService


@pytest.fixture
async def two_sites(mongo_db):
    service = SiteService(SiteRepository())
    site_a = await service.create(SiteCreate(name="Site A", location="Loc A"), "admin-1")
    site_b = await service.create(SiteCreate(name="Site B", location="Loc B"), "admin-1")
    return site_a, site_b


@pytest.fixture
async def labourer_with_wage(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Attendance Test"), "admin-1"
    )
    await WageService(WageRepository(), LabourerRepository()).add_wage(
        labourer.id, WageCreate(daily_wage="800", effective_from=date(2026, 1, 1)), "admin-1"
    )
    return labourer


@pytest.fixture
def attendance_service(mongo_db):
    return AttendanceService(
        WorkRecordRepository(),
        LabourerRepository(),
        SiteRepository(),
        WageService(WageRepository(), LabourerRepository()),
    )


async def _mark(attendance_service, labourer_id, site_id, work_date, status, amount=None):
    """Assign then mark attendance in one helper, for tests that only care about the outcome."""
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=work_date), "admin-1"
    )
    return await attendance_service.update(
        assigned.id, WorkRecordUpdate(status=status, amount=amount), "admin-1"
    )


async def test_assign_creates_pending_record_with_no_status(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, _ = two_sites

    record = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)),
        "admin-1",
    )

    assert record.status is None
    assert record.amount == 0


async def test_cannot_assign_same_labourer_twice_same_date(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, site_b = two_sites
    await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)),
        "admin-1",
    )

    with pytest.raises(ConflictError):
        await attendance_service.assign(
            WorkRecordAssign(
                labourer_id=labourer_with_wage.id, site_id=site_b.id, work_date=date(2026, 2, 1)
            ),
            "admin-1",
        )


async def test_cannot_assign_to_a_closed_site(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    await SiteService(SiteRepository()).set_active(site_a.id, False, "admin-1")

    with pytest.raises(ConflictError, match="closed"):
        await attendance_service.assign(
            WorkRecordAssign(
                labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)
            ),
            "admin-1",
        )


async def test_cannot_assign_an_inactive_labourer(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    await LabourerService(LabourerRepository()).set_active(labourer_with_wage.id, False, "admin-1")

    with pytest.raises(ConflictError, match="inactive"):
        await attendance_service.assign(
            WorkRecordAssign(
                labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)
            ),
            "admin-1",
        )


async def test_unassign_removes_pending_record(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    record = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)),
        "admin-1",
    )

    await attendance_service.unassign(record.id, "admin-1")

    assert await attendance_service._repo.get_by_id(record.id) is None


async def test_can_remove_marked_attendance_if_not_yet_paid(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    record = await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 1), AttendanceStatus.FULL_DAY
    )

    await attendance_service.unassign(record.id, "admin-1")

    assert await attendance_service._repo.get_by_id(record.id) is None


async def test_cannot_remove_a_paid_record(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    record = await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 1), AttendanceStatus.FULL_DAY
    )
    await PaymentService().create_payment(
        PaymentCreate(
            labourer_id=labourer_with_wage.id,
            period_type=PeriodType.DAILY,
            period_start=date(2026, 2, 1),
            period_end=date(2026, 2, 1),
            paid_amount="800",
        ),
        "admin-1",
        idempotency_key="remove-test-pay-1",
    )

    with pytest.raises(ConflictError):
        await attendance_service.unassign(record.id, "admin-1")


async def test_full_day_auto_resolves_wage(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites

    record = await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 1), AttendanceStatus.FULL_DAY
    )

    assert record.amount == 800
    assert record.wage_snapshot == 800


async def test_full_day_without_wage_history_is_rejected(attendance_service, two_sites):
    site_a, _ = two_sites
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="No Wage"), "admin-1"
    )

    with pytest.raises(ConflictError):
        await _mark(attendance_service, labourer.id, site_a.id, date(2026, 2, 1), AttendanceStatus.FULL_DAY)


async def test_half_day_requires_manual_amount(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites

    with pytest.raises(ConflictError):
        await _mark(
            attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 1), AttendanceStatus.HALF_DAY
        )

    record = await _mark(
        attendance_service,
        labourer_with_wage.id,
        site_a.id,
        date(2026, 2, 2),
        AttendanceStatus.HALF_DAY,
        amount="350",
    )

    assert record.amount == 350
    # wage_snapshot stays informational (the day's rate), it never derives the half-day amount
    assert record.wage_snapshot == 800


async def test_half_day_rejects_zero_or_negative_amount(attendance_service, labourer_with_wage, two_sites):
    site_a, _ = two_sites
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_with_wage.id, site_id=site_a.id, work_date=date(2026, 2, 1)),
        "admin-1",
    )

    with pytest.raises(ConflictError, match="greater than zero"):
        await attendance_service.update(
            assigned.id, WorkRecordUpdate(status=AttendanceStatus.HALF_DAY, amount="0"), "admin-1"
        )

    with pytest.raises(ConflictError, match="greater than zero"):
        await attendance_service.update(
            assigned.id, WorkRecordUpdate(status=AttendanceStatus.HALF_DAY, amount="-100"), "admin-1"
        )


async def test_absent_defaults_to_zero_regardless_of_submitted_amount(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, _ = two_sites

    record = await _mark(
        attendance_service,
        labourer_with_wage.id,
        site_a.id,
        date(2026, 2, 3),
        AttendanceStatus.ABSENT,
        amount="9999",
    )

    assert record.amount == 0


async def test_labourer_cannot_work_two_sites_same_date(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, site_b = two_sites

    await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 4), AttendanceStatus.FULL_DAY
    )

    with pytest.raises(ConflictError):
        await attendance_service.assign(
            WorkRecordAssign(
                labourer_id=labourer_with_wage.id, site_id=site_b.id, work_date=date(2026, 2, 4)
            ),
            "admin-1",
        )


async def test_future_wage_change_does_not_affect_past_record(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, _ = two_sites

    record = await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 5), AttendanceStatus.FULL_DAY
    )
    assert record.amount == 800

    await WageService(WageRepository(), LabourerRepository()).add_wage(
        labourer_with_wage.id,
        WageCreate(daily_wage="1000", effective_from=date(2026, 3, 1)),
        "admin-1",
    )

    unchanged = await attendance_service._repo.get_by_id(record.id)
    assert unchanged is not None
    assert unchanged.amount == 800


async def test_board_only_shows_this_sites_crew(attendance_service, labourer_with_wage, two_sites):
    site_a, site_b = two_sites

    await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 6), AttendanceStatus.FULL_DAY
    )

    board_a = await attendance_service.get_board(site_a.id, date(2026, 2, 6))
    board_b = await attendance_service.get_board(site_b.id, date(2026, 2, 6))

    assert len(board_a) == 1
    assert board_a[0].labourer_id == labourer_with_wage.id
    assert board_b == []


async def test_search_available_labourers_flags_those_assigned_elsewhere(
    attendance_service, labourer_with_wage, two_sites
):
    site_a, site_b = two_sites

    await _mark(
        attendance_service, labourer_with_wage.id, site_a.id, date(2026, 2, 6), AttendanceStatus.FULL_DAY
    )

    results = await attendance_service.search_available_labourers(date(2026, 2, 6), None)
    entry = next(r for r in results if r.labourer_id == labourer_with_wage.id)

    assert entry.unavailable_reason == f"Already assigned to {site_a.name} today"

    unrelated_day = await attendance_service.search_available_labourers(date(2026, 2, 7), None)
    entry_other_day = next(r for r in unrelated_day if r.labourer_id == labourer_with_wage.id)
    assert entry_other_day.unavailable_reason is None


UNKNOWN_RECORD_ID = "507f1f77bcf86cd799439011"


async def test_get_detail_unknown_record_raises_not_found(attendance_service):
    with pytest.raises(NotFoundError):
        await attendance_service.get_detail(UNKNOWN_RECORD_ID)


async def test_update_unknown_record_raises_not_found(attendance_service):
    with pytest.raises(NotFoundError):
        await attendance_service.update(
            UNKNOWN_RECORD_ID, WorkRecordUpdate(status=AttendanceStatus.ABSENT), "admin-1"
        )


async def test_unassign_unknown_record_raises_not_found(attendance_service):
    with pytest.raises(NotFoundError):
        await attendance_service.unassign(UNKNOWN_RECORD_ID, "admin-1")


async def test_adjust_amount_unknown_record_raises_not_found(attendance_service):
    with pytest.raises(NotFoundError):
        await attendance_service.adjust_amount(
            UNKNOWN_RECORD_ID, AmountAdjustment(amount="100"), "admin-1"
        )


async def test_assign_unknown_labourer_raises_not_found(attendance_service, two_sites):
    site_a, _ = two_sites
    with pytest.raises(NotFoundError):
        await attendance_service.assign(
            WorkRecordAssign(labourer_id=UNKNOWN_RECORD_ID, site_id=site_a.id, work_date=date(2026, 2, 1)),
            "admin-1",
        )


async def test_assign_unknown_site_raises_not_found(attendance_service, labourer_with_wage):
    with pytest.raises(NotFoundError):
        await attendance_service.assign(
            WorkRecordAssign(
                labourer_id=labourer_with_wage.id, site_id=UNKNOWN_RECORD_ID, work_date=date(2026, 2, 1)
            ),
            "admin-1",
        )


async def test_get_board_unknown_site_raises_not_found(attendance_service):
    with pytest.raises(NotFoundError):
        await attendance_service.get_board(UNKNOWN_RECORD_ID, date(2026, 2, 1))
