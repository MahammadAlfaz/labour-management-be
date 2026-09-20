from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.attendance.schemas import (
    AmountAdjustment,
    AvailableLabourer,
    LabourerBoardEntry,
    WorkRecordAssign,
    WorkRecordDetail,
    WorkRecordOut,
    WorkRecordUpdate,
)
from app.modules.attendance.service import AttendanceService

router = APIRouter(prefix="/work-records", tags=["attendance"])


@router.get("/board", response_model=list[LabourerBoardEntry])
async def get_board(
    site_id: str = Query(...),
    work_date: date = Query(...),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> list[LabourerBoardEntry]:
    return await AttendanceService().get_board(site_id, work_date)


@router.get("/available-labourers", response_model=list[AvailableLabourer])
async def search_available_labourers(
    work_date: date = Query(...),
    search: str | None = Query(default=None),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> list[AvailableLabourer]:
    return await AttendanceService().search_available_labourers(work_date, search)


@router.post("", response_model=WorkRecordOut, status_code=201)
async def assign_labourer(
    payload: WorkRecordAssign, current_admin: AdminOut = Depends(get_current_admin)
) -> WorkRecordOut:
    return await AttendanceService().assign(payload, current_admin.id)


@router.delete("/{record_id}", status_code=204)
async def unassign_labourer(
    record_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> None:
    await AttendanceService().unassign(record_id, current_admin.id)


@router.patch("/{record_id}/clear-attendance", response_model=WorkRecordOut)
async def clear_attendance(
    record_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> WorkRecordOut:
    return await AttendanceService().clear_attendance(record_id, current_admin.id)


@router.get("/{record_id}", response_model=WorkRecordDetail)
async def get_work_record(
    record_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> WorkRecordDetail:
    return await AttendanceService().get_detail(record_id)


@router.patch("/{record_id}", response_model=WorkRecordOut)
async def update_work_record(
    record_id: str,
    payload: WorkRecordUpdate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> WorkRecordOut:
    return await AttendanceService().update(record_id, payload, current_admin.id)


@router.patch("/{record_id}/adjust-amount", response_model=WorkRecordOut)
async def adjust_work_record_amount(
    record_id: str,
    payload: AmountAdjustment,
    current_admin: AdminOut = Depends(get_current_admin),
) -> WorkRecordOut:
    return await AttendanceService().adjust_amount(record_id, payload, current_admin.id)
