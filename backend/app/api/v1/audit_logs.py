"""Audit log read endpoints (admin only)."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.permissions.rbac import require_admin
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogPublic, PaginatedAuditLogs

router = APIRouter()


@router.get("", response_model=PaginatedAuditLogs, dependencies=[Depends(require_admin)])
async def list_audit_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    entity_type: str | None = None,
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedAuditLogs:
    items, total = await AuditLogRepository(db).list_paginated(
        page, page_size, entity_type, action, user_id
    )
    return PaginatedAuditLogs(
        items=[AuditLogPublic.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )
