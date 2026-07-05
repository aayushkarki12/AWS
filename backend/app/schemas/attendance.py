"""Pydantic schemas for attendance, breaks, and corrections."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.attendance import AttendanceStatus, BreakType


class ClockInRequest(BaseModel):
    remarks: str | None = Field(None, max_length=1000)
    clock_in_time: datetime | None = None


class ClockOutRequest(BaseModel):
    remarks: str | None = Field(None, max_length=1000)
    clock_out_time: datetime | None = None


class ManualAttendanceCreate(BaseModel):
    employee_id: uuid.UUID
    attendance_date: date
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    status: AttendanceStatus
    remarks: str | None = Field(None, max_length=1000)


class AttendanceUpdate(BaseModel):
    clock_in: datetime | None = None
    clock_out: datetime | None = None
    status: AttendanceStatus | None = None
    remarks: str | None = Field(None, max_length=1000)


class BreakStartRequest(BaseModel):
    break_type: BreakType
    reason: str | None = Field(None, max_length=500)
    is_paid: bool = True


class BreakPublic(BaseModel):
    id: uuid.UUID
    break_type: str
    break_start: datetime
    break_end: datetime | None
    duration_minutes: int | None
    reason: str | None
    is_paid: bool

    model_config = {"from_attributes": True}


class AttendancePublic(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    shift_id: uuid.UUID | None
    attendance_date: date
    clock_in: datetime | None
    clock_out: datetime | None
    status: str
    remarks: str | None
    is_late: bool
    is_early_leave: bool
    is_missing_punch: bool
    is_manual_entry: bool
    total_working_minutes: int | None
    overtime_minutes: int
    breaks: list[BreakPublic] = []

    model_config = {"from_attributes": True}


class PaginatedAttendance(BaseModel):
    items: list[AttendancePublic]
    total: int
    page: int
    page_size: int


class CorrectionRequestCreate(BaseModel):
    requested_clock_in: datetime | None = None
    requested_clock_out: datetime | None = None
    requested_status: AttendanceStatus | None = None
    reason: str = Field(..., min_length=1, max_length=1000)


class CorrectionDecision(BaseModel):
    approve: bool
    approval_remarks: str | None = Field(None, max_length=1000)


class CorrectionPublic(BaseModel):
    id: uuid.UUID
    attendance_id: uuid.UUID
    requested_by_id: uuid.UUID
    requested_clock_in: datetime | None
    requested_clock_out: datetime | None
    requested_status: str | None
    reason: str
    status: str
    approver_id: uuid.UUID | None
    approval_remarks: str | None
    approved_at: datetime | None

    model_config = {"from_attributes": True}
