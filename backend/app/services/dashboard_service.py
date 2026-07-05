"""Aggregation queries backing the admin and employee dashboards, and reports."""
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import (
    Attendance,
    AttendanceBreak,
    AttendanceCorrection,
    AttendanceStatus,
    CorrectionStatus,
)
from app.models.employee import Employee
from app.repositories.attendance_repository import AttendanceRepository
from app.repositories.holiday_repository import HolidayRepository
from app.schemas.attendance import AttendancePublic
from app.schemas.dashboard import (
    AdminDashboard,
    BreakAnalysis,
    BreakTypeBreakdown,
    DailyTrendPoint,
    EmployeeDashboard,
    EmployeeSummaryRow,
    LeaderboardEntry,
)
from app.schemas.holiday import HolidayPublic

_PRESENT_LIKE_STATUSES = (AttendanceStatus.PRESENT.value, AttendanceStatus.WFH.value)


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.attendance = AttendanceRepository(session)
        self.holidays = HolidayRepository(session)

    async def admin_dashboard(self, on_date: date | None = None) -> AdminDashboard:
        on_date = on_date or date.today()

        total_employees = (
            await self.session.execute(
                select(func.count()).select_from(Employee).where(Employee.deleted_at.is_(None))
            )
        ).scalar_one()

        rows = (
            await self.session.execute(
                select(Attendance.status, func.count().label("count"))
                .where(Attendance.attendance_date == on_date, Attendance.deleted_at.is_(None))
                .group_by(Attendance.status)
            )
        ).all()

        status_counts = {row[0]: row[1] for row in rows}
        late_count = (
            await self.session.execute(
                select(func.count())
                .select_from(Attendance)
                .where(
                    Attendance.attendance_date == on_date,
                    Attendance.is_late.is_(True),
                    Attendance.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        working_now = (
            await self.session.execute(
                select(func.count())
                .select_from(Attendance)
                .where(
                    Attendance.attendance_date == on_date,
                    Attendance.clock_in.is_not(None),
                    Attendance.clock_out.is_(None),
                    Attendance.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        on_break = (
            await self.session.execute(
                select(func.count(func.distinct(AttendanceBreak.attendance_id)))
                .select_from(AttendanceBreak)
                .join(Attendance, Attendance.id == AttendanceBreak.attendance_id)
                .where(
                    Attendance.attendance_date == on_date,
                    AttendanceBreak.break_end.is_(None),
                )
            )
        ).scalar_one()

        overtime_and_avg = (
            await self.session.execute(
                select(
                    func.coalesce(func.sum(Attendance.overtime_minutes), 0),
                    func.coalesce(func.avg(Attendance.total_working_minutes), 0.0),
                ).where(
                    Attendance.attendance_date == on_date,
                    Attendance.deleted_at.is_(None),
                )
            )
        ).one()

        pending_corrections = (
            await self.session.execute(
                select(func.count())
                .select_from(AttendanceCorrection)
                .where(AttendanceCorrection.status == CorrectionStatus.PENDING)
            )
        ).scalar_one()

        present_count = status_counts.get(AttendanceStatus.PRESENT.value, 0)
        absent_count = status_counts.get(AttendanceStatus.ABSENT.value, 0)
        attendance_rate = (
            (present_count / (present_count + absent_count) * 100)
            if (present_count + absent_count) > 0
            else 0.0
        )
        on_time_rate = (
            (present_count - late_count) / present_count * 100 if present_count > 0 else 0.0
        )

        return AdminDashboard(
            total_employees=total_employees,
            present_count=present_count,
            absent_count=absent_count,
            late_count=late_count,
            on_leave_count=status_counts.get(AttendanceStatus.LEAVE.value, 0),
            working_now_count=working_now,
            on_break_count=on_break,
            total_overtime_minutes=int(overtime_and_avg[0]),
            average_working_minutes=float(overtime_and_avg[1]),
            attendance_rate=round(attendance_rate, 1),
            on_time_rate=round(max(on_time_rate, 0.0), 1),
            pending_corrections_count=pending_corrections,
        )

    async def employee_dashboard(self, employee_id: uuid.UUID) -> EmployeeDashboard:
        today = date.today()
        today_attendance = await self.attendance.get_by_employee_and_date(employee_id, today)

        month_start = today.replace(day=1)
        month_rows = (
            await self.session.execute(
                select(Attendance.status, func.count())
                .where(
                    Attendance.employee_id == employee_id,
                    Attendance.attendance_date >= month_start,
                    Attendance.attendance_date <= today,
                    Attendance.deleted_at.is_(None),
                )
                .group_by(Attendance.status)
            )
        ).all()
        month_status_counts = {row[0]: row[1] for row in month_rows}

        month_working_minutes = (
            await self.session.execute(
                select(func.coalesce(func.sum(Attendance.total_working_minutes), 0)).where(
                    Attendance.employee_id == employee_id,
                    Attendance.attendance_date >= month_start,
                    Attendance.attendance_date <= today,
                    Attendance.deleted_at.is_(None),
                )
            )
        ).scalar_one()

        recent, _ = await self.attendance.list_paginated(1, 5, employee_id=employee_id)
        upcoming_holidays = await self.holidays.list_upcoming(today, limit=5)

        return EmployeeDashboard(
            today_attendance=(
                AttendancePublic.model_validate(today_attendance) if today_attendance else None
            ),
            monthly_present_days=month_status_counts.get(AttendanceStatus.PRESENT.value, 0),
            monthly_absent_days=month_status_counts.get(AttendanceStatus.ABSENT.value, 0),
            monthly_total_working_minutes=int(month_working_minutes),
            upcoming_holidays=[HolidayPublic.model_validate(h) for h in upcoming_holidays],
            recent_attendance=[AttendancePublic.model_validate(a) for a in recent],
        )

    async def daily_trend(
        self, date_from: date, date_to: date, employee_id: uuid.UUID | None = None
    ) -> list[DailyTrendPoint]:
        query = (
            select(
                Attendance.attendance_date,
                func.count()
                .filter(Attendance.status == AttendanceStatus.PRESENT.value)
                .label("present"),
                func.count()
                .filter(Attendance.status == AttendanceStatus.ABSENT.value)
                .label("absent"),
                func.count().filter(Attendance.is_late.is_(True)).label("late"),
            )
            .where(
                Attendance.attendance_date >= date_from,
                Attendance.attendance_date <= date_to,
                Attendance.deleted_at.is_(None),
            )
            .group_by(Attendance.attendance_date)
            .order_by(Attendance.attendance_date)
        )
        if employee_id is not None:
            query = query.where(Attendance.employee_id == employee_id)

        rows = (await self.session.execute(query)).all()
        return [
            DailyTrendPoint(
                attendance_date=row[0], present_count=row[1], absent_count=row[2], late_count=row[3]
            )
            for row in rows
        ]

    async def attendance_summary(
        self, date_from: date, date_to: date, department_id: uuid.UUID | None = None
    ) -> list[EmployeeSummaryRow]:
        query = (
            select(
                Employee.id,
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                func.count().filter(Attendance.status == AttendanceStatus.PRESENT.value),
                func.count().filter(Attendance.status == AttendanceStatus.ABSENT.value),
                func.count().filter(Attendance.is_late.is_(True)),
                func.coalesce(func.sum(Attendance.total_working_minutes), 0),
                func.coalesce(func.sum(Attendance.overtime_minutes), 0),
            )
            .join(Attendance, Attendance.employee_id == Employee.id)
            .where(
                Attendance.attendance_date >= date_from,
                Attendance.attendance_date <= date_to,
                Attendance.deleted_at.is_(None),
                Employee.deleted_at.is_(None),
            )
            .group_by(Employee.id, Employee.employee_code, Employee.first_name, Employee.last_name)
            .order_by(Employee.first_name)
        )
        if department_id is not None:
            query = query.where(Employee.department_id == department_id)

        rows = (await self.session.execute(query)).all()
        return [
            EmployeeSummaryRow(
                employee_id=row[0],
                employee_code=row[1],
                full_name=f"{row[2]} {row[3]}",
                present_days=row[4],
                absent_days=row[5],
                late_days=row[6],
                total_working_minutes=int(row[7]),
                total_overtime_minutes=int(row[8]),
            )
            for row in rows
        ]

    async def break_analysis(
        self, date_from: date, date_to: date, employee_id: uuid.UUID | None = None
    ) -> BreakAnalysis:
        query = (
            select(
                AttendanceBreak.break_type,
                func.count(),
                func.coalesce(func.sum(AttendanceBreak.duration_minutes), 0),
            )
            .join(Attendance, Attendance.id == AttendanceBreak.attendance_id)
            .where(
                Attendance.attendance_date >= date_from,
                Attendance.attendance_date <= date_to,
                AttendanceBreak.duration_minutes.is_not(None),
            )
            .group_by(AttendanceBreak.break_type)
            .order_by(func.count().desc())
        )
        if employee_id is not None:
            query = query.where(Attendance.employee_id == employee_id)

        rows = (await self.session.execute(query)).all()

        by_type = [
            BreakTypeBreakdown(
                break_type=row[0],
                count=row[1],
                total_minutes=int(row[2]),
                average_minutes=round(row[2] / row[1], 1) if row[1] else 0.0,
            )
            for row in rows
        ]
        total_breaks = sum(b.count for b in by_type)
        total_minutes = sum(b.total_minutes for b in by_type)
        average_minutes = round(total_minutes / total_breaks, 1) if total_breaks else 0.0

        return BreakAnalysis(
            total_breaks=total_breaks,
            total_minutes=total_minutes,
            average_minutes=average_minutes,
            by_type=by_type,
        )

    async def leaderboard(self, days: int = 30, limit: int = 10) -> list[LeaderboardEntry]:
        today = date.today()
        period_start = today - timedelta(days=days - 1)

        rows = (
            await self.session.execute(
                select(
                    Employee.id,
                    Employee.employee_code,
                    Employee.first_name,
                    Employee.last_name,
                    func.count().filter(Attendance.status.in_(_PRESENT_LIKE_STATUSES)),
                    func.count().filter(Attendance.is_late.is_(True)),
                )
                .join(Attendance, Attendance.employee_id == Employee.id)
                .where(
                    Attendance.attendance_date >= period_start,
                    Attendance.attendance_date <= today,
                    Attendance.deleted_at.is_(None),
                    Employee.deleted_at.is_(None),
                )
                .group_by(
                    Employee.id, Employee.employee_code, Employee.first_name, Employee.last_name
                )
                .order_by(
                    func.count().filter(Attendance.status.in_(_PRESENT_LIKE_STATUSES)).desc()
                )
                .limit(limit)
            )
        ).all()

        entries: list[LeaderboardEntry] = []
        for row in rows:
            employee_id, employee_code, first_name, last_name, present_days, late_days = row
            if present_days == 0:
                continue

            history = (
                await self.session.execute(
                    select(Attendance.attendance_date, Attendance.status, Attendance.clock_in)
                    .where(
                        Attendance.employee_id == employee_id,
                        Attendance.attendance_date >= period_start,
                        Attendance.attendance_date <= today,
                        Attendance.deleted_at.is_(None),
                    )
                    .order_by(Attendance.attendance_date.desc())
                )
            ).all()

            streak = 0
            expected_date = today
            for record_date, status, _clock_in in history:
                if record_date != expected_date:
                    break
                if status not in _PRESENT_LIKE_STATUSES:
                    break
                streak += 1
                expected_date = record_date - timedelta(days=1)

            last_7 = [h for h in history if h[0] >= today - timedelta(days=6)]
            perfect_week = len(last_7) >= 5 and all(
                h[1] in _PRESENT_LIKE_STATUSES for h in last_7
            )
            early_clock_ins = sum(
                1 for _, _, clock_in in history if clock_in and clock_in.hour < 9
            )

            badges: list[str] = []
            if late_days == 0:
                badges.append("Never Late")
            if perfect_week:
                badges.append("Perfect Week")
            if early_clock_ins >= 3:
                badges.append("Early Bird")

            entries.append(
                LeaderboardEntry(
                    employee_id=employee_id,
                    employee_code=employee_code,
                    employee_name=f"{first_name} {last_name}",
                    present_days=present_days,
                    current_streak=streak,
                    badges=badges,
                )
            )

        return entries
