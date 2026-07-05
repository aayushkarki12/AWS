"""Pydantic schemas for reading the audit trail."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    old_values: dict | None
    new_values: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogPublic]
    total: int
    page: int
    page_size: int
