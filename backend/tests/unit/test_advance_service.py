from datetime import date

import pytest

from app.core.errors import NotFoundError
from app.modules.advances.repository import AdvanceRepository
from app.modules.advances.schemas import AdvanceCreate
from app.modules.advances.service import AdvanceService
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate
from app.modules.labourers.service import LabourerService

UNKNOWN_LABOURER_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
async def labourer_id(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Advance Test"), "admin-1"
    )
    return labourer.id


@pytest.fixture
def service(mongo_db):
    return AdvanceService(AdvanceRepository(), LabourerRepository())


async def test_create_advance(service, labourer_id):
    advance = await service.create(
        AdvanceCreate(labourer_id=labourer_id, amount="500", given_at=date(2026, 2, 1), note="Fuel"),
        "admin-1",
    )

    assert advance.amount == 500
    assert advance.note == "Fuel"
    assert advance.settled is False
    assert advance.settled_in_payment_id is None
    assert advance.created_by == "admin-1"


async def test_create_advance_for_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.create(
            AdvanceCreate(labourer_id=UNKNOWN_LABOURER_ID, amount="500", given_at=date(2026, 2, 1)),
            "admin-1",
        )


async def test_create_advance_rejects_non_positive_amount(service, labourer_id):
    with pytest.raises(ValueError):
        AdvanceCreate(labourer_id=labourer_id, amount="0", given_at=date(2026, 2, 1))
    with pytest.raises(ValueError):
        AdvanceCreate(labourer_id=labourer_id, amount="-50", given_at=date(2026, 2, 1))


async def test_list_for_labourer_orders_most_recent_first(service, labourer_id):
    await service.create(AdvanceCreate(labourer_id=labourer_id, amount="100", given_at=date(2026, 1, 1)), "admin-1")
    await service.create(AdvanceCreate(labourer_id=labourer_id, amount="200", given_at=date(2026, 2, 1)), "admin-1")

    advances = await service.list_for_labourer(labourer_id)

    assert [a.amount for a in advances] == [200, 100]


async def test_list_for_labourer_only_returns_their_own_advances(service, labourer_id, mongo_db):
    other = await LabourerService(LabourerRepository()).create(LabourerCreate(name="Other"), "admin-1")
    await service.create(AdvanceCreate(labourer_id=labourer_id, amount="100", given_at=date(2026, 1, 1)), "admin-1")
    await service.create(AdvanceCreate(labourer_id=other.id, amount="999", given_at=date(2026, 1, 1)), "admin-1")

    advances = await service.list_for_labourer(labourer_id)

    assert len(advances) == 1
    assert advances[0].amount == 100
