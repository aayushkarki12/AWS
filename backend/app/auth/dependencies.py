"""FastAPI dependencies for extracting and validating the current authenticated user."""
import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import TokenType, decode_token
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import User
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import RequestContext


def _extract_access_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    raise UnauthorizedError("Not authenticated")


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    token = _extract_access_token(request)
    payload = decode_token(token)
    if payload is None or payload.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedError("Invalid or expired access token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError("Invalid access token") from None

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("User account is no longer active")

    return user


async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    if user.is_locked:
        raise UnauthorizedError("Account is locked")
    return user


async def get_current_employee(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> Employee:
    employee = await EmployeeRepository(db).get_by_user_id(user.id)
    if employee is None:
        raise NotFoundError("No employee profile is associated with this account")
    return employee


def get_request_context(request: Request) -> RequestContext:
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )
