from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from app.modules.adjustments.schemas import AdjustmentOut


class PeriodType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class PaymentStatus(str, Enum):
    PAID = "paid"
    PARTIAL = "partial"
    OVERPAID = "overpaid"


class PaymentSnapshot(BaseModel):
    wages: Decimal
    travel_expenses: Decimal
    earnings: Decimal
    unsettled_advances: Decimal
    unsettled_deductions: Decimal
    unsettled_adjustments: Decimal
    prior_balance: Decimal
    suggested_amount: Decimal


class PaymentPreview(PaymentSnapshot):
    labourer_id: str
    period_type: PeriodType
    period_start: date
    period_end: date
    unpaid_work_record_ids: list[str]
    adjustments: list[AdjustmentOut]


class PaymentCreate(BaseModel):
    labourer_id: str
    period_type: PeriodType
    period_start: date
    period_end: date
    paid_amount: Decimal = Field(ge=0)
    adjustment_reason: str | None = Field(
        default=None,
        max_length=500,
        description="Required when paid_amount differs from the calculated suggested amount",
    )


class PaymentOut(BaseModel):
    id: str
    labourer_id: str
    period_type: PeriodType
    period_start: date
    period_end: date
    calculation_snapshot: PaymentSnapshot
    paid_amount: Decimal
    adjustment_reason: str | None
    status: PaymentStatus
    created_by: str
    created_at: datetime
