from datetime import date

import pytest

from app.core.errors import ConflictError, NotFoundError
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate
from app.modules.labourers.service import LabourerService
from app.modules.wages.repository import WageRepository
from app.modules.wages.schemas import WageCreate
from app.modules.wages.service import WageService


@pytest.fixture
async def labourer_id(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Wage Test Labourer"), "admin-1"
    )
    return labourer.id


@pytest.fixture
def wage_service(mongo_db):
    return WageService(WageRepository(), LabourerRepository())


async def test_resolve_picks_most_recent_effective_wage(wage_service, labourer_id):
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)), "admin-1"
    )
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="800", effective_from=date(2026, 3, 1)), "admin-1"
    )

    assert await wage_service.resolve_for_date(labourer_id, date(2026, 2, 1)) == 700
    assert await wage_service.resolve_for_date(labourer_id, date(2026, 3, 1)) == 800
    assert await wage_service.resolve_for_date(labourer_id, date(2026, 12, 31)) == 800


async def test_resolve_returns_none_before_any_wage_set(wage_service, labourer_id):
    assert await wage_service.resolve_for_date(labourer_id, date(2026, 1, 1)) is None


async def test_duplicate_effective_date_is_rejected(wage_service, labourer_id):
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)), "admin-1"
    )

    with pytest.raises(ConflictError):
        await wage_service.add_wage(
            labourer_id, WageCreate(daily_wage="750", effective_from=date(2026, 1, 1)), "admin-1"
        )


async def test_add_wage_for_unknown_labourer_raises_not_found(wage_service):
    with pytest.raises(NotFoundError):
        await wage_service.add_wage(
            "507f1f77bcf86cd799439011",
            WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)),
            "admin-1",
        )
