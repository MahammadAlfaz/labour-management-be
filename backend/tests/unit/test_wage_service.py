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


async def test_concurrent_duplicate_effective_date_is_rejected_by_db_constraint(
    wage_service, labourer_id, monkeypatch
):
    """Two admins racing to add the same effective date must still be blocked even if
    both requests pass the pre-check before either has written -- the unique index on
    (labourer_id, effective_from) is the real backstop, not the application check."""
    async def _never_finds_existing(*args, **kwargs):
        return False

    monkeypatch.setattr(wage_service._repo, "exists_for_effective_date", _never_finds_existing)

    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)), "admin-1"
    )

    with pytest.raises(ConflictError):
        await wage_service.add_wage(
            labourer_id, WageCreate(daily_wage="750", effective_from=date(2026, 1, 1)), "admin-2"
        )


async def test_add_wage_for_unknown_labourer_raises_not_found(wage_service):
    with pytest.raises(NotFoundError):
        await wage_service.add_wage(
            "507f1f77bcf86cd799439011",
            WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)),
            "admin-1",
        )


async def test_wage_rejects_non_positive_amount():
    with pytest.raises(ValueError):
        WageCreate(daily_wage="0", effective_from=date(2026, 1, 1))
    with pytest.raises(ValueError):
        WageCreate(daily_wage="-100", effective_from=date(2026, 1, 1))


async def test_list_history_orders_most_recent_effective_date_first(wage_service, labourer_id):
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="700", effective_from=date(2026, 1, 1)), "admin-1"
    )
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="900", effective_from=date(2026, 6, 1)), "admin-1"
    )
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="800", effective_from=date(2026, 3, 1)), "admin-1"
    )

    history = await wage_service.list_history(labourer_id)

    assert [w.daily_wage for w in history] == [900, 800, 700]


async def test_backfilling_an_earlier_wage_does_not_disturb_later_resolution(wage_service, labourer_id):
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="900", effective_from=date(2026, 6, 1)), "admin-1"
    )
    # Admin realizes they forgot an earlier rate change and backfills it.
    await wage_service.add_wage(
        labourer_id, WageCreate(daily_wage="750", effective_from=date(2026, 3, 1)), "admin-1"
    )

    assert await wage_service.resolve_for_date(labourer_id, date(2026, 2, 1)) is None
    assert await wage_service.resolve_for_date(labourer_id, date(2026, 4, 1)) == 750
    assert await wage_service.resolve_for_date(labourer_id, date(2026, 7, 1)) == 900
