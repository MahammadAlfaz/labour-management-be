from fastapi import UploadFile

from app.core.audit import record_audit_log
from app.core.errors import NotFoundError
from app.core.photo_upload import handle_photo_upload
from app.core.supabase_storage import delete_image
from app.modules.labourers.repository import LabourerRepository
from app.modules.labourers.schemas import LabourerCreate, LabourerOut, LabourerUpdate


class LabourerService:
    def __init__(self, repo: LabourerRepository | None = None):
        self._repo = repo or LabourerRepository()

    async def create(self, payload: LabourerCreate, admin_id: str) -> LabourerOut:
        data = payload.model_dump(mode="json")
        labourer = await self._repo.create(
            name=data["name"].strip(),
            phone=data.get("phone"),
            upi_id=data.get("upi_id"),
            work_category=data.get("work_category"),
            payment_frequency=data["payment_frequency"],
            admin_id=admin_id,
        )
        await record_audit_log(
            entity_type="labourer",
            entity_id=labourer.id,
            action="create",
            admin_id=admin_id,
            after=labourer.model_dump(mode="json"),
        )
        return labourer

    async def get(self, labourer_id: str) -> LabourerOut:
        labourer = await self._repo.get_by_id(labourer_id)
        if labourer is None:
            raise NotFoundError("Labourer not found")
        return labourer

    async def list(self, *, status: str | None, search: str | None) -> list[LabourerOut]:
        return await self._repo.list(status=status, search=search)

    async def update(self, labourer_id: str, payload: LabourerUpdate, admin_id: str) -> LabourerOut:
        before = await self.get(labourer_id)
        updates = {
            k: v
            for k, v in payload.model_dump(mode="json", exclude_unset=True).items()
            if v is not None
        }
        if "name" in updates:
            updates["name"] = updates["name"].strip()

        updated = await self._repo.update(labourer_id, updates=updates, admin_id=admin_id)
        await record_audit_log(
            entity_type="labourer",
            entity_id=labourer_id,
            action="update",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
            after=updated.model_dump(mode="json") if updated else None,
        )
        return updated  # type: ignore[return-value]

    async def upload_photo(self, labourer_id: str, file: UploadFile, admin_id: str) -> LabourerOut:
        await self.get(labourer_id)  # raises NotFoundError if missing
        existing_path = await self._repo.get_photo_path(labourer_id)

        result = await handle_photo_upload(
            file=file, folder=f"labourers/{labourer_id}", existing_photo_path=existing_path
        )

        updated = await self._repo.set_photo(
            labourer_id, path=result["path"], url=result["url"], admin_id=admin_id
        )
        await record_audit_log(
            entity_type="labourer",
            entity_id=labourer_id,
            action="photo_upload",
            admin_id=admin_id,
            after={"photo_url": result["url"]},
        )
        return updated  # type: ignore[return-value]

    async def remove_photo(self, labourer_id: str, admin_id: str) -> LabourerOut:
        await self.get(labourer_id)
        existing_path = await self._repo.get_photo_path(labourer_id)
        if existing_path:
            await delete_image(existing_path)

        updated = await self._repo.set_photo(labourer_id, path=None, url=None, admin_id=admin_id)
        await record_audit_log(
            entity_type="labourer",
            entity_id=labourer_id,
            action="photo_remove",
            admin_id=admin_id,
        )
        return updated  # type: ignore[return-value]

    async def set_active(self, labourer_id: str, is_active: bool, admin_id: str) -> LabourerOut:
        before = await self.get(labourer_id)
        status = "active" if is_active else "inactive"
        updated = await self._repo.set_status(labourer_id, status, admin_id)
        await record_audit_log(
            entity_type="labourer",
            entity_id=labourer_id,
            action="activate" if is_active else "deactivate",
            admin_id=admin_id,
            before=before.model_dump(mode="json"),
            after=updated.model_dump(mode="json") if updated else None,
        )
        return updated  # type: ignore[return-value]
