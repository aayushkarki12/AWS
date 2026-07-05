"""Business logic for authentication, sessions, and password management."""
import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    hash_password,
    verify_password,
)
from app.models.employee import Employee
from app.models.refresh_token import RefreshToken
from app.models.user import RoleName, User
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class RequestContext:
    """Carries request metadata used for audit logging and device tracking."""

    def __init__(self, ip_address: str | None, user_agent: str | None):
        self.ip_address = ip_address
        self.user_agent = user_agent


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.employees = EmployeeRepository(session)
        self.refresh_tokens = RefreshTokenRepository(session)
        self.audit_logs = AuditLogRepository(session)

    async def _generate_employee_code(self) -> str:
        for _ in range(5):
            candidate = f"EMP-{uuid.uuid4().hex[:8].upper()}"
            if await self.employees.get_by_employee_code(candidate) is None:
                return candidate
        raise RuntimeError("Could not generate a unique employee code")

    async def register(self, email: str, password: str, first_name: str, last_name: str) -> User:
        email = email.lower().strip()
        existing = await self.users.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")

        employee_role = await self.users.get_role_by_name(RoleName.EMPLOYEE)
        if employee_role is None:
            raise NotFoundError("Default employee role is not configured")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            role_id=employee_role.id,
        )
        await self.users.create(user)

        employee = Employee(
            user_id=user.id,
            employee_code=await self._generate_employee_code(),
            first_name=first_name,
            last_name=last_name,
        )
        await self.employees.create(employee)

        await self.session.commit()
        user.role = employee_role
        return user

    async def authenticate(
        self, email: str, password: str, ctx: RequestContext
    ) -> User:
        email = email.lower().strip()
        user = await self.users.get_by_email(email)

        if user is None:
            raise UnauthorizedError("Invalid email or password")

        if user.is_locked:
            await self.audit_logs.create(
                action="login_blocked_locked",
                entity_type="user",
                user_id=user.id,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            )
            await self.session.commit()
            raise ForbiddenError(
                "Account is temporarily locked due to repeated failed login attempts"
            )

        if not user.is_active:
            raise ForbiddenError("Account is deactivated")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=settings.ACCOUNT_LOCKOUT_MINUTES
                )
                await self.audit_logs.create(
                    action="account_locked",
                    entity_type="user",
                    user_id=user.id,
                    ip_address=ctx.ip_address,
                    user_agent=ctx.user_agent,
                )
            await self.session.commit()
            raise UnauthorizedError("Invalid email or password")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(UTC)
        await self.audit_logs.create(
            action="login_success",
            entity_type="user",
            user_id=user.id,
            ip_address=ctx.ip_address,
            user_agent=ctx.user_agent,
        )
        await self.session.commit()
        return user

    async def issue_tokens(
        self, user: User, ctx: RequestContext, remember_me: bool = False
    ) -> tuple[str, str, int]:
        """Returns (access_token, refresh_token, access_expires_in_seconds)."""
        access_token, _ = create_access_token(str(user.id), user.role.name)
        refresh_token, refresh_jti = create_refresh_token(str(user.id), remember_me)

        payload = decode_token(refresh_token)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)

        await self.refresh_tokens.create(
            RefreshToken(
                user_id=user.id,
                jti=refresh_jti,
                token_hash=_hash_token(refresh_token),
                expires_at=expires_at,
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
            )
        )
        await self.session.commit()
        return access_token, refresh_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def rotate_refresh_token(
        self, refresh_token: str, ctx: RequestContext
    ) -> tuple[str, str, int]:
        payload = decode_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise UnauthorizedError("Invalid or expired refresh token")

        jti = payload["jti"]
        stored = await self.refresh_tokens.get_by_jti(jti)
        if stored is None or stored.revoked:
            if stored is not None:
                # Reuse of a revoked token indicates possible theft: revoke the whole chain.
                await self.refresh_tokens.revoke_all_for_user(stored.user_id)
                await self.session.commit()
            raise UnauthorizedError("Refresh token has been revoked")

        if stored.expires_at < datetime.now(UTC):
            raise UnauthorizedError("Refresh token has expired")

        if stored.token_hash != _hash_token(refresh_token):
            raise UnauthorizedError("Invalid refresh token")

        user = await self.users.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User account is no longer active")

        new_access, new_refresh, expires_in = await self.issue_tokens(user, ctx)
        # Fetch the newly created token's jti to link rotation chain.
        new_payload = decode_token(new_refresh)
        await self.refresh_tokens.revoke(stored, replaced_by_jti=new_payload["jti"])
        await self.session.commit()
        return new_access, new_refresh, expires_in

    async def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload is None:
            return
        stored = await self.refresh_tokens.get_by_jti(payload.get("jti", ""))
        if stored is not None:
            await self.refresh_tokens.revoke(stored)
            await self.session.commit()

    async def logout_all_devices(self, user_id: uuid.UUID) -> None:
        await self.refresh_tokens.revoke_all_for_user(user_id)
        await self.session.commit()

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()

    async def request_password_reset(self, email: str) -> str | None:
        user = await self.users.get_by_email(email.lower().strip())
        if user is None:
            return None
        token = generate_password_reset_token()
        user.password_reset_token = _hash_token(token)
        user.password_reset_expires_at = datetime.now(UTC) + timedelta(hours=1)
        await self.session.commit()
        return token

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        hashed = _hash_token(token)
        user = await self.users.get_by_password_reset_token(hashed)
        if (
            user is None
            or user.password_reset_expires_at is None
            or user.password_reset_expires_at < datetime.now(UTC)
        ):
            raise UnauthorizedError("Invalid or expired password reset token")

        user.hashed_password = hash_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        user.failed_login_attempts = 0
        user.locked_until = None
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.commit()

    async def list_sessions(self, user_id: uuid.UUID) -> list[RefreshToken]:
        return await self.refresh_tokens.get_active_sessions(user_id)

    async def revoke_session(self, user_id: uuid.UUID, token_id: uuid.UUID) -> bool:
        return await self.refresh_tokens.revoke_by_id(user_id, token_id)
