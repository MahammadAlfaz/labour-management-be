from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.wages.schemas import WageCreate, WageOut
from app.modules.wages.service import WageService

router = APIRouter(prefix="/labourers/{labourer_id}/wages", tags=["wages"])


@router.post("", response_model=WageOut, status_code=201)
async def add_wage(
    labourer_id: str,
    payload: WageCreate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> WageOut:
    return await WageService().add_wage(labourer_id, payload, current_admin.id)


@router.get("", response_model=list[WageOut])
async def list_wages(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[WageOut]:
    return await WageService().list_history(labourer_id)
