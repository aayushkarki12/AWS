"""Data access layer for User and Role entities."""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Role, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.role)).where(
                User.id == user_id, User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.role)).where(
                User.email == email.lower(), User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_password_reset_token(self, token: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.password_reset_token == token, User.deleted_at.is_(None)
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_by_role_names(self, role_names: list[str]) -> list[User]:
        result = await self.session.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(Role.name.in_(role_names), User.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def save(self, user: User) -> User:
        await self.session.flush()
        return user
