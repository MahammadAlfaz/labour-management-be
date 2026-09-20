from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.adjustments.schemas import AdjustmentCreate, AdjustmentOut
from app.modules.adjustments.service import AdjustmentService
from app.modules.admins.schemas import AdminOut

router = APIRouter(prefix="/adjustments", tags=["adjustments"])


@router.post("", response_model=AdjustmentOut, status_code=201)
async def create_adjustment(
    payload: AdjustmentCreate, current_admin: AdminOut = Depends(get_current_admin)
) -> AdjustmentOut:
    return await AdjustmentService().create_manual(payload, current_admin.id)


@router.get("/labourer/{labourer_id}", response_model=list[AdjustmentOut])
async def list_adjustments(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[AdjustmentOut]:
    return await AdjustmentService().list_for_labourer(labourer_id)
