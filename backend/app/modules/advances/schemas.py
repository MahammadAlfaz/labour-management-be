from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class AdvanceCreate(BaseModel):
    labourer_id: str
    amount: Decimal = Field(gt=0)
    note: str | None = Field(default=None, max_length=300)
    given_at: date


class AdvanceOut(BaseModel):
    id: str
    labourer_id: str
    amount: Decimal
    note: str | None
    given_at: date
    settled: bool
    settled_in_payment_id: str | None
    created_by: str
    created_at: datetime
