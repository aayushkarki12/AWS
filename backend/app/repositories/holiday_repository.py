"""Data access layer for the holiday calendar."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday import Holiday


class HolidayRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, holiday: Holiday) -> Holiday:
        self.session.add(holiday)
        await self.session.flush()
        return holiday

    async def list_upcoming(self, from_date: date, limit: int = 10) -> list[Holiday]:
        result = await self.session.execute(
            select(Holiday)
            .where(Holiday.holiday_date >= from_date)
            .order_by(Holiday.holiday_date)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[Holiday]:
        result = await self.session.execute(select(Holiday).order_by(Holiday.holiday_date))
        return list(result.scalars().all())
