"""Authentication endpoints: register, login, logout, refresh, password management, sessions."""
import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_request_context
from app.core.config import settings
from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.rate_limit import limiter
from app.core.security import decode_token, generate_csrf_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    SessionPublic,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import AuthService

router = APIRouter()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME * 86400,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path=f"{settings.API_V1_PREFIX}/auth",
    )
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=generate_csrf_token(),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME * 86400,
        httponly=False,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME, path=f"{settings.API_V1_PREFIX}/auth"
    )
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path="/")


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def register(
    request: Request, payload: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> UserPublic:
    service = AuthService(db)
    user = await service.register(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UserPublic(
        id=user.id, email=user.email, role=user.role.name, is_active=user.is_active,
        is_email_verified=user.is_email_verified,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    ctx = get_request_context(request)
    user = await service.authenticate(payload.email, payload.password, ctx)
    access_token, refresh_token, expires_in = await service.issue_tokens(
        user, ctx, remember_me=payload.remember_me
    )
    _set_auth_cookies(response, access_token, refresh_token)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserPublic(
            id=user.id, email=user.email, role=user.role.name, is_active=user.is_active,
            is_email_verified=user.is_email_verified,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        raise UnauthorizedError("Refresh token missing")

    service = AuthService(db)
    ctx = get_request_context(request)
    access_token, new_refresh_token, expires_in = await service.rotate_refresh_token(
        refresh_token, ctx
    )
    _set_auth_cookies(response, access_token, new_refresh_token)

    payload = decode_token(access_token)
    user = await service.users.get_by_id(uuid.UUID(payload["sub"]))
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserPublic(
            id=user.id, email=user.email, role=user.role.name, is_active=user.is_active,
            is_email_verified=user.is_email_verified,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> None:
    refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if refresh_token:
        await AuthService(db).logout(refresh_token)
    _clear_auth_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_devices(
    response: Response,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await AuthService(db).logout_all_devices(user.id)
    _clear_auth_cookies(response)


@router.get("/me", response_model=UserPublic)
async def get_me(user: User = Depends(get_current_active_user)) -> UserPublic:
    return UserPublic(
        id=user.id, email=user.email, role=user.role.name, is_active=user.is_active,
        is_email_verified=user.is_email_verified,
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await AuthService(db).change_password(
        user, payload.current_password, payload.new_password
    )
    _clear_auth_cookies(response)


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def request_password_reset(
    request: Request, payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)
) -> dict:
    # Always return a generic response to avoid leaking whether the email exists.
    await AuthService(db).request_password_reset(payload.email)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)
) -> None:
    await AuthService(db).confirm_password_reset(payload.token, payload.new_password)


@router.get("/sessions", response_model=list[SessionPublic])
async def list_sessions(
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[SessionPublic]:
    current_refresh = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    current_jti = None
    if current_refresh:
        decoded = decode_token(current_refresh)
        current_jti = decoded.get("jti") if decoded else None

    sessions = await AuthService(db).list_sessions(user.id)
    return [
        SessionPublic(
            id=s.id,
            device_label=s.device_label,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            created_at=s.created_at.isoformat(),
            expires_at=s.expires_at.isoformat(),
            is_current=(s.jti == current_jti),
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    revoked = await AuthService(db).revoke_session(user.id, session_id)
    if not revoked:
        raise NotFoundError("Session not found")
