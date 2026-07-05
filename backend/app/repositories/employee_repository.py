"""Data access layer for employee profiles."""
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee


class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.id == employee_id, Employee.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.user_id == user_id, Employee.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_employee_code(self, employee_code: str) -> Employee | None:
        result = await self.session.execute(
            select(Employee).where(Employee.employee_code == employee_code)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Employee], int]:
        query = select(Employee).where(Employee.deleted_at.is_(None))
        count_query = select(func.count()).select_from(Employee).where(
            Employee.deleted_at.is_(None)
        )

        if department_id is not None:
            query = query.where(Employee.department_id == department_id)
            count_query = count_query.where(Employee.department_id == department_id)

        if search:
            like = f"%{search}%"
            search_filter = (
                Employee.first_name.ilike(like)
                | Employee.last_name.ilike(like)
                | Employee.employee_code.ilike(like)
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = (await self.session.execute(count_query)).scalar_one()
        query = query.order_by(Employee.first_name).offset((page - 1) * page_size).limit(
            page_size
        )
        result = await self.session.execute(query)
        return list(result.scalars().all()), total

    async def create(self, employee: Employee) -> Employee:
        self.session.add(employee)
        await self.session.flush()
        return employee

    async def soft_delete(self, employee: Employee) -> None:
        from datetime import UTC, datetime

        employee.deleted_at = datetime.now(UTC)
        await self.session.flush()
