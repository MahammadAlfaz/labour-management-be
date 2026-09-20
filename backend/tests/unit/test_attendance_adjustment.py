from datetime import date

import pytest

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
from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import SiteCreate
from app.modules.sites.service import SiteService
from app.modules.wages.repository import WageRepository
from app.modules.wages.schemas import WageCreate
from app.modules.wages.service import WageService


@pytest.fixture
async def site_id(mongo_db):
    site = await SiteService(SiteRepository()).create(SiteCreate(name="Site A", location="Loc A"), "admin-1")
    return site.id


@pytest.fixture
async def labourer_with_wage(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Adjustment Test"), "admin-1"
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


async def _mark_full_day(attendance_service, labourer_id, site_id, work_date):
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=work_date), "admin-1"
    )
    return await attendance_service.update(
        assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1"
    )


async def test_full_day_record_sets_original_amount_equal_to_amount(
    attendance_service, labourer_with_wage, site_id
):
    record = await _mark_full_day(attendance_service, labourer_with_wage.id, site_id, date(2026, 2, 1))

    assert record.original_amount == 800
    assert record.amount == 800
    assert record.adjustment_reason is None
    assert record.adjusted_by is None


async def test_adjust_amount_preserves_original_amount(attendance_service, labourer_with_wage, site_id):
    record = await _mark_full_day(attendance_service, labourer_with_wage.id, site_id, date(2026, 2, 2))

    adjusted = await attendance_service.adjust_amount(
        record.id, AmountAdjustment(amount="750", reason="Left 2 hours early"), "admin-2"
    )

    assert adjusted.original_amount == 800  # unchanged
    assert adjusted.amount == 750
    assert adjusted.adjustment_reason == "Left 2 hours early"
    assert adjusted.adjusted_by == "admin-2"
    assert adjusted.adjusted_at is not None
    assert adjusted.status == AttendanceStatus.FULL_DAY  # status untouched


async def test_full_correction_clears_prior_adjustment(attendance_service, labourer_with_wage, site_id):
    record = await _mark_full_day(attendance_service, labourer_with_wage.id, site_id, date(2026, 2, 3))
    await attendance_service.adjust_amount(
        record.id, AmountAdjustment(amount="750", reason="Left early"), "admin-1"
    )

    corrected = await attendance_service.update(
        record.id, WorkRecordUpdate(status=AttendanceStatus.HALF_DAY, amount="400"), "admin-1"
    )

    assert corrected.original_amount == 400
    assert corrected.amount == 400
    assert corrected.adjustment_reason is None
    assert corrected.adjusted_by is None
