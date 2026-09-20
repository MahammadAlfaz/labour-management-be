from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.modules.advances.repository import AdvanceRepository
from app.modules.advances.schemas import AdvanceCreate, AdvanceOut
from app.modules.labourers.repository import LabourerRepository


class AdvanceService:
    def __init__(
        self,
        repo: AdvanceRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
    ):
        self._repo = repo or AdvanceRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()

    async def create(self, payload: AdvanceCreate, admin_id: str) -> AdvanceOut:
        if await self._labourer_repo.get_by_id(payload.labourer_id) is None:
            raise NotFoundError("Labourer not found")

        advance = await self._repo.create(
            labourer_id=payload.labourer_id,
            amount=payload.amount,
            note=payload.note,
            given_at=payload.given_at,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="advance",
            entity_id=advance.id,
            action="create",
            admin_id=admin_id,
            after=advance.model_dump(mode="json"),
        )
        return advance

    async def list_for_labourer(self, labourer_id: str) -> list[AdvanceOut]:
        return await self._repo.list_for_labourer(labourer_id)
