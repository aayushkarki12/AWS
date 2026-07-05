"""Tests for shift definitions and shift assignments."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.conftest import authed_client_for, create_employee_for_user, create_user_with_role

PREFIX = f"{settings.API_V1_PREFIX}/shifts"


async def _make_employee(client, db_session, email, code):
    user = await create_user_with_role(db_session, email, "employee")
    employee = await create_employee_for_user(db_session, user, code, "Shift", "Worker")
    authed_client_for(client, user, "employee")
    return user, employee


async def _make_admin(client, db_session, email):
    user = await create_user_with_role(db_session, email, "admin")
    authed_client_for(client, user, "admin")
    return user


async def _create_shift(client: AsyncClient, name: str = "Day Shift") -> str:
    resp = await client.post(
        PREFIX,
        json={
            "name": name,
            "shift_type": "day",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
            "grace_period_minutes": 10,
            "max_break_minutes": 60,
            "expected_working_minutes": 480,
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_employee_cannot_create_shift(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_employee(client, db_session, "shiftworker1@example.com", "SFT001")
    resp = await client.post(
        PREFIX,
        json={
            "name": "Night Shift",
            "shift_type": "night",
            "start_time": "22:00:00",
            "end_time": "06:00:00",
        },
    )
    assert resp.status_code == 403


async def test_employee_can_list_shifts(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_admin(client, db_session, "shiftadmin1@example.com")
    await _create_shift(client)

    await _make_employee(client, db_session, "shiftworker2@example.com", "SFT002")
    resp = await client.get(PREFIX)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_admin_can_create_and_assign_shift(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_admin(client, db_session, "shiftadmin2@example.com")
    shift_id = await _create_shift(client, "Morning Shift")

    _, employee = await _make_employee(client, db_session, "shiftworker3@example.com", "SFT003")

    # switch back to admin to assign
    admin_user = await create_user_with_role(db_session, "shiftadmin2b@example.com", "admin")
    authed_client_for(client, admin_user, "admin")

    resp = await client.post(
        f"{PREFIX}/assignments",
        json={
            "employee_id": str(employee.id),
            "shift_id": shift_id,
            "effective_from": "2026-01-01",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["employee_code"] == "SFT003"
    assert body["employee_name"] == "Shift Worker"
    assert body["shift_name"] == "Morning Shift"

    resp = await client.get(f"{PREFIX}/assignments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_employee_cannot_list_shift_assignments(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "shiftworker4@example.com", "SFT004")
    resp = await client.get(f"{PREFIX}/assignments")
    assert resp.status_code == 403


async def test_assign_shift_requires_existing_employee(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_admin(client, db_session, "shiftadmin3@example.com")
    shift_id = await _create_shift(client, "Evening Shift")

    resp = await client.post(
        f"{PREFIX}/assignments",
        json={
            "employee_id": "00000000-0000-0000-0000-000000000000",
            "shift_id": shift_id,
            "effective_from": "2026-01-01",
        },
    )
    assert resp.status_code == 404
