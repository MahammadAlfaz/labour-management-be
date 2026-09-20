from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.advances.schemas import AdvanceCreate, AdvanceOut
from app.modules.advances.service import AdvanceService

router = APIRouter(prefix="/advances", tags=["advances"])


@router.post("", response_model=AdvanceOut, status_code=201)
async def create_advance(
    payload: AdvanceCreate, current_admin: AdminOut = Depends(get_current_admin)
) -> AdvanceOut:
    return await AdvanceService().create(payload, current_admin.id)


@router.get("/labourer/{labourer_id}", response_model=list[AdvanceOut])
async def list_advances(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[AdvanceOut]:
    return await AdvanceService().list_for_labourer(labourer_id)
