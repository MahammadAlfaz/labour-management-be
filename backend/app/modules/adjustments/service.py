from decimal import Decimal

from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.modules.adjustments.repository import AdjustmentRepository
from app.modules.adjustments.schemas import AdjustmentCreate, AdjustmentOut
from app.modules.labourers.repository import LabourerRepository


class AdjustmentService:
    def __init__(
        self,
        repo: AdjustmentRepository | None = None,
        labourer_repo: LabourerRepository | None = None,
    ):
        self._repo = repo or AdjustmentRepository()
        self._labourer_repo = labourer_repo or LabourerRepository()

    async def create_manual(self, payload: AdjustmentCreate, admin_id: str) -> AdjustmentOut:
        if await self._labourer_repo.get_by_id(payload.labourer_id) is None:
            raise NotFoundError("Labourer not found")

        adjustment = await self._repo.create(
            labourer_id=payload.labourer_id,
            amount=payload.amount,
            reason=payload.reason,
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="adjustment",
            entity_id=adjustment.id,
            action="create",
            admin_id=admin_id,
            after=adjustment.model_dump(mode="json"),
        )
        return adjustment

    async def record_correction(
        self,
        *,
        labourer_id: str,
        amount: Decimal,
        reason: str,
        related_record_type: str,
        related_record_id: str,
        admin_id: str,
    ) -> AdjustmentOut:
        """Used internally when a post-payment edit changes an already-paid amount.

        The historical payment is never touched; this ledger entry carries the
        difference into the labourer's next settlement instead.
        """
        adjustment = await self._repo.create(
            labourer_id=labourer_id,
            amount=amount,
            reason=reason,
            admin_id=admin_id,
            related_record_type=related_record_type,
            related_record_id=related_record_id,
        )
        await record_audit_log(
            entity_type="adjustment",
            entity_id=adjustment.id,
            action="auto_correction",
            admin_id=admin_id,
            after=adjustment.model_dump(mode="json"),
        )
        return adjustment

    async def list_for_labourer(self, labourer_id: str) -> list[AdjustmentOut]:
        return await self._repo.list_for_labourer(labourer_id)
