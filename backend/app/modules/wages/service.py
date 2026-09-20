from datetime import date
from decimal import Decimal

from app.core.audit import record_audit_log
from app.core.errors import ConflictError, NotFoundError
from app.modules.labourers.repository import LabourerRepository
from app.modules.wages.repository import WageRepository
from app.modules.wages.schemas import WageCreate, WageOut


class WageService:
    def __init__(
        self,
        repo: WageRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
    ):
        self._repo = repo or WageRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()

    async def add_wage(self, labourer_id: str, payload: WageCreate, admin_id: str) -> WageOut:
        labourer = await self._labourer_repo.get_by_id(labourer_id)
        if labourer is None:
            raise NotFoundError("Labourer not found")

        if await self._repo.exists_for_effective_date(labourer_id, payload.effective_from):
            raise ConflictError("A wage entry already exists for this effective date")

        wage = await self._repo.create(
            labourer_id=labourer_id,
            daily_wage=payload.daily_wage,
            effective_from=payload.effective_from,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="wage_history",
            entity_id=wage.id,
            action="create",
            admin_id=admin_id,
            after=wage.model_dump(mode="json"),
        )
        return wage

    async def list_history(self, labourer_id: str) -> list[WageOut]:
        return await self._repo.list_for_labourer(labourer_id)

    async def resolve_for_date(self, labourer_id: str, work_date: date) -> Decimal | None:
        return await self._repo.resolve_for_date(labourer_id, work_date)
