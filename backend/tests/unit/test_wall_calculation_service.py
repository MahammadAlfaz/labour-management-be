from decimal import Decimal

import pytest

from app.core.errors import NotFoundError
from app.modules.sites.repository import SiteRepository
from app.modules.sites.schemas import SiteCreate
from app.modules.sites.service import SiteService
from app.modules.wall_calculations.repository import WallCalculationRepository
from app.modules.wall_calculations.schemas import (
    LayerInput,
    MeasurementLine,
    WallCalculationCreate,
    WallCalculationUpdate,
)
from app.modules.wall_calculations.service import WallCalculationService


@pytest.fixture
def service(mongo_db):
    return WallCalculationService(WallCalculationRepository(), SiteRepository())


def _payload(**overrides) -> WallCalculationCreate:
    defaults = dict(
        measurements=[
            MeasurementLine(raw_text="31 1/4 - 1 pc", length=Decimal("31.25"), quantity=1),
        ],
        total_measurement=Decimal("190.75"),
        layers=[LayerInput(height=Decimal("2.25"), breadth=Decimal("2.50"))],
        rate_per_sqft=Decimal("27"),
    )
    defaults.update(overrides)
    return WallCalculationCreate(**defaults)


async def test_create_computes_layers_area_and_total_cost(service):
    calc = await service.create(_payload(), "admin-1")

    assert calc.layers[0].area == Decimal("1072.96875")
    assert calc.total_area == Decimal("1072.96875")
    assert calc.total_cost == Decimal("28970.16")  # 1072.96875 * 27, rounded
    assert calc.created_by == "admin-1"


async def test_create_ignores_client_supplied_totals_and_recomputes_server_side(service):
    payload = _payload()
    # WallCalculationCreate has no total_area/total_cost fields at all --
    # this asserts the service never trusts anything but layers/rate/total_measurement.
    calc = await service.create(payload, "admin-1")

    assert calc.total_cost == Decimal("28970.16")


async def test_create_with_unknown_site_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.create(_payload(site_id="000000000000000000000000"), "admin-1")


async def test_create_with_valid_site_id_links_the_calculation(service):
    site = await SiteService(SiteRepository()).create(
        SiteCreate(name="North Wall Site", location="Sector 7"), "admin-1"
    )

    calc = await service.create(_payload(site_id=site.id), "admin-1")

    assert calc.site_id == site.id


async def test_list_filters_by_site_id(service):
    site = await SiteService(SiteRepository()).create(
        SiteCreate(name="Site A", location="X"), "admin-1"
    )
    await service.create(_payload(site_id=site.id), "admin-1")
    await service.create(_payload(), "admin-1")

    scoped = await service.list(site_id=site.id)

    assert len(scoped) == 1
    assert scoped[0].site_id == site.id


async def test_update_recomputes_totals_from_new_rate(service):
    calc = await service.create(_payload(), "admin-1")

    updated = await service.update(
        calc.id, WallCalculationUpdate(rate_per_sqft=Decimal("30")), "admin-1"
    )

    assert updated.rate_per_sqft == Decimal("30")
    assert updated.total_cost == Decimal("32189.06")  # 1072.96875 * 30, rounded


async def test_update_recomputes_layer_area_when_total_measurement_changes(service):
    calc = await service.create(_payload(), "admin-1")

    updated = await service.update(
        calc.id, WallCalculationUpdate(total_measurement=Decimal("100")), "admin-1"
    )

    assert updated.layers[0].area == Decimal("562.50")  # 100 * 2.25 * 2.50


async def test_delete_removes_the_record(service):
    calc = await service.create(_payload(), "admin-1")

    await service.delete(calc.id, "admin-1")

    with pytest.raises(NotFoundError):
        await service.get(calc.id)


async def test_get_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.get("000000000000000000000000")


async def test_update_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.update(
            "000000000000000000000000", WallCalculationUpdate(rate_per_sqft=Decimal("30")), "admin-1"
        )


async def test_update_with_unknown_site_id_raises_not_found(service):
    calc = await service.create(_payload(), "admin-1")

    with pytest.raises(NotFoundError):
        await service.update(
            calc.id, WallCalculationUpdate(site_id="000000000000000000000000"), "admin-1"
        )


async def test_delete_unknown_id_raises_not_found(service):
    with pytest.raises(NotFoundError):
        await service.delete("000000000000000000000000", "admin-1")
