"""Data access layer for attendance breaks."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceBreak


class BreakRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, break_id: uuid.UUID) -> AttendanceBreak | None:
        result = await self.session.execute(
            select(AttendanceBreak).where(AttendanceBreak.id == break_id)
        )
        return result.scalar_one_or_none()

    async def get_open_break(self, attendance_id: uuid.UUID) -> AttendanceBreak | None:
        result = await self.session.execute(
            select(AttendanceBreak).where(
                AttendanceBreak.attendance_id == attendance_id,
                AttendanceBreak.break_end.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_attendance(self, attendance_id: uuid.UUID) -> list[AttendanceBreak]:
        result = await self.session.execute(
            select(AttendanceBreak)
            .where(AttendanceBreak.attendance_id == attendance_id)
            .order_by(AttendanceBreak.break_start)
        )
        return list(result.scalars().all())

    async def create(self, attendance_break: AttendanceBreak) -> AttendanceBreak:
        self.session.add(attendance_break)
        await self.session.flush()
        return attendance_break
