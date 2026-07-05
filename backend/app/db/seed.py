"""Seed baseline reference data: roles and an initial super admin account."""
import asyncio

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import Role, RoleName, User

ROLE_DESCRIPTIONS = {
    RoleName.SUPER_ADMIN: "Full system access",
    RoleName.ADMIN: "Manage employees, attendance, shifts, and reports",
    RoleName.EMPLOYEE: "Manage own attendance and profile",
}


async def seed_roles() -> dict[str, Role]:
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        roles: dict[str, Role] = {}
        for role_name, description in ROLE_DESCRIPTIONS.items():
            result = await session.execute(select(Role).where(Role.name == role_name.value))
            role = result.scalar_one_or_none()
            if role is None:
                role = Role(name=role_name.value, description=description)
                session.add(role)
                await session.flush()
            roles[role_name.value] = role
        await session.commit()
        return roles


async def seed_super_admin(email: str, password: str) -> None:
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        result = await session.execute(select(Role).where(Role.name == RoleName.SUPER_ADMIN))
        super_admin_role = result.scalar_one_or_none()
        if super_admin_role is None:
            raise RuntimeError("Roles must be seeded before creating a super admin")

        result = await session.execute(select(User).where(User.email == email.lower()))
        if result.scalar_one_or_none() is not None:
            return

        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            role_id=super_admin_role.id,
            is_active=True,
            is_email_verified=True,
        )
        session.add(user)
        await session.commit()


async def main() -> None:
    await seed_roles()
    print("Seeded roles: super_admin, admin, employee")


if __name__ == "__main__":
    asyncio.run(main())
