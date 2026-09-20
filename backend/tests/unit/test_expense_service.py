from datetime import date

import pytest

from app.core.errors import NotFoundError
from app.modules.attendance.repository import WorkRecordRepository
from app.modules.attendance.schemas import AttendanceStatus, WorkRecordAssign, WorkRecordUpdate
from app.modules.attendance.service import AttendanceService
from app.modules.expenses.repository import ExpenseRepository
from app.modules.expenses.schemas import ExpenseCreate, ExpenseUpdate
from app.modules.expenses.service import ExpenseService
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
async def work_record_id(mongo_db):
    site = await SiteService(SiteRepository()).create(SiteCreate(name="Site A", location="Loc A"), "admin-1")
    labourer = await LabourerService(LabourerRepository()).create(LabourerCreate(name="Expense Test"), "admin-1")
    await WageService(WageRepository(), LabourerRepository()).add_wage(
        labourer.id, WageCreate(daily_wage="800", effective_from=date(2026, 1, 1)), "admin-1"
    )
    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    assigned = await attendance_service.assign(
        WorkRecordAssign(labourer_id=labourer.id, site_id=site.id, work_date=date(2026, 2, 1)), "admin-1"
    )
    record = await attendance_service.update(
        assigned.id, WorkRecordUpdate(status=AttendanceStatus.FULL_DAY), "admin-1"
    )
    return record.id


@pytest.fixture
def expense_service(mongo_db):
    return ExpenseService(ExpenseRepository(), WorkRecordRepository())


async def test_add_expense_and_list(expense_service, work_record_id):
    await expense_service.add(work_record_id, ExpenseCreate(category="PETROL", amount="50"), "admin-1")
    await expense_service.add(work_record_id, ExpenseCreate(category="BUS", amount="20", note="Return trip"), "admin-1")

    expenses = await expense_service.list_for_record(work_record_id)

    assert len(expenses) == 2
    assert {e.category for e in expenses} == {"PETROL", "BUS"}


async def test_add_expense_for_unknown_record_raises_not_found(expense_service):
    with pytest.raises(NotFoundError):
        await expense_service.add(
            "507f1f77bcf86cd799439011", ExpenseCreate(category="OTHER", amount="10"), "admin-1"
        )


async def test_update_and_delete_expense(expense_service, work_record_id):
    expense = await expense_service.add(work_record_id, ExpenseCreate(category="AUTO", amount="30"), "admin-1")

    updated = await expense_service.update(work_record_id, expense.id, ExpenseUpdate(amount="35"), "admin-1")
    assert updated.amount == 35

    await expense_service.delete(work_record_id, expense.id, "admin-1")
    assert await expense_service.list_for_record(work_record_id) == []


async def test_update_rejects_mismatched_record_id(expense_service, work_record_id):
    expense = await expense_service.add(work_record_id, ExpenseCreate(category="AUTO", amount="30"), "admin-1")

    with pytest.raises(NotFoundError):
        await expense_service.update(
            "507f1f77bcf86cd799439011", expense.id, ExpenseUpdate(amount="99"), "admin-1"
        )


async def test_earnings_calculation_includes_expenses(work_record_id, mongo_db):
    expense_service = ExpenseService(ExpenseRepository(), WorkRecordRepository())
    await expense_service.add(work_record_id, ExpenseCreate(category="PETROL", amount="50"), "admin-1")
    await expense_service.add(work_record_id, ExpenseCreate(category="BUS", amount="25"), "admin-1")

    attendance_service = AttendanceService(
        WorkRecordRepository(), LabourerRepository(), SiteRepository(), WageService(WageRepository(), LabourerRepository())
    )
    detail = await attendance_service.get_detail(work_record_id)

    assert detail.amount == 800
    assert len(detail.expenses) == 2
    assert detail.total_earnings == 875
