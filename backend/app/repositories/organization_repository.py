"""Data access layer for branches and departments."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Branch, Department


class BranchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Branch]:
        result = await self.session.execute(
            select(Branch).where(Branch.deleted_at.is_(None)).order_by(Branch.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, branch_id: uuid.UUID) -> Branch | None:
        result = await self.session.execute(
            select(Branch).where(Branch.id == branch_id, Branch.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Branch | None:
        result = await self.session.execute(select(Branch).where(Branch.code == code))
        return result.scalar_one_or_none()

    async def create(self, branch: Branch) -> Branch:
        self.session.add(branch)
        await self.session.flush()
        return branch


class DepartmentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_all(self) -> list[Department]:
        result = await self.session.execute(
            select(Department).where(Department.deleted_at.is_(None)).order_by(Department.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, department_id: uuid.UUID) -> Department | None:
        result = await self.session.execute(
            select(Department).where(
                Department.id == department_id, Department.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Department | None:
        result = await self.session.execute(select(Department).where(Department.code == code))
        return result.scalar_one_or_none()

    async def create(self, department: Department) -> Department:
        self.session.add(department)
        await self.session.flush()
        return department
