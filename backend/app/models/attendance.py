"""Attendance, breaks, and correction request models."""
import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LEAVE = "leave"
    HOLIDAY = "holiday"
    WFH = "wfh"
    TRAINING = "training"


class BreakType(StrEnum):
    LUNCH = "lunch"
    TEA = "tea"
    PRAYER = "prayer"
    MEDICAL = "medical"
    MEETING = "meeting"
    EMERGENCY = "emergency"
    PERSONAL = "personal"
    OTHER = "other"


class CorrectionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Attendance(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "attendance"

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    employee: Mapped["Employee"] = relationship(lazy="selectin")  # noqa: F821

    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shifts.id"), nullable=True
    )
    shift: Mapped["Shift | None"] = relationship()  # noqa: F821

    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    clock_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    clock_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_early_leave: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_missing_punch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_manual_entry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    total_working_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    breaks: Mapped[list["AttendanceBreak"]] = relationship(
        back_populates="attendance", cascade="all, delete-orphan", lazy="selectin"
    )
    corrections: Mapped[list["AttendanceCorrection"]] = relationship(
        back_populates="attendance", cascade="all, delete-orphan"
    )

    __table_args__ = ()

    @property
    def employee_code(self) -> str:
        return self.employee.employee_code

    @property
    def employee_name(self) -> str:
        return self.employee.full_name


class AttendanceBreak(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "attendance_breaks"

    attendance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance.id"), nullable=False, index=True
    )
    attendance: Mapped["Attendance"] = relationship(back_populates="breaks")

    break_type: Mapped[str] = mapped_column(String(20), nullable=False)
    break_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    break_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AttendanceCorrection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "attendance_corrections"

    attendance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance.id"), nullable=False, index=True
    )
    attendance: Mapped["Attendance"] = relationship(back_populates="corrections")

    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False
    )
    requested_by: Mapped["Employee"] = relationship(foreign_keys=[requested_by_id])  # noqa: F821

    requested_clock_in: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requested_clock_out: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    requested_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), default=CorrectionStatus.PENDING, nullable=False, index=True
    )
    # References the deciding User (not Employee) since admins may have no
    # employee profile of their own.
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approver: Mapped["User | None"] = relationship(foreign_keys=[approver_id])  # noqa: F821
    approval_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
