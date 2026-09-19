from datetime import datetime, timezone

from bson import ObjectId

from app.db import get_database
from app.modules.admins.schemas import AdminOut


def _to_admin_out(doc: dict) -> AdminOut:
    return AdminOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        is_active=doc["is_active"],
        created_at=doc["created_at"],
    )


class AdminRepository:
    def __init__(self) -> None:
        self._collection = get_database().admins

    async def find_by_google_sub(self, google_sub: str) -> AdminOut | None:
        doc = await self._collection.find_one({"google_sub": google_sub})
        return _to_admin_out(doc) if doc else None

    async def find_by_email(self, email: str) -> AdminOut | None:
        doc = await self._collection.find_one({"email": email.lower()})
        return _to_admin_out(doc) if doc else None

    async def get_by_id(self, admin_id: str) -> AdminOut | None:
        if not ObjectId.is_valid(admin_id):
            return None
        doc = await self._collection.find_one({"_id": ObjectId(admin_id)})
        return _to_admin_out(doc) if doc else None

    async def create(self, *, google_sub: str, email: str, name: str) -> AdminOut:
        now = datetime.now(timezone.utc)
        doc = {
            "google_sub": google_sub,
            "email": email.lower(),
            "name": name,
            "is_active": True,
            "created_at": now,
        }
        result = await self._collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return _to_admin_out(doc)

    async def set_active(self, admin_id: str, is_active: bool) -> None:
        await self._collection.update_one(
            {"_id": ObjectId(admin_id)}, {"$set": {"is_active": is_active}}
        )

    async def list_all(self) -> list[AdminOut]:
        cursor = self._collection.find().sort("created_at", 1)
        return [_to_admin_out(doc) async for doc in cursor]
