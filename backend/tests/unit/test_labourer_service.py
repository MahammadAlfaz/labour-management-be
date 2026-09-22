import pytest

from app.core.errors import NotFoundError
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate, LabourerUpdate
from app.modules.labourers.service import LabourerService

UNKNOWN_LABOURER_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def service(mongo_db):
    return LabourerService(LabourerRepository())


async def test_create_labourer_defaults_to_active(service):
    labourer = await service.create(
        LabourerCreate(name="Ravi Kumar", phone="9999999999", upi_id="ravi@upi"), "admin-1"
    )

    assert labourer.status == "active"
    assert labourer.name == "Ravi Kumar"
    assert labourer.created_by == "admin-1"
    assert labourer.phone == "9999999999"
    assert labourer.upi_id == "ravi@upi"


async def test_create_labourer_without_upi_id_leaves_it_none(service):
    labourer = await service.create(LabourerCreate(name="No UPI"), "admin-1")

    assert labourer.upi_id is None


async def test_update_sets_upi_id(service):
    labourer = await service.create(LabourerCreate(name="Test"), "admin-1")

    updated = await service.update(labourer.id, LabourerUpdate(upi_id="test@ybl"), "admin-1")

    assert updated.upi_id == "test@ybl"


async def test_deactivate_then_activate_round_trip(service):
    labourer = await service.create(LabourerCreate(name="Test"), "admin-1")

    deactivated = await service.set_active(labourer.id, False, "admin-1")
    assert deactivated.status == "inactive"

    reactivated = await service.set_active(labourer.id, True, "admin-1")
    assert reactivated.status == "active"


async def test_list_filters_by_status(service):
    await service.create(LabourerCreate(name="Active One"), "admin-1")
    inactive = await service.create(LabourerCreate(name="Inactive One"), "admin-1")
    await service.set_active(inactive.id, False, "admin-1")

    active_only = await service.list(status="active", search=None)

    assert {labourer.name for labourer in active_only} == {"Active One"}


async def test_update_changes_fields_without_touching_status(service):
    labourer = await service.create(LabourerCreate(name="Old Name"), "admin-1")

    updated = await service.update(labourer.id, LabourerUpdate(name="New Name"), "admin-1")

    assert updated.name == "New Name"
    assert updated.status == "active"


async def test_get_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.get(UNKNOWN_LABOURER_ID)


async def test_update_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.update(UNKNOWN_LABOURER_ID, LabourerUpdate(name="X"), "admin-1")


async def test_set_active_unknown_labourer_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.set_active(UNKNOWN_LABOURER_ID, False, "admin-1")


async def test_search_filters_by_partial_case_insensitive_name(service):
    await service.create(LabourerCreate(name="Ramesh Kumar"), "admin-1")
    await service.create(LabourerCreate(name="Suresh"), "admin-1")

    results = await service.list(status=None, search="ramesh")

    assert {l.name for l in results} == {"Ramesh Kumar"}


async def test_update_strips_whitespace_from_name(service):
    labourer = await service.create(LabourerCreate(name="Original"), "admin-1")

    updated = await service.update(labourer.id, LabourerUpdate(name="  Padded Name  "), "admin-1")

    assert updated.name == "Padded Name"
