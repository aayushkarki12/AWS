"""Business logic for attendance, breaks, and correction workflows."""
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.attendance import (
    Attendance,
    AttendanceBreak,
    AttendanceCorrection,
    AttendanceStatus,
    BreakType,
    CorrectionStatus,
)
from app.models.notification import NotificationType
from app.models.shift import Shift
from app.models.user import RoleName
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.break_repository import BreakRepository
from app.repositories.correction_repository import CorrectionRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.shift_repository import ShiftRepository
from app.repositories.user_repository import UserRepository


def _combine_shift_datetime(
    attendance_date: date, shift_time, crosses_midnight: bool, is_end: bool
) -> datetime:
    dt = datetime.combine(attendance_date, shift_time, tzinfo=UTC)
    if crosses_midnight and is_end:
        dt += timedelta(days=1)
    return dt


class AttendanceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.attendance = AttendanceRepository(session)
        self.breaks = BreakRepository(session)
        self.corrections = CorrectionRepository(session)
        self.shifts = ShiftRepository(session)
        self.audit_logs = AuditLogRepository(session)
        self.notifications = NotificationRepository(session)
        self.employees = EmployeeRepository(session)
        self.users = UserRepository(session)

    @staticmethod
    def _resolve_punch_time(
        requested_time: datetime | None, today: date, field_label: str
    ) -> datetime:
        """Validates an employee-supplied clock-in/out time: same day, not in the future."""
        now = datetime.now(UTC)
        if requested_time is None:
            return now

        if requested_time.tzinfo is None:
            requested_time = requested_time.replace(tzinfo=UTC)

        if requested_time > now:
            raise ConflictError(f"{field_label} cannot be in the future")
        if requested_time.date() != today:
            raise ConflictError(f"{field_label} must be on today's date")
        return requested_time

    async def clock_in(
        self,
        employee_id: uuid.UUID,
        remarks: str | None,
        actor_id: uuid.UUID,
        clock_in_time: datetime | None = None,
    ) -> Attendance:
        today = datetime.now(UTC).date()
        existing = await self.attendance.get_by_employee_and_date(employee_id, today)
        if existing is not None and existing.clock_in is not None:
            raise ConflictError("You have already clocked in today")

        punch_time = self._resolve_punch_time(clock_in_time, today, "Clock-in time")
        is_manual = clock_in_time is not None
        assignment = await self.shifts.get_active_assignment(employee_id, today)
        shift = await self.shifts.get_by_id(assignment.shift_id) if assignment else None

        is_late = False
        if shift is not None:
            shift_start = _combine_shift_datetime(
                today, shift.start_time, shift.crosses_midnight, False
            )
            grace_deadline = shift_start + timedelta(minutes=shift.grace_period_minutes)
            is_late = punch_time > grace_deadline

        if existing is not None:
            existing.clock_in = punch_time
            existing.status = AttendanceStatus.PRESENT
            existing.is_late = is_late
            existing.is_manual_entry = existing.is_manual_entry or is_manual
            existing.remarks = remarks or existing.remarks
            existing.shift_id = shift.id if shift else None
            attendance = existing
        else:
            attendance = Attendance(
                employee_id=employee_id,
                shift_id=shift.id if shift else None,
                attendance_date=today,
                clock_in=punch_time,
                status=AttendanceStatus.PRESENT,
                is_late=is_late,
                is_manual_entry=is_manual,
                remarks=remarks,
            )
            # Populate in memory so the serializer doesn't trigger an async lazy-load.
            attendance.employee = await self.employees.get_by_id(employee_id)
            await self.attendance.create(attendance)

        await self.audit_logs.create(
            action="clock_in",
            entity_type="attendance",
            entity_id=str(attendance.id),
            user_id=actor_id,
            new_values={"clock_in": punch_time.isoformat(), "manual": is_manual},
        )
        await self.session.commit()
        return attendance

    async def clock_out(
        self,
        employee_id: uuid.UUID,
        remarks: str | None,
        actor_id: uuid.UUID,
        clock_out_time: datetime | None = None,
    ) -> Attendance:
        today = datetime.now(UTC).date()
        attendance = await self.attendance.get_by_employee_and_date(employee_id, today)
        if attendance is None or attendance.clock_in is None:
            raise ConflictError("You must clock in before clocking out")
        if attendance.clock_out is not None:
            raise ConflictError("You have already clocked out today")

        now = self._resolve_punch_time(clock_out_time, today, "Clock-out time")
        if now < attendance.clock_in:
            raise ConflictError("Clock-out time cannot be before clock-in time")
        if clock_out_time is not None:
            attendance.is_manual_entry = True

        attendance.clock_out = now
        if remarks:
            attendance.remarks = remarks

        shift = await self.shifts.get_by_id(attendance.shift_id) if attendance.shift_id else None
        break_minutes = sum(
            b.duration_minutes or 0 for b in attendance.breaks if b.duration_minutes
        )
        gross_minutes = int((now - attendance.clock_in).total_seconds() // 60)
        net_minutes = max(gross_minutes - break_minutes, 0)
        attendance.total_working_minutes = net_minutes

        if shift is not None:
            shift_end = _combine_shift_datetime(
                attendance.attendance_date, shift.end_time, shift.crosses_midnight, True
            )
            attendance.is_early_leave = now < shift_end
            attendance.overtime_minutes = max(net_minutes - shift.expected_working_minutes, 0)
        else:
            attendance.overtime_minutes = 0

        await self.audit_logs.create(
            action="clock_out",
            entity_type="attendance",
            entity_id=str(attendance.id),
            user_id=actor_id,
        )
        await self.session.commit()
        return attendance

    async def start_break(
        self,
        employee_id: uuid.UUID,
        break_type: BreakType,
        reason: str | None,
        is_paid: bool,
        actor_id: uuid.UUID,
    ) -> AttendanceBreak:
        today = datetime.now(UTC).date()
        attendance = await self.attendance.get_by_employee_and_date(employee_id, today)
        if attendance is None or attendance.clock_in is None:
            raise ConflictError("You must clock in before starting a break")
        if attendance.clock_out is not None:
            raise ConflictError("Cannot start a break after clocking out")

        if await self.breaks.get_open_break(attendance.id) is not None:
            raise ConflictError("You already have an open break; end it before starting another")

        shift: Shift | None = (
            await self.shifts.get_by_id(attendance.shift_id) if attendance.shift_id else None
        )
        if shift is not None:
            existing_minutes = sum(
                b.duration_minutes or 0 for b in attendance.breaks if b.duration_minutes
            )
            if existing_minutes >= shift.max_break_minutes:
                raise ConflictError(
                    f"Maximum break time of {shift.max_break_minutes} minutes has been reached"
                )

        attendance_break = AttendanceBreak(
            attendance_id=attendance.id,
            break_type=break_type,
            break_start=datetime.now(UTC),
            reason=reason,
            is_paid=is_paid,
        )
        await self.breaks.create(attendance_break)

        await self.audit_logs.create(
            action="break_start",
            entity_type="attendance_break",
            entity_id=str(attendance_break.id),
            user_id=actor_id,
        )
        await self.session.commit()
        return attendance_break

    async def end_break(
        self, employee_id: uuid.UUID, break_id: uuid.UUID, actor_id: uuid.UUID
    ) -> AttendanceBreak:
        attendance_break = await self.breaks.get_by_id(break_id)
        if attendance_break is None:
            raise NotFoundError("Break not found")

        attendance = await self.attendance.get_by_id(attendance_break.attendance_id)
        if attendance is None or attendance.employee_id != employee_id:
            raise ForbiddenError("You may only end your own breaks")
        if attendance_break.break_end is not None:
            raise ConflictError("This break has already ended")

        now = datetime.now(UTC)
        attendance_break.break_end = now
        attendance_break.duration_minutes = int(
            (now - attendance_break.break_start).total_seconds() // 60
        )

        await self.audit_logs.create(
            action="break_end",
            entity_type="attendance_break",
            entity_id=str(attendance_break.id),
            user_id=actor_id,
        )
        await self.session.commit()
        return attendance_break

    async def create_manual_attendance(
        self,
        employee_id: uuid.UUID,
        attendance_date: date,
        clock_in: datetime | None,
        clock_out: datetime | None,
        status: AttendanceStatus,
        remarks: str | None,
        actor_id: uuid.UUID,
    ) -> Attendance:
        existing = await self.attendance.get_by_employee_and_date(employee_id, attendance_date)
        if existing is not None:
            raise ConflictError("An attendance record already exists for this employee and date")

        working_minutes = None
        if clock_in and clock_out:
            working_minutes = max(int((clock_out - clock_in).total_seconds() // 60), 0)

        attendance = Attendance(
            employee_id=employee_id,
            attendance_date=attendance_date,
            clock_in=clock_in,
            clock_out=clock_out,
            status=status,
            remarks=remarks,
            is_manual_entry=True,
            is_missing_punch=bool(clock_in) != bool(clock_out),
            total_working_minutes=working_minutes,
        )
        attendance.employee = await self.employees.get_by_id(employee_id)
        await self.attendance.create(attendance)

        await self.audit_logs.create(
            action="create_manual",
            entity_type="attendance",
            entity_id=str(attendance.id),
            user_id=actor_id,
            new_values={"status": status.value, "attendance_date": str(attendance_date)},
        )
        await self.session.commit()
        return attendance

    async def get_attendance_or_404(self, attendance_id: uuid.UUID) -> Attendance:
        attendance = await self.attendance.get_by_id(attendance_id)
        if attendance is None:
            raise NotFoundError("Attendance record not found")
        return attendance

    async def list_attendance(
        self,
        page: int,
        page_size: int,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Attendance], int]:
        return await self.attendance.list_paginated(
            page, page_size, employee_id, status, date_from, date_to
        )

    async def request_correction(
        self,
        attendance_id: uuid.UUID,
        requested_by_id: uuid.UUID,
        requested_clock_in: datetime | None,
        requested_clock_out: datetime | None,
        requested_status: AttendanceStatus | None,
        reason: str,
        actor_user_id: uuid.UUID,
    ) -> AttendanceCorrection:
        attendance = await self.get_attendance_or_404(attendance_id)
        if attendance.employee_id != requested_by_id:
            raise ForbiddenError("You may only request corrections for your own attendance")

        correction = AttendanceCorrection(
            attendance_id=attendance_id,
            requested_by_id=requested_by_id,
            requested_clock_in=requested_clock_in,
            requested_clock_out=requested_clock_out,
            requested_status=requested_status,
            reason=reason,
        )
        await self.corrections.create(correction)
        await self.audit_logs.create(
            action="correction_requested",
            entity_type="attendance_correction",
            entity_id=str(correction.id),
            user_id=actor_user_id,
        )

        admins = await self.users.list_by_role_names(
            [RoleName.ADMIN.value, RoleName.SUPER_ADMIN.value]
        )
        for admin in admins:
            await self.notifications.create(
                user_id=admin.id,
                notification_type=NotificationType.CORRECTION_SUBMITTED,
                title="New attendance correction request",
                message=f"An employee has requested a correction: {reason}",
            )

        await self.session.commit()
        return correction

    async def decide_correction(
        self,
        correction_id: uuid.UUID,
        approve: bool,
        approval_remarks: str | None,
        approver_id: uuid.UUID,
    ) -> AttendanceCorrection:
        correction = await self.corrections.get_by_id(correction_id)
        if correction is None:
            raise NotFoundError("Correction request not found")
        if correction.status != CorrectionStatus.PENDING:
            raise ConflictError("This correction request has already been decided")

        correction.status = CorrectionStatus.APPROVED if approve else CorrectionStatus.REJECTED
        correction.approver_id = approver_id
        correction.approval_remarks = approval_remarks
        correction.approved_at = datetime.now(UTC)

        if approve:
            attendance = await self.get_attendance_or_404(correction.attendance_id)
            if correction.requested_clock_in is not None:
                attendance.clock_in = correction.requested_clock_in
            if correction.requested_clock_out is not None:
                attendance.clock_out = correction.requested_clock_out
            if correction.requested_status is not None:
                attendance.status = correction.requested_status
            if attendance.clock_in and attendance.clock_out:
                attendance.total_working_minutes = max(
                    int((attendance.clock_out - attendance.clock_in).total_seconds() // 60), 0
                )

        await self.audit_logs.create(
            action="correction_approved" if approve else "correction_rejected",
            entity_type="attendance_correction",
            entity_id=str(correction.id),
            user_id=approver_id,
        )

        requester = await self.employees.get_by_id(correction.requested_by_id)
        if requester is not None:
            await self.notifications.create(
                user_id=requester.user_id,
                notification_type=(
                    NotificationType.CORRECTION_APPROVED
                    if approve
                    else NotificationType.CORRECTION_REJECTED
                ),
                title=f"Correction request {'approved' if approve else 'rejected'}",
                message=approval_remarks or (
                    "Your attendance correction request has been "
                    f"{'approved' if approve else 'rejected'}."
                ),
            )

        await self.session.commit()
        return correction

    async def list_pending_corrections(self) -> list[AttendanceCorrection]:
        return await self.corrections.list_pending()

    async def list_my_corrections(self, employee_id: uuid.UUID) -> list[AttendanceCorrection]:
        return await self.corrections.list_for_employee(employee_id)
