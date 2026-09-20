from fastapi import APIRouter, Depends

from app.core.deps import get_current_admin
from app.modules.admins.schemas import AdminOut
from app.modules.expenses.schemas import ExpenseCreate, ExpenseOut, ExpenseUpdate
from app.modules.expenses.service import ExpenseService

router = APIRouter(prefix="/work-records/{record_id}/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseOut, status_code=201)
async def add_expense(
    record_id: str,
    payload: ExpenseCreate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> ExpenseOut:
    return await ExpenseService().add(record_id, payload, current_admin.id)


@router.get("", response_model=list[ExpenseOut])
async def list_expenses(
    record_id: str, _current_admin: AdminOut = Depends(get_current_admin)
) -> list[ExpenseOut]:
    return await ExpenseService().list_for_record(record_id)


@router.patch("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    record_id: str,
    expense_id: str,
    payload: ExpenseUpdate,
    current_admin: AdminOut = Depends(get_current_admin),
) -> ExpenseOut:
    return await ExpenseService().update(record_id, expense_id, payload, current_admin.id)


@router.delete("/{expense_id}", status_code=204)
async def delete_expense(
    record_id: str,
    expense_id: str,
    current_admin: AdminOut = Depends(get_current_admin),
) -> None:
    await ExpenseService().delete(record_id, expense_id, current_admin.id)
