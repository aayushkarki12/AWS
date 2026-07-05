"""Data access layer for in-app notifications."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: uuid.UUID, notification_type: str, title: str, message: str
    ) -> Notification:
        notification = Notification(
            user_id=user_id, notification_type=notification_type, title=title, message=message
        )
        self.session.add(notification)
        await self.session.flush()
        return notification

    async def list_paginated(
        self, user_id: uuid.UUID, page: int, page_size: int
    ) -> tuple[list[Notification], int, int]:
        base = select(Notification).where(Notification.user_id == user_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(Notification).where(
                    Notification.user_id == user_id
                )
            )
        ).scalar_one()
        unread = (
            await self.session.execute(
                select(func.count())
                .select_from(Notification)
                .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            )
        ).scalar_one()
        result = await self.session.execute(
            base.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total, unread

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.user_id == user_id, Notification.is_read.is_(False)
            )
        )
        for notification in result.scalars().all():
            notification.is_read = True
        await self.session.flush()
