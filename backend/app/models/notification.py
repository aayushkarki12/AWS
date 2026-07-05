"""In-app user notifications."""
import uuid
from enum import StrEnum

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NotificationType(StrEnum):
    LATE = "late"
    MISSING_PUNCH = "missing_punch"
    CORRECTION_SUBMITTED = "correction_submitted"
    CORRECTION_APPROVED = "correction_approved"
    CORRECTION_REJECTED = "correction_rejected"
    HOLIDAY_REMINDER = "holiday_reminder"
    SHIFT_REMINDER = "shift_reminder"
    BREAK_LIMIT = "break_limit"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
