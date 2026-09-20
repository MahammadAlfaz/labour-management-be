from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.modules.deductions.repository import DeductionRepository
from app.modules.deductions.schemas import DeductionCreate, DeductionOut
from app.modules.labourers.repository import LabourerRepository


class DeductionService:
    def __init__(
        self,
        repo: DeductionRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
    ):
        self._repo = repo or DeductionRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()

    async def create(self, payload: DeductionCreate, admin_id: str) -> DeductionOut:
        if await self._labourer_repo.get_by_id(payload.labourer_id) is None:
            raise NotFoundError("Labourer not found")

        deduction = await self._repo.create(
            labourer_id=payload.labourer_id,
            amount=payload.amount,
            reason=payload.reason,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="deduction",
            entity_id=deduction.id,
            action="create",
            admin_id=admin_id,
            after=deduction.model_dump(mode="json"),
        )
        return deduction

    async def list_for_labourer(self, labourer_id: str) -> list[DeductionOut]:
        return await self._repo.list_for_labourer(labourer_id)
