"""Pydantic schemas for branches and departments."""
import uuid

from pydantic import BaseModel, Field


class BranchCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=20)
    address: str | None = Field(None, max_length=500)
    timezone: str = Field(default="UTC", max_length=50)


class BranchUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    address: str | None = Field(None, max_length=500)
    timezone: str | None = Field(None, max_length=50)


class BranchPublic(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    address: str | None
    timezone: str

    model_config = {"from_attributes": True}


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=20)
    branch_id: uuid.UUID


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    branch_id: uuid.UUID | None = None


class DepartmentPublic(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    branch_id: uuid.UUID

    model_config = {"from_attributes": True}
