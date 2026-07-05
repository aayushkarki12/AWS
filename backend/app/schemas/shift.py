"""Pydantic schemas for shifts and shift assignments."""
import uuid
from datetime import date, time

from pydantic import BaseModel, Field

from app.models.shift import ShiftType


class ShiftCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    shift_type: ShiftType
    start_time: time
    end_time: time
    crosses_midnight: bool = False
    grace_period_minutes: int = Field(default=0, ge=0)
    max_break_minutes: int = Field(default=60, ge=0)
    expected_working_minutes: int = Field(default=480, ge=0)


class ShiftPublic(BaseModel):
    id: uuid.UUID
    name: str
    shift_type: str
    start_time: time
    end_time: time
    crosses_midnight: bool
    grace_period_minutes: int
    max_break_minutes: int
    expected_working_minutes: int

    model_config = {"from_attributes": True}


class ShiftAssignmentCreate(BaseModel):
    employee_id: uuid.UUID
    shift_id: uuid.UUID
    effective_from: date
    effective_to: date | None = None


class ShiftAssignmentPublic(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    shift_id: uuid.UUID
    shift_name: str
    effective_from: date
    effective_to: date | None

    model_config = {"from_attributes": True}
