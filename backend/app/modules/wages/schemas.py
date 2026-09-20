from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class WageCreate(BaseModel):
    daily_wage: Decimal = Field(gt=0)
    effective_from: date


class WageOut(BaseModel):
    id: str
    labourer_id: str
    daily_wage: Decimal
    effective_from: date
    created_by: str
    created_at: datetime
