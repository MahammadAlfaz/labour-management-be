from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.modules.attendance.schemas import AttendanceStatus
from app.modules.payments.schemas import PaymentOut


class LabourerHistoryWorkRecord(BaseModel):
    id: str
    work_date: date
    site_id: str
    site_name: str
    status: AttendanceStatus | None
    amount: Decimal
    expenses_total: Decimal
    paid: bool


class LabourerHistoryReport(BaseModel):
    labourer_id: str
    labourer_name: str
    period_start: date
    period_end: date
    work_records: list[LabourerHistoryWorkRecord]
    payments: list[PaymentOut]
    total_earnings: Decimal
    outstanding_balance: Decimal


class SiteAttendanceEntry(BaseModel):
    work_date: date
    labourer_id: str
    labourer_name: str
    status: AttendanceStatus | None
    amount: Decimal


class SiteAttendanceReport(BaseModel):
    site_id: str
    site_name: str
    period_start: date
    period_end: date
    entries: list[SiteAttendanceEntry]
    total_amount: Decimal


class WeeklySettlementEntry(BaseModel):
    labourer_id: str
    labourer_name: str
    suggested_amount: Decimal
    has_unpaid_earnings: bool


class WeeklySettlementReport(BaseModel):
    period_start: date
    period_end: date
    entries: list[WeeklySettlementEntry]
