"""Pydantic schemas for the holiday calendar."""
import uuid
from datetime import date

from pydantic import BaseModel, Field


class HolidayCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    holiday_date: date
    is_optional: bool = False
    branch_id: uuid.UUID | None = None


class HolidayPublic(BaseModel):
    id: uuid.UUID
    name: str
    holiday_date: date
    is_optional: bool
    branch_id: uuid.UUID | None

    model_config = {"from_attributes": True}
