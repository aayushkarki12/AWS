"""Data access layer for attendance records."""
import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import Attendance


class AttendanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, attendance_id: uuid.UUID) -> Attendance | None:
        result = await self.session.execute(
            select(Attendance)
            .options(selectinload(Attendance.breaks))
            .where(Attendance.id == attendance_id, Attendance.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_employee_and_date(
        self, employee_id: uuid.UUID, attendance_date: date
    ) -> Attendance | None:
        result = await self.session.execute(
            select(Attendance)
            .options(selectinload(Attendance.breaks))
            .where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date,
                Attendance.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        employee_id: uuid.UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> tuple[list[Attendance], int]:
        query = select(Attendance).options(selectinload(Attendance.breaks)).where(
            Attendance.deleted_at.is_(None)
        )
        count_query = select(func.count()).select_from(Attendance).where(
            Attendance.deleted_at.is_(None)
        )

        if employee_id is not None:
            query = query.where(Attendance.employee_id == employee_id)
            count_query = count_query.where(Attendance.employee_id == employee_id)
        if status is not None:
            query = query.where(Attendance.status == status)
            count_query = count_query.where(Attendance.status == status)
        if date_from is not None:
            query = query.where(Attendance.attendance_date >= date_from)
            count_query = count_query.where(Attendance.attendance_date >= date_from)
        if date_to is not None:
            query = query.where(Attendance.attendance_date <= date_to)
            count_query = count_query.where(Attendance.attendance_date <= date_to)

        total = (await self.session.execute(count_query)).scalar_one()
        query = query.order_by(Attendance.attendance_date.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size)
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create(self, attendance: Attendance) -> Attendance:
        # New records never have breaks yet; set explicitly so the collection
        # is considered loaded and callers don't trigger an implicit lazy-load
        # (which fails under asyncpg outside of an active await context).
        if "breaks" not in attendance.__dict__:
            attendance.breaks = []
        self.session.add(attendance)
        await self.session.flush()
        return attendance
