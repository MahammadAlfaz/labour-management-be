from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.repository import AdminRepository
from app.modules.admins.schemas import AdminOut

router = APIRouter(prefix="/admins", tags=["admins"])


@router.get("", response_model=list[AdminOut])
async def list_admins(_current_admin: AdminOut = Depends(get_current_admin)) -> list[AdminOut]:
    return await AdminRepository().list_all()
