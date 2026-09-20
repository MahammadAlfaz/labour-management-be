from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from app.modules.expenses.schemas import ExpenseOut


class AttendanceStatus(str, Enum):
    FULL_DAY = "FULL_DAY"
    HALF_DAY = "HALF_DAY"
    ABSENT = "ABSENT"


class WorkRecordAssign(BaseModel):
    """Assigns a labourer to a site for a date. No attendance status yet --
    that's a separate, later action (see WorkRecordUpdate)."""

    labourer_id: str
    site_id: str
    work_date: date


class WorkRecordUpdate(BaseModel):
    status: AttendanceStatus
    amount: Decimal | None = Field(default=None, description="Required for HALF_DAY")


class AmountAdjustment(BaseModel):
    amount: Decimal = Field(ge=0)
    reason: str | None = Field(default=None, max_length=500)


class WorkRecordOut(BaseModel):
    id: str
    labourer_id: str
    site_id: str
    work_date: date
    status: AttendanceStatus | None = Field(
        default=None, description="None means assigned but not yet marked"
    )
    wage_snapshot: Decimal | None
    original_amount: Decimal
    amount: Decimal
    adjustment_reason: str | None = None
    adjusted_by: str | None = None
    adjusted_at: datetime | None = None
    payment_id: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class WorkRecordDetail(WorkRecordOut):
    expenses: list[ExpenseOut]
    total_earnings: Decimal


class LabourerBoardEntry(BaseModel):
    labourer_id: str
    labourer_name: str
    record: WorkRecordOut


class AvailableLabourer(BaseModel):
    labourer_id: str
    labourer_name: str
    unavailable_reason: str | None = Field(
        default=None, description="Set when already assigned/marked elsewhere for this date"
    )
