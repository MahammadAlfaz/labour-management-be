import pytest

from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate, LabourerUpdate
from app.modules.labourers.service import LabourerService


@pytest.fixture
def service(mongo_db):
    return LabourerService(LabourerRepository())


async def test_create_labourer_defaults_to_active(service):
    labourer = await service.create(LabourerCreate(name="Ravi Kumar", phone="9999999999"), "admin-1")

    assert labourer.status == "active"
    assert labourer.name == "Ravi Kumar"
    assert labourer.created_by == "admin-1"


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
