import pytest

from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import ClientReceiptCreate, SiteCreate, SiteUpdate
from app.modules.sites.service import SiteService


@pytest.fixture
def service(mongo_db):
    return SiteService(SiteRepository())


async def test_create_site_defaults_to_active(service):
    site = await service.create(SiteCreate(name="Tower A", location="Sector 12"), "admin-1")

    assert site.status == "active"
    assert site.name == "Tower A"


async def test_close_then_reopen_round_trip(service):
    site = await service.create(SiteCreate(name="Tower B", location="Sector 9"), "admin-1")

    closed = await service.set_active(site.id, False, "admin-1")
    assert closed.status == "closed"

    reopened = await service.set_active(site.id, True, "admin-1")
    assert reopened.status == "active"


async def test_list_filters_by_status(service):
    await service.create(SiteCreate(name="Open Site", location="X"), "admin-1")
    closed = await service.create(SiteCreate(name="Closed Site", location="Y"), "admin-1")
    await service.set_active(closed.id, False, "admin-1")

    active_only = await service.list(status="active")

    assert {site.name for site in active_only} == {"Open Site"}


async def test_update_persists_optional_dates(service):
    site = await service.create(SiteCreate(name="Tower C", location="Z"), "admin-1")

    updated = await service.update(
        site.id, SiteUpdate(description="Foundation work"), "admin-1"
    )

    assert updated.description == "Foundation work"


async def test_recording_client_receipt_preserves_a_history(service):
    site = await service.create(
        SiteCreate(name="Tower D", location="Pune", contract_amount="100000"), "admin-1"
    )

    receipt = await service.record_client_receipt(
        site.id,
        ClientReceiptCreate(
            amount="25000", received_on="2026-02-01", note="First instalment"
        ),
        "admin-1",
    )

    assert receipt.amount == 25000
    assert (await service.list_client_receipts(site.id))[0].id == receipt.id
