"""Pydantic schemas for in-app notifications."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationPublic(BaseModel):
    id: uuid.UUID
    notification_type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    items: list[NotificationPublic]
    total: int
    unread_count: int
    page: int
    page_size: int
