"""Pydantic schemas for employee profiles."""
import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.models.employee import EmploymentStatus


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    employee_code: str = Field(..., min_length=1, max_length=30)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=30)
    job_title: str | None = Field(None, max_length=150)
    date_of_joining: date | None = None
    department_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    role: str = Field(default="employee")


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=30)
    job_title: str | None = Field(None, max_length=150)
    date_of_joining: date | None = None
    department_id: uuid.UUID | None = None
    manager_id: uuid.UUID | None = None
    employment_status: EmploymentStatus | None = None


class EmployeeSelfUpdate(BaseModel):
    """Fields an employee may update on their own profile."""

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=30)


class EmployeePublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str
    email: EmailStr
    role_name: str
    phone: str | None
    job_title: str | None
    profile_picture_url: str | None
    date_of_joining: date | None
    employment_status: str
    department_id: uuid.UUID | None
    department_name: str | None
    branch_name: str | None
    manager_id: uuid.UUID | None
    manager_name: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PaginatedEmployees(BaseModel):
    items: list[EmployeePublic]
    total: int
    page: int
    page_size: int
