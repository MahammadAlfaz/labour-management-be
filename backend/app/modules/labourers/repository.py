from datetime import datetime, timezone

from bson import ObjectId

from app.db import get_database
from app.modules.labourers.schemas import LabourerOut


def _to_out(doc: dict) -> LabourerOut:
    return LabourerOut(
        id=str(doc["_id"]),
        name=doc["name"],
        phone=doc.get("phone"),
        upi_id=doc.get("upi_id"),
        status=doc["status"],
        work_category=doc.get("work_category"),
        payment_frequency=doc["payment_frequency"],
        photo_url=doc.get("photo_url"),
        created_by=doc["created_by"],
        updated_by=doc["updated_by"],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


class LabourerRepository:
    def __init__(self) -> None:
        self._collection = get_database().labourers

    async def create(
        self,
        *,
        name: str,
        phone: str | None,
        upi_id: str | None,
        work_category: str | None,
        payment_frequency: str,
        admin_id: str,
    ) -> LabourerOut:
        now = datetime.now(timezone.utc)
        doc = {
            "name": name,
            "phone": phone,
            "upi_id": upi_id,
            "status": "active",
            "work_category": work_category,
            "payment_frequency": payment_frequency,
            "created_by": admin_id,
            "updated_by": admin_id,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_out(doc)

    async def get_by_id(self, labourer_id: str) -> LabourerOut | None:
        if not ObjectId.is_valid(labourer_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(labourer_id)})
        return _to_out(doc) if doc else None

    async def list(
        self, *, status: str | None = None, search: str | None = None
    ) -> list[LabourerOut]:
        query: dict = {}
        if status:
            query["status"] = status
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        cursor = self._collection.find(query).sort("name", 1)
        return [_to_out(doc) async for doc in cursor]

    async def update(self, labourer_id: str, *, updates: dict, admin_id: str) -> LabourerOut | None:
        updates_with_meta = {
            **updates,
            "updated_by": admin_id,
            "updated_at": datetime.now(timezone.utc),
        }
        await self._collection.update_one(
            {"_id": ObjectId(labourer_id)}, {"$set": updates_with_meta}
        )
        return await self.get_by_id(labourer_id)

    async def set_status(self, labourer_id: str, status: str, admin_id: str) -> LabourerOut | None:
        return await self.update(labourer_id, updates={"status": status}, admin_id=admin_id)

    async def get_photo_path(self, labourer_id: str) -> str | None:
        doc = await self._collection.find_one(
            {"_id": ObjectId(labourer_id)}, projection={"photo_path": 1}
        )
        return doc.get("photo_path") if doc else None

    async def set_photo(
        self, labourer_id: str, *, path: str | None, url: str | None, admin_id: str
    ) -> LabourerOut | None:
        return await self.update(
            labourer_id, updates={"photo_path": path, "photo_url": url}, admin_id=admin_id
        )
