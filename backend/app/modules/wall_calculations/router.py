from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.wall_calculations.extraction import extract_measurements_from_image
from app.modules.wall_calculations.schemas import (
    ExtractionResult,
    WallCalculationCreate,
    WallCalculationOut,
    WallCalculationUpdate,
)
from app.modules.wall_calculations.service import WallCalculationService

router = APIRouter(prefix="/wall-calculations", tags=["wall-calculations"])


@router.post("/extract", response_model=ExtractionResult)
async def extract_measurements(
    file: UploadFile = File(...),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> ExtractionResult:
    raw = await file.read()
    return await extract_measurements_from_image(content_type=file.content_type, raw_bytes=raw)


@router.post("", response_model=WallCalculationOut, status_code=201)
async def create_calculation(
    payload: WallCalculationCreate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> WallCalculationOut:
    return await WallCalculationService().create(payload, current_admin.id)


@router.get("", response_model=list[WallCalculationOut])
async def list_calculations(
    site_id: str | None = Query(default=None),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> list[WallCalculationOut]:
    return await WallCalculationService().list(site_id=site_id)


@router.get("/{calc_id}", response_model=WallCalculationOut)
async def get_calculation(
    calc_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> WallCalculationOut:
    return await WallCalculationService().get(calc_id)


@router.patch("/{calc_id}", response_model=WallCalculationOut)
async def update_calculation(
    calc_id: str,
    payload: WallCalculationUpdate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> WallCalculationOut:
    return await WallCalculationService().update(calc_id, payload, current_admin.id)


@router.delete("/{calc_id}", status_code=204)
async def delete_calculation(
    calc_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> None:
    await WallCalculationService().delete(calc_id, current_admin.id)
