from datetime import date

import pytest

from app.modules.attendance.repository import WorkRecordRepository
from app.modules.attendance.schemas import AttendanceStatus, WorkRecordAssign, WorkRecordUpdate
from app.modules.attendance.service import AttendanceService
from app.modules.chat import tools
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
async def labourer_id(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(LabourerCreate(name="Tool Test"), "admin-1")
    await WageService(WageRepository(), LabourerRepository()).add_wage(
        labourer.id, WageCreate(daily_wage="800", effective_from=date(2026, 1, 1)), "admin-1"
    )
    return labourer.id


@pytest.fixture
async def site_id(mongo_db):
    site = await SiteService(SiteRepository()).create(SiteCreate(name="Tool Site", location="Loc"), "admin-1")
    return site.id


async def test_list_labourers_returns_serializable_dict(mongo_db, labourer_id):
    result = await tools.list_labourers()

    assert result["total_count"] == 1
    assert result["truncated"] is False
    assert result["labourers"][0]["id"] == labourer_id
    assert result["labourers"][0]["name"] == "Tool Test"


async def test_list_labourers_filters_by_search(mongo_db, labourer_id):
    result = await tools.list_labourers(search="nonexistent")

    assert result["labourers"] == []
    assert result["total_count"] == 0


async def test_list_labourers_truncates_over_max(mongo_db):
    service = LabourerService(LabourerRepository())
    for i in range(tools.MAX_LIST_RESULTS + 5):
        await service.create(LabourerCreate(name=f"Labourer {i}"), "admin-1")

    result = await tools.list_labourers()

    assert len(result["labourers"]) == tools.MAX_LIST_RESULTS
    assert result["total_count"] == tools.MAX_LIST_RESULTS + 5
    assert result["truncated"] is True


async def test_get_labourer_returns_profile(mongo_db, labourer_id):
    result = await tools.get_labourer(labourer_id)

    assert result["id"] == labourer_id
    assert result["name"] == "Tool Test"


async def test_get_labourer_unknown_id_raises_not_found(mongo_db):
    from app.core.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await tools.get_labourer("507f1f77bcf86cd799439011")


async def test_list_sites_returns_serializable_dict(mongo_db, site_id):
    result = await tools.list_sites()

    assert result["total_count"] == 1
    assert result["sites"][0]["id"] == site_id


async def test_list_sites_filters_by_search(mongo_db, site_id):
    result = await tools.list_sites(search="Tool")

    assert result["sites"][0]["id"] == site_id

    result = await tools.list_sites(search="nonexistent")

    assert result["sites"] == []


async def test_get_site_returns_profile(mongo_db, site_id):
    result = await tools.get_site(site_id)

    assert result["id"] == site_id
    assert result["name"] == "Tool Site"


async def test_get_site_financial_summary_shape(mongo_db, site_id):
    result = await tools.get_site_financial_summary(site_id)

    assert result["site_id"] == site_id
    assert "total_cost" in result
    assert "current_profit" in result


async def test_get_site_crew_today_defaults_to_today(mongo_db, site_id, labourer_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date.today()), "admin-1"
    )

    result = await tools.get_site_crew_today(site_id)

    assert result["work_date"] == date.today().isoformat()
    assert len(result["entries"]) == 1
    assert result["entries"][0]["labourer_id"] == labourer_id


async def test_get_site_crew_today_with_explicit_date(mongo_db, site_id, labourer_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date(2026, 2, 1)), "admin-1"
    )

    result = await tools.get_site_crew_today(site_id, work_date="2026-02-01")

    assert len(result["entries"]) == 1


async def test_get_labourer_history_shape(mongo_db, labourer_id, site_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date(2026, 2, 1)), "admin-1"
    )
    await attendance_service.update(assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1")

    result = await tools.get_labourer_history(labourer_id, "2026-02-01", "2026-02-01")

    assert result["labourer_id"] == labourer_id
    assert result["total_earnings"] == "800.00"
    assert len(result["work_records"]) == 1


async def test_get_site_attendance_shape(mongo_db, labourer_id, site_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date(2026, 2, 1)), "admin-1"
    )
    await attendance_service.update(assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1")

    result = await tools.get_site_attendance(site_id, "2026-02-01", "2026-02-01")

    assert result["site_id"] == site_id
    assert result["total_amount"] == "800.00"


async def test_get_weekly_settlement_shape(mongo_db, labourer_id, site_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date(2026, 2, 2)), "admin-1"
    )
    await attendance_service.update(assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1")

    result = await tools.get_weekly_settlement("2026-02-01", "2026-02-07")

    entry = next(e for e in result["entries"] if e["labourer_id"] == labourer_id)
    assert entry["has_unpaid_earnings"] is True


async def test_get_payment_preview_shape(mongo_db, labourer_id, site_id):
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer_id, site_id=site_id, work_date=date(2026, 2, 1)), "admin-1"
    )
    await attendance_service.update(assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1")

    result = await tools.get_payment_preview(labourer_id, "daily", "2026-02-01", "2026-02-01")

    assert result["suggested_amount"] == "800.00"


async def test_get_labourer_ledger_bundles_everything(mongo_db, labourer_id):
    result = await tools.get_labourer_ledger(labourer_id)

    assert result["labourer_id"] == labourer_id
    assert result["labourer_name"] == "Tool Test"
    assert len(result["wage_history"]) == 1
    assert result["advances"] == []
    assert result["deductions"] == []
    assert result["adjustments"] == []
    assert result["payments"] == []


async def test_get_labourer_ledger_unknown_id_raises_not_found(mongo_db):
    from app.core.errors import NotFoundError

    with pytest.raises(NotFoundError):
        await tools.get_labourer_ledger("507f1f77bcf86cd799439011")


def test_tool_dispatch_contains_only_declared_read_tools():
    declared_names = {fd.name for fd in tools.TOOL_DECLARATIONS.function_declarations}

    assert set(tools.TOOL_DISPATCH.keys()) == declared_names
    # Structural read-only guarantee: no write-shaped name is ever registered.
    for name in tools.TOOL_DISPATCH:
        assert not any(verb in name for verb in ("create", "update", "delete", "assign", "mark", "remove", "set_"))
