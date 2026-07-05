"""Notification endpoints: list own notifications, mark read."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.session import get_db
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationPublic, PaginatedNotifications

router = APIRouter()


@router.get("", response_model=PaginatedNotifications)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedNotifications:
    items, total, unread = await NotificationRepository(db).list_paginated(
        user.id, page, page_size
    )
    return PaginatedNotifications(
        items=[NotificationPublic.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
        page=page,
        page_size=page_size,
    )


@router.post("/{notification_id}/read", response_model=NotificationPublic)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationPublic:
    repo = NotificationRepository(db)
    notification = await repo.get_by_id(notification_id)
    if notification is None:
        raise NotFoundError("Notification not found")
    if notification.user_id != user.id:
        raise ForbiddenError("You may only manage your own notifications")

    notification.is_read = True
    await db.commit()
    return NotificationPublic.model_validate(notification)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> None:
    await NotificationRepository(db).mark_all_read(user.id)
    await db.commit()
