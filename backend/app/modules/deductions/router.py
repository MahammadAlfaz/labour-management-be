from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.deductions.schemas import DeductionCreate, DeductionOut
from app.modules.deductions.service import DeductionService

router = APIRouter(prefix="/deductions", tags=["deductions"])


@router.post("", response_model=DeductionOut, status_code=201)
async def create_deduction(
    payload: DeductionCreate, current_admin: AdminOut = Depends(get_current_admin)
) -> DeductionOut:
    return await DeductionService().create(payload, current_admin.id)


@router.get("/labourer/{labourer_id}", response_model=list[DeductionOut])
async def list_deductions(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[DeductionOut]:
    return await DeductionService().list_for_labourer(labourer_id)
