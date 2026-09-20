from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.core.supabase_storage import delete_image
from app.modules.sites.repository import SiteRepository
from app.modules.wall_calculations.calculations import compute_layers, compute_total_cost, sum_area
from app.modules.wall_calculations.repository import WallCalculationRepository
from app.modules.wall_calculations.schemas import (
    LayerInput,
    WallCalculationCreate,
    WallCalculationOut,
    WallCalculationUpdate,
)


class WallCalculationService:
    def __init__(
        self,
        repo: WallCalculationRepository | None = None,
        site_repo: SiteRepository | None = None,
    ):
        self._repo = repo or WallCalculationRepository()
        self._site_repo = site_repo or SiteRepository()

    async def _ensure_site_exists(self, site_id: str | None) -> None:
        if site_id is None:
            return
        site = await self._site_repo.get_by_id(site_id)
        if site is None:
            raise NotFoundError("Site not found")

    async def create(self, payload: WallCalculationCreate, admin_id: str) -> WallCalculationOut:
        await self._ensure_site_exists(payload.site_id)

        layers = compute_layers(payload.layers, payload.total_measurement)
        total_area = sum_area(layers)
        total_cost = compute_total_cost(total_area, payload.rate_per_sqft)

        calc = await self._repo.create(
            site_id=payload.site_id,
            title=payload.title,
            source_image_path=payload.source_image_path,
            measurements=payload.measurements,
            layers=layers,
            total_measurement=payload.total_measurement,
            total_area=total_area,
            rate_per_sqft=payload.rate_per_sqft,
            total_cost=total_cost,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="wall_calculation",
            entity_id=calc.id,
            action="create",
            admin_id=admin_id,
            after=calc.model_dump(mode="json"),
        )
        return calc

    async def get(self, calc_id: str) -> WallCalculationOut:
        calc = await self._repo.get_by_id(calc_id)
        if calc is None:
            raise NotFoundError("Wall calculation not found")
        return calc

    async def list(self, *, site_id: str | None = None) -> list[WallCalculationOut]:
        return await self._repo.list(site_id=site_id)

    async def update(
        self, calc_id: str, payload: WallCalculationUpdate, admin_id: str
    ) -> WallCalculationOut:
        before = await self.get(calc_id)

        site_id = payload.site_id if payload.site_id is not None else before.site_id
        await self._ensure_site_exists(site_id)

        title = payload.title if payload.title is not None else before.title
        measurements = (
            payload.measurements if payload.measurements is not None else before.measurements
        )
        total_measurement = (
            payload.total_measurement
            if payload.total_measurement is not None
            else before.total_measurement
        )
        layer_inputs = (
            payload.layers
            if payload.layers is not None
            else [
                LayerInput(label=layer.label, height=layer.height, breadth=layer.breadth)
                for layer in before.layers
            ]
        )
        rate_per_sqft = (
            payload.rate_per_sqft if payload.rate_per_sqft is not None else before.rate_per_sqft
        )

        layers = compute_layers(layer_inputs, total_measurement)
        total_area = sum_area(layers)
        total_cost = compute_total_cost(total_area, rate_per_sqft)

        updated = await self._repo.replace_calculation(
            calc_id,
            site_id=site_id,
            title=title,
            measurements=measurements,
            layers=layers,
            total_measurement=total_measurement,
            total_area=total_area,
            rate_per_sqft=rate_per_sqft,
            total_cost=total_cost,
            admin_id=admin_id,
        )
        assert updated is not None  # `before` was already fetched successfully above

        await record_audit_log(
            entity_type="wall_calculation",
            entity_id=calc_id,
            action="update",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
            after=updated.model_dump(mode="json"),
        )
        return updated

    async def delete(self, calc_id: str, admin_id: str) -> None:
        before = await self.get(calc_id)
        await self._repo.delete(calc_id)
        if before.source_image_path:
            await delete_image(before.source_image_path)
        await record_audit_log(
            entity_type="wall_calculation",
            entity_id=calc_id,
            action="delete",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
        )
