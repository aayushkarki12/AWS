"""Integration tests for the authentication flow: register, login, lockout, refresh rotation."""
from httpx import AsyncClient

from app.core.config import settings

VALID_PASSWORD = "Str0ng!Passw0rd"


async def _register_and_login(client: AsyncClient, email: str = "jane@example.com") -> AsyncClient:
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "first_name": "Jane",
            "last_name": "Doe",
        },
    )
    assert resp.status_code == 201
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200
    return client


async def test_register_creates_employee(client: AsyncClient) -> None:
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "alice@example.com",
            "password": VALID_PASSWORD,
            "first_name": "Alice",
            "last_name": "Smith",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "employee"


async def test_register_duplicate_email_conflicts(client: AsyncClient) -> None:
    payload = {
        "email": "bob@example.com",
        "password": VALID_PASSWORD,
        "first_name": "Bob",
        "last_name": "Lee",
    }
    first = await client.post(f"{settings.API_V1_PREFIX}/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post(f"{settings.API_V1_PREFIX}/auth/register", json=payload)
    assert second.status_code == 409


async def test_weak_password_rejected(client: AsyncClient) -> None:
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "weak@example.com",
            "password": "password",
            "first_name": "Weak",
            "last_name": "Pw",
        },
    )
    assert resp.status_code == 422


async def test_login_success_sets_cookies(client: AsyncClient) -> None:
    await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "carl@example.com",
            "password": VALID_PASSWORD,
            "first_name": "Carl",
            "last_name": "King",
        },
    )
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "carl@example.com", "password": VALID_PASSWORD},
    )
    assert resp.status_code == 200
    assert settings.ACCESS_TOKEN_COOKIE_NAME in resp.cookies
    assert settings.REFRESH_TOKEN_COOKIE_NAME in resp.cookies


async def test_login_wrong_password_fails(client: AsyncClient) -> None:
    await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": "dave@example.com",
            "password": VALID_PASSWORD,
            "first_name": "Dave",
            "last_name": "Owens",
        },
    )
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": "dave@example.com", "password": "WrongPassw0rd!"},
    )
    assert resp.status_code == 401


async def test_account_locks_after_max_failed_attempts(client: AsyncClient) -> None:
    email = "eve@example.com"
    await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "first_name": "Eve",
            "last_name": "Adams",
        },
    )
    for _ in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
        resp = await client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            json={"email": email, "password": "WrongPassw0rd!"},
        )
        assert resp.status_code == 401

    # Next attempt, even with the correct password, should be blocked.
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert resp.status_code == 403


async def test_me_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.API_V1_PREFIX}/auth/me")
    assert resp.status_code == 401


async def test_me_returns_current_user_after_login(client: AsyncClient) -> None:
    await _register_and_login(client, email="frank@example.com")
    resp = await client.get(f"{settings.API_V1_PREFIX}/auth/me")
    assert resp.status_code == 200
    assert resp.json()["email"] == "frank@example.com"


async def test_refresh_rotates_token_and_old_one_is_revoked(client: AsyncClient) -> None:
    await _register_and_login(client, email="grace@example.com")
    old_refresh_cookie = client.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)

    resp = await client.post(f"{settings.API_V1_PREFIX}/auth/refresh")
    assert resp.status_code == 200
    new_refresh_cookie = client.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    assert new_refresh_cookie != old_refresh_cookie

    # Reusing the old (now revoked) refresh token must fail.
    client.cookies.set(settings.REFRESH_TOKEN_COOKIE_NAME, old_refresh_cookie)
    resp = await client.post(f"{settings.API_V1_PREFIX}/auth/refresh")
    assert resp.status_code == 401


async def test_logout_revokes_session(client: AsyncClient) -> None:
    await _register_and_login(client, email="heidi@example.com")
    resp = await client.post(f"{settings.API_V1_PREFIX}/auth/logout")
    assert resp.status_code == 204

    resp = await client.post(f"{settings.API_V1_PREFIX}/auth/refresh")
    assert resp.status_code == 401


async def test_change_password_requires_correct_current_password(client: AsyncClient) -> None:
    await _register_and_login(client, email="ivan@example.com")
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/change-password",
        json={"current_password": "WrongOne!23", "new_password": "NewStr0ng!Pass"},
    )
    assert resp.status_code == 401


async def test_password_reset_flow(client: AsyncClient) -> None:
    email = "judy@example.com"
    await client.post(
        f"{settings.API_V1_PREFIX}/auth/register",
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "first_name": "Judy",
            "last_name": "Moss",
        },
    )
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/password-reset/request", json={"email": email}
    )
    assert resp.status_code == 202


async def test_password_reset_unknown_email_does_not_leak(client: AsyncClient) -> None:
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/auth/password-reset/request",
        json={"email": "doesnotexist@example.com"},
    )
    assert resp.status_code == 202
