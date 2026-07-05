"""Data access layer for shifts and shift assignments."""
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shift import Shift, ShiftAssignment


class ShiftRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, shift_id: uuid.UUID) -> Shift | None:
        result = await self.session.execute(
            select(Shift).where(Shift.id == shift_id, Shift.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Shift]:
        result = await self.session.execute(
            select(Shift).where(Shift.deleted_at.is_(None)).order_by(Shift.name)
        )
        return list(result.scalars().all())

    async def create(self, shift: Shift) -> Shift:
        self.session.add(shift)
        await self.session.flush()
        return shift

    async def get_active_assignment(
        self, employee_id: uuid.UUID, on_date: date
    ) -> ShiftAssignment | None:
        result = await self.session.execute(
            select(ShiftAssignment)
            .where(
                ShiftAssignment.employee_id == employee_id,
                ShiftAssignment.effective_from <= on_date,
                (ShiftAssignment.effective_to.is_(None))
                | (ShiftAssignment.effective_to >= on_date),
            )
            .order_by(ShiftAssignment.effective_from.desc())
        )
        return result.scalars().first()

    async def create_assignment(self, assignment: ShiftAssignment) -> ShiftAssignment:
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def list_assignments(self) -> list[ShiftAssignment]:
        result = await self.session.execute(
            select(ShiftAssignment).order_by(ShiftAssignment.effective_from.desc())
        )
        return list(result.scalars().all())
