"""Data access layer for attendance correction requests."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceCorrection, CorrectionStatus


class CorrectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, correction_id: uuid.UUID) -> AttendanceCorrection | None:
        result = await self.session.execute(
            select(AttendanceCorrection).where(AttendanceCorrection.id == correction_id)
        )
        return result.scalar_one_or_none()

    async def list_pending(self) -> list[AttendanceCorrection]:
        result = await self.session.execute(
            select(AttendanceCorrection)
            .where(AttendanceCorrection.status == CorrectionStatus.PENDING)
            .order_by(AttendanceCorrection.created_at)
        )
        return list(result.scalars().all())

    async def list_for_employee(self, employee_id: uuid.UUID) -> list[AttendanceCorrection]:
        result = await self.session.execute(
            select(AttendanceCorrection)
            .where(AttendanceCorrection.requested_by_id == employee_id)
            .order_by(AttendanceCorrection.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, correction: AttendanceCorrection) -> AttendanceCorrection:
        self.session.add(correction)
        await self.session.flush()
        return correction
