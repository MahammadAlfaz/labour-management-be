from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaymentFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


class LabourerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LabourerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    work_category: str | None = Field(default=None, max_length=100)
    payment_frequency: PaymentFrequency = PaymentFrequency.DAILY


class LabourerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=20)
    work_category: str | None = Field(default=None, max_length=100)
    payment_frequency: PaymentFrequency | None = None


class LabourerOut(BaseModel):
    id: str
    name: str
    phone: str | None
    status: LabourerStatus
    work_category: str | None
    payment_frequency: PaymentFrequency
    photo_url: str | None = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
