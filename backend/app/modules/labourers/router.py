from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.labourers.schemas import LabourerCreate, LabourerOut, LabourerUpdate
from app.modules.labourers.service import LabourerService

router = APIRouter(prefix="/labourers", tags=["labourers"])


@router.post("", response_model=LabourerOut, status_code=201)
async def create_labourer(
    payload: LabourerCreate, current_admin: AdminOut = Depends(get_current_admin)
) -> LabourerOut:
    return await LabourerService().create(payload, current_admin.id)


@router.get("", response_model=list[LabourerOut])
async def list_labourers(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> list[LabourerOut]:
    return await LabourerService().list(status=status, search=search)


@router.get("/{labourer_id}", response_model=LabourerOut)
async def get_labourer(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> LabourerOut:
    return await LabourerService().get(labourer_id)


@router.patch("/{labourer_id}", response_model=LabourerOut)
async def update_labourer(
    labourer_id: str,
    payload: LabourerUpdate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> LabourerOut:
    return await LabourerService().update(labourer_id, payload, current_admin.id)


@router.post("/{labourer_id}/deactivate", response_model=LabourerOut)
async def deactivate_labourer(
    labourer_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> LabourerOut:
    return await LabourerService().set_active(labourer_id, False, current_admin.id)


@router.post("/{labourer_id}/activate", response_model=LabourerOut)
async def activate_labourer(
    labourer_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> LabourerOut:
    return await LabourerService().set_active(labourer_id, True, current_admin.id)


@router.post("/{labourer_id}/photo", response_model=LabourerOut)
async def upload_labourer_photo(
    labourer_id: str,
    file: UploadFile = File(...),
    current_admin: AdminOut = Depends(get_current_admin),
) -> LabourerOut:
    return await LabourerService().upload_photo(labourer_id, file, current_admin.id)


@router.delete("/{labourer_id}/photo", response_model=LabourerOut)
async def remove_labourer_photo(
    labourer_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> LabourerOut:
    return await LabourerService().remove_photo(labourer_id, current_admin.id)
