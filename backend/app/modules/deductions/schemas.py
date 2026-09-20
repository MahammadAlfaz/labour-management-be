from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class DeductionCreate(BaseModel):
    labourer_id: str
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=1, max_length=500)


class DeductionOut(BaseModel):
    id: str
    labourer_id: str
    amount: Decimal
    reason: str
    settled: bool
    settled_in_payment_id: str | None
    created_by: str
    created_at: datetime
