from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class ExpenseCategory(str, Enum):
    PETROL = "PETROL"
    BUS = "BUS"
    AUTO = "AUTO"
    OTHER = "OTHER"


class ExpenseCreate(BaseModel):
    category: ExpenseCategory
    amount: Decimal = Field(gt=0)
    note: str | None = Field(default=None, max_length=300)


class ExpenseUpdate(BaseModel):
    category: ExpenseCategory | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    note: str | None = Field(default=None, max_length=300)


class ExpenseOut(BaseModel):
    id: str
    daily_work_record_id: str
    category: ExpenseCategory
    amount: Decimal
    note: str | None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
