from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AdjustmentCreate(BaseModel):
    labourer_id: str
    amount: Decimal = Field(description="Signed: positive = owed to labourer, negative = owed back")
    reason: str = Field(min_length=1, max_length=500)


class AdjustmentOut(BaseModel):
    id: str
    labourer_id: str
    amount: Decimal
    reason: str
    related_record_type: str | None
    related_record_id: str | None
    settled: bool
    settled_in_payment_id: str | None
    created_by: str
    created_at: datetime
