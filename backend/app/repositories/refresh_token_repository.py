"""Data access layer for refresh token / session tracking."""
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, token: RefreshToken) -> RefreshToken:
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def get_active_sessions(self, user_id: uuid.UUID) -> list[RefreshToken]:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(UTC),
            ).order_by(RefreshToken.created_at.desc())
        )
        return list(result.scalars().all())

    async def revoke(self, token: RefreshToken, replaced_by_jti: str | None = None) -> None:
        token.revoked = True
        if replaced_by_jti:
            token.replaced_by_jti = replaced_by_jti
        await self.session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        sessions = await self.get_active_sessions(user_id)
        for session in sessions:
            session.revoked = True
        await self.session.flush()

    async def revoke_by_id(self, user_id: uuid.UUID, token_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.id == token_id, RefreshToken.user_id == user_id
            )
        )
        token = result.scalar_one_or_none()
        if token is None:
            return False
        token.revoked = True
        await self.session.flush()
        return True
