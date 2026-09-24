import pytest

from app.core.errors import NotFoundError
from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import ClientReceiptCreate, SiteCreate, SiteExpenseCreate, SiteUpdate
from app.modules.sites.service import SiteService

UNKNOWN_SITE_ID = "507f1f77bcf86cd799439011"


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


async def test_list_filters_by_partial_case_insensitive_name_search(service):
    await service.create(SiteCreate(name="Sampath Kumar", location="Kundapura"), "admin-1")
    await service.create(SiteCreate(name="Siriyara Bavi", location="Siriyara"), "admin-1")

    results = await service.list(status=None, search="sampath")

    assert {site.name for site in results} == {"Sampath Kumar"}


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


async def test_get_unknown_site_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.get(UNKNOWN_SITE_ID)


async def test_update_unknown_site_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.update(UNKNOWN_SITE_ID, SiteUpdate(description="x"), "admin-1")


async def test_record_client_receipt_for_unknown_site_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.record_client_receipt(
            UNKNOWN_SITE_ID,
            ClientReceiptCreate(amount="1000", received_on="2026-02-01"),
            "admin-1",
        )


async def test_record_site_expense_for_unknown_site_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.record_site_expense(
            UNKNOWN_SITE_ID,
            SiteExpenseCreate(category="FOOD", amount="500", expense_date="2026-02-01"),
            "admin-1",
        )


async def test_record_and_list_site_expenses(service):
    site = await service.create(SiteCreate(name="Tower E", location="Pune"), "admin-1")

    expense = await service.record_site_expense(
        site.id,
        SiteExpenseCreate(category="FOOD", amount="1500", expense_date="2026-02-01", note="Lunch"),
        "admin-1",
    )

    assert expense.amount == 1500
    listed = await service.list_site_expenses(site.id)
    assert len(listed) == 1
    assert listed[0].id == expense.id


async def test_financial_summary_with_no_contract_amount(service):
    site = await service.create(SiteCreate(name="Tower F", location="Pune"), "admin-1")

    summary = await service.financial_summary(site.id)

    assert summary.contract_amount is None
    assert summary.client_balance is None
    assert summary.expected_profit is None
    assert summary.current_profit == 0
    assert summary.total_cost == 0


async def test_financial_summary_aggregates_receipts_and_site_expenses(service):
    site = await service.create(
        SiteCreate(name="Tower G", location="Pune", contract_amount="50000"), "admin-1"
    )
    await service.record_client_receipt(
        site.id, ClientReceiptCreate(amount="20000", received_on="2026-02-01"), "admin-1"
    )
    await service.record_client_receipt(
        site.id, ClientReceiptCreate(amount="10000", received_on="2026-02-10"), "admin-1"
    )
    await service.record_site_expense(
        site.id, SiteExpenseCreate(category="FOOD", amount="2000", expense_date="2026-02-01"), "admin-1"
    )
    await service.record_site_expense(
        site.id, SiteExpenseCreate(category="OTHER", amount="500", expense_date="2026-02-02"), "admin-1"
    )

    summary = await service.financial_summary(site.id)

    assert summary.client_received == 30000
    assert summary.site_expenses == 2500
    assert summary.labour_cost == 0  # no attendance recorded for this site
    assert summary.travel_expenses == 0
    assert summary.total_cost == 2500
    assert summary.current_profit == 27500  # 30000 received - 2500 cost
    assert summary.client_balance == 20000  # 50000 contract - 30000 received
    assert summary.expected_profit == 47500  # 50000 contract - 2500 cost


async def test_financial_summary_can_show_a_loss(service):
    site = await service.create(
        SiteCreate(name="Tower H", location="Pune", contract_amount="1000"), "admin-1"
    )
    await service.record_site_expense(
        site.id, SiteExpenseCreate(category="OTHER", amount="5000", expense_date="2026-02-01"), "admin-1"
    )

    summary = await service.financial_summary(site.id)

    assert summary.current_profit == -5000
    assert summary.expected_profit == -4000
