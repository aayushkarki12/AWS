"""Tests for employee self-service profile editing and avatar upload."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.conftest import authed_client_for, create_employee_for_user, create_user_with_role

PREFIX = f"{settings.API_V1_PREFIX}/employees"

_PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d494844520000000100000001080600000"
    "01f15c4890000000a49444154789c6360000002000155a24a"
    "9d0000000049454e44ae426082"
)


async def _make_employee(client, db_session, email, code):
    user = await create_user_with_role(db_session, email, "employee")
    employee = await create_employee_for_user(db_session, user, code, "Original", "Name")
    authed_client_for(client, user, "employee")
    return user, employee


async def test_employee_can_update_own_name_and_phone(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "profileworker1@example.com", "PROF001")
    resp = await client.patch(
        f"{PREFIX}/me", json={"first_name": "Updated", "phone": "555-1234"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["first_name"] == "Updated"
    assert body["last_name"] == "Name"
    assert body["phone"] == "555-1234"


async def test_avatar_upload_rejects_non_image(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "profileworker2@example.com", "PROF002")
    resp = await client.post(
        f"{PREFIX}/me/avatar",
        files={"file": ("evil.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 422


async def test_avatar_upload_accepts_valid_image(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "profileworker3@example.com", "PROF003")
    resp = await client.post(
        f"{PREFIX}/me/avatar",
        files={"file": ("avatar.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["profile_picture_url"] is not None
    assert body["profile_picture_url"].endswith(".png")

    resp = await client.get(f"{PREFIX}/me")
    assert resp.json()["profile_picture_url"] == body["profile_picture_url"]


async def test_avatar_upload_rejects_oversized_file(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "profileworker4@example.com", "PROF004")
    oversized = b"\x00" * (settings.MAX_AVATAR_SIZE_MB * 1024 * 1024 + 1)
    resp = await client.post(
        f"{PREFIX}/me/avatar",
        files={"file": ("big.png", oversized, "image/png")},
    )
    assert resp.status_code == 422
