import pytest

from app.core.errors import NotFoundError
from app.modules.deductions.repository import DeductionRepository
from app.modules.deductions.schemas import DeductionCreate
from app.modules.deductions.service import DeductionService
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate
from app.modules.labourers.service import LabourerService

UNKNOWN_LABOURER_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
async def labourer_id(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Deduction Test"), "admin-1"
    )
    return labourer.id


@pytest.fixture
def service(mongo_db):
    return DeductionService(DeductionRepository(), LabourerRepository())


async def test_create_deduction(service, labourer_id):
    deduction = await service.create(
        DeductionCreate(labourer_id=labourer_id, amount="200", reason="Tool damage"), "admin-1"
    )

    assert deduction.amount == 200
    assert deduction.reason == "Tool damage"
    assert deduction.settled is False
    assert deduction.settled_in_payment_id is None


async def test_create_deduction_for_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.create(
            DeductionCreate(labourer_id=UNKNOWN_LABOURER_ID, amount="200", reason="x"), "admin-1"
        )


async def test_create_deduction_requires_a_reason(service, labourer_id):
    with pytest.raises(ValueError):
        DeductionCreate(labourer_id=labourer_id, amount="200", reason="")


async def test_create_deduction_rejects_non_positive_amount(service, labourer_id):
    with pytest.raises(ValueError):
        DeductionCreate(labourer_id=labourer_id, amount="0", reason="x")


async def test_list_for_labourer_orders_most_recent_first(service, labourer_id):
    first = await service.create(DeductionCreate(labourer_id=labourer_id, amount="50", reason="A"), "admin-1")
    second = await service.create(DeductionCreate(labourer_id=labourer_id, amount="75", reason="B"), "admin-1")

    deductions = await service.list_for_labourer(labourer_id)

    assert [d.id for d in deductions] == [second.id, first.id]
