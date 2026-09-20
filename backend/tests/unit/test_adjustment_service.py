import pytest

from app.core.errors import NotFoundError
from app.modules.adjustments.repository import AdjustmentRepository
from app.modules.adjustments.schemas import AdjustmentCreate
from app.modules.adjustments.service import AdjustmentService
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate
from app.modules.labourers.service import LabourerService

UNKNOWN_LABOURER_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
async def labourer_id(mongo_db):
    labourer = await LabourerService(LabourerRepository()).create(
        LabourerCreate(name="Adjustment Test"), "admin-1"
    )
    return labourer.id


@pytest.fixture
def service(mongo_db):
    return AdjustmentService(AdjustmentRepository(), LabourerRepository())


async def test_create_manual_adjustment_positive_amount(service, labourer_id):
    adjustment = await service.create_manual(
        AdjustmentCreate(labourer_id=labourer_id, amount="150", reason="Miscounted last week"),
        "admin-1",
    )

    assert adjustment.amount == 150
    assert adjustment.reason == "Miscounted last week"
    assert adjustment.settled is False
    assert adjustment.related_record_type is None
    assert adjustment.related_record_id is None


async def test_create_manual_adjustment_negative_amount(service, labourer_id):
    adjustment = await service.create_manual(
        AdjustmentCreate(labourer_id=labourer_id, amount="-100", reason="Overpaid last time"),
        "admin-1",
    )

    assert adjustment.amount == -100


async def test_create_manual_adjustment_for_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.create_manual(
            AdjustmentCreate(labourer_id=UNKNOWN_LABOURER_ID, amount="100", reason="x"), "admin-1"
        )


async def test_create_manual_adjustment_requires_a_reason(service, labourer_id):
    with pytest.raises(ValueError):
        AdjustmentCreate(labourer_id=labourer_id, amount="100", reason="")


async def test_record_correction_links_related_record(service, labourer_id):
    adjustment = await service.record_correction(
        labourer_id=labourer_id,
        amount="-50",
        reason="Expense removed after payment",
        related_record_type="daily_work_record",
        related_record_id="abc123",
        admin_id="admin-1",
    )

    assert adjustment.amount == -50
    assert adjustment.related_record_type == "daily_work_record"
    assert adjustment.related_record_id == "abc123"
    assert adjustment.settled is False


async def test_list_for_labourer_orders_most_recent_first(service, labourer_id):
    first = await service.create_manual(
        AdjustmentCreate(labourer_id=labourer_id, amount="10", reason="A"), "admin-1"
    )
    second = await service.create_manual(
        AdjustmentCreate(labourer_id=labourer_id, amount="20", reason="B"), "admin-1"
    )

    adjustments = await service.list_for_labourer(labourer_id)

    assert [a.id for a in adjustments] == [second.id, first.id]
