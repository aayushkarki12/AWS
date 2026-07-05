"""Shift definitions and employee shift assignments."""
import uuid
from datetime import date, time
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ShiftType(StrEnum):
    DAY = "day"
    NIGHT = "night"
    TWENTY_FOUR_HOUR = "24_hours"
    CUSTOM = "custom"
    FLEXIBLE = "flexible"
    SPLIT = "split"


class Shift(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "shifts"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_type: Mapped[str] = mapped_column(String(20), nullable=False)

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    crosses_midnight: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    grace_period_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_break_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    expected_working_minutes: Mapped[int] = mapped_column(Integer, default=480, nullable=False)

    assignments: Mapped[list["ShiftAssignment"]] = relationship(back_populates="shift")


class ShiftAssignment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "shift_assignments"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    employee: Mapped["Employee"] = relationship(lazy="selectin")  # noqa: F821

    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shifts.id"), nullable=False
    )
    shift: Mapped["Shift"] = relationship(back_populates="assignments", lazy="selectin")

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    @property
    def employee_code(self) -> str:
        return self.employee.employee_code

    @property
    def employee_name(self) -> str:
        return self.employee.full_name

    @property
    def shift_name(self) -> str:
        return self.shift.name
