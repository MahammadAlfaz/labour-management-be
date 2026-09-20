from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.sites.schemas import (
    ClientReceiptCreate,
    ClientReceiptOut,
    SiteExpenseCreate,
    SiteExpenseOut,
    SiteCreate,
    SiteFinancialSummary,
    SiteOut,
    SiteUpdate,
)
from app.modules.sites.service import SiteService

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("", response_model=SiteOut, status_code=201)
async def create_site(
    payload: SiteCreate, current_admin: AdminOut = Depends(get_current_admin)
) -> SiteOut:
    return await SiteService().create(payload, current_admin.id)


@router.get("", response_model=list[SiteOut])
async def list_sites(
    status: str | None = Query(default=None),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> list[SiteOut]:
    return await SiteService().list(status=status)


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(site_id: str, _current_admin: AdminOut = Depends(get_current_admin)) -> SiteOut:
    return await SiteService().get(site_id)


@router.patch("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: str, payload: SiteUpdate, current_admin: AdminOut = Depends(get_current_admin)
) -> SiteOut:
    return await SiteService().update(site_id, payload, current_admin.id)


@router.post("/{site_id}/close", response_model=SiteOut)
async def close_site(
    site_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> SiteOut:
    return await SiteService().set_active(site_id, False, current_admin.id)


@router.post("/{site_id}/reopen", response_model=SiteOut)
async def reopen_site(
    site_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> SiteOut:
    return await SiteService().set_active(site_id, True, current_admin.id)


@router.get("/{site_id}/financial-summary", response_model=SiteFinancialSummary)
async def get_financial_summary(
    site_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> SiteFinancialSummary:
    return await SiteService().financial_summary(site_id)


@router.get("/{site_id}/client-receipts", response_model=list[ClientReceiptOut])
async def list_client_receipts(
    site_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[ClientReceiptOut]:
    return await SiteService().list_client_receipts(site_id)


@router.post("/{site_id}/client-receipts", response_model=ClientReceiptOut, status_code=201)
async def create_client_receipt(
    site_id: str,
    payload: ClientReceiptCreate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> ClientReceiptOut:
    return await SiteService().record_client_receipt(site_id, payload, current_admin.id)


@router.get("/{site_id}/expenses", response_model=list[SiteExpenseOut])
async def list_site_expenses(site_id: str, _current_admin: AdminOut = Depends(get_current_admin)) -> list[SiteExpenseOut]:
    return await SiteService().list_site_expenses(site_id)


@router.post("/{site_id}/expenses", response_model=SiteExpenseOut, status_code=201)
async def create_site_expense(site_id: str, payload: SiteExpenseCreate, current_admin: AdminOut = Depends(get_current_admin)) -> SiteExpenseOut:
    return await SiteService().record_site_expense(site_id, payload, current_admin.id)


@router.post("/{site_id}/photo", response_model=SiteOut)
async def upload_site_photo(
    site_id: str,
    file: UploadFile = File(...),
    current_admin: AdminOut = Depends(get_current_admin),
) -> SiteOut:
    return await SiteService().upload_photo(site_id, file, current_admin.id)


@router.delete("/{site_id}/photo", response_model=SiteOut)
async def remove_site_photo(
    site_id: str, current_admin: AdminOut = Depends(get_current_admin)
) -> SiteOut:
    return await SiteService().remove_photo(site_id, current_admin.id)
