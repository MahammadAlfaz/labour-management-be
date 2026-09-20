from datetime import date

from fastapi import APIRouter, Depends, Header, Query

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.payments.schemas import PaymentCreate, PaymentOut, PaymentPreview, PeriodType
from app.modules.payments.service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/preview", response_model=PaymentPreview)
async def preview_payment(
    labourer_id: str = Query(...),
    period_type: PeriodType = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    _current_admin: AdminOut = Depends(get_current_admin),
) -> PaymentPreview:
    return await PaymentService().preview(labourer_id, period_type, period_start, period_end)


@router.post("", response_model=PaymentOut, status_code=201)
async def create_payment(
    payload: PaymentCreate,
    current_admin: AdminOut = Depends(get_current_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> PaymentOut:
    return await PaymentService().create_payment(payload, current_admin.id, idempotency_key)


@router.get("/labourer/{labourer_id}", response_model=list[PaymentOut])
async def list_payments(
    labourer_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[PaymentOut]:
    return await PaymentService().list_for_labourer(labourer_id)
