"""Integration tests for attendance: clock in/out, breaks, manual entry, corrections."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.conftest import authed_client_for, create_employee_for_user, create_user_with_role

PREFIX = f"{settings.API_V1_PREFIX}/attendance"


async def _make_employee(client, db_session, email, code):
    user = await create_user_with_role(db_session, email, "employee")
    employee = await create_employee_for_user(db_session, user, code, "Test", "Worker")
    authed_client_for(client, user, "employee")
    return user, employee


async def _make_admin(client, db_session, email):
    user = await create_user_with_role(db_session, email, "admin")
    authed_client_for(client, user, "admin")
    return user


async def test_clock_in_creates_present_record(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "worker1@example.com", "ATT001")
    resp = await client.post(f"{PREFIX}/clock-in", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "present"
    assert body["clock_in"] is not None
    assert body["clock_out"] is None


async def test_double_clock_in_conflicts(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_employee(client, db_session, "worker2@example.com", "ATT002")
    await client.post(f"{PREFIX}/clock-in", json={})
    resp = await client.post(f"{PREFIX}/clock-in", json={})
    assert resp.status_code == 409


async def test_clock_out_without_clock_in_fails(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "worker3@example.com", "ATT003")
    resp = await client.post(f"{PREFIX}/clock-out", json={})
    assert resp.status_code == 409


async def test_clock_out_computes_working_minutes(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "worker4@example.com", "ATT004")
    await client.post(f"{PREFIX}/clock-in", json={})
    resp = await client.post(f"{PREFIX}/clock-out", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["clock_out"] is not None
    assert body["total_working_minutes"] is not None
    assert body["total_working_minutes"] >= 0


async def test_break_requires_clock_in(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_employee(client, db_session, "worker5@example.com", "ATT005")
    resp = await client.post(
        f"{PREFIX}/breaks/start", json={"break_type": "lunch", "is_paid": True}
    )
    assert resp.status_code == 409


async def test_break_start_and_end(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_employee(client, db_session, "worker6@example.com", "ATT006")
    await client.post(f"{PREFIX}/clock-in", json={})

    resp = await client.post(
        f"{PREFIX}/breaks/start", json={"break_type": "tea", "is_paid": True}
    )
    assert resp.status_code == 200
    break_id = resp.json()["id"]

    resp = await client.post(f"{PREFIX}/breaks/{break_id}/end")
    assert resp.status_code == 200
    assert resp.json()["duration_minutes"] is not None


async def test_cannot_start_second_open_break(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "worker7@example.com", "ATT007")
    await client.post(f"{PREFIX}/clock-in", json={})
    resp1 = await client.post(
        f"{PREFIX}/breaks/start", json={"break_type": "lunch", "is_paid": True}
    )
    assert resp1.status_code == 200

    resp2 = await client.post(
        f"{PREFIX}/breaks/start", json={"break_type": "tea", "is_paid": True}
    )
    assert resp2.status_code == 409


async def test_manual_attendance_requires_admin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, employee = await _make_employee(client, db_session, "worker8@example.com", "ATT008")
    resp = await client.post(
        f"{PREFIX}/manual",
        json={
            "employee_id": str(employee.id),
            "attendance_date": "2026-01-01",
            "status": "present",
        },
    )
    assert resp.status_code == 403


async def test_admin_can_create_manual_attendance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_client_user, employee = await _make_employee(
        client, db_session, "worker9@example.com", "ATT009"
    )
    # switch to admin session
    await _make_admin(client, db_session, "admin_manual@example.com")

    resp = await client.post(
        f"{PREFIX}/manual",
        json={
            "employee_id": str(employee.id),
            "attendance_date": "2026-01-01",
            "status": "wfh",
            "remarks": "Backdated entry",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["is_manual_entry"] is True


async def test_employee_list_attendance_scoped_to_self(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "worker10@example.com", "ATT010")
    await client.post(f"{PREFIX}/clock-in", json={})

    resp = await client.get(PREFIX)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1


async def test_correction_request_and_approval_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, employee = await _make_employee(client, db_session, "worker11@example.com", "ATT011")
    clock_in_resp = await client.post(f"{PREFIX}/clock-in", json={})
    attendance_id = clock_in_resp.json()["id"]
    await client.post(f"{PREFIX}/clock-out", json={})

    resp = await client.post(
        f"{PREFIX}/{attendance_id}/corrections",
        json={"requested_status": "half_day", "reason": "Left early for appointment"},
    )
    assert resp.status_code == 200
    correction_id = resp.json()["id"]
    assert resp.json()["status"] == "pending"

    # Employee cannot decide their own correction.
    resp = await client.patch(
        f"{PREFIX}/corrections/{correction_id}", json={"approve": True}
    )
    assert resp.status_code == 403

    await _make_admin(client, db_session, "admin_correction@example.com")
    resp = await client.patch(
        f"{PREFIX}/corrections/{correction_id}",
        json={"approve": True, "approval_remarks": "Confirmed with employee"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"

    resp = await client.get(f"{PREFIX}/{attendance_id}")
    assert resp.json()["status"] == "half_day"


async def test_employee_cannot_request_correction_for_others_attendance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, victim_employee = await _make_employee(
        client, db_session, "victim2@example.com", "ATT012"
    )
    clock_in_resp = await client.post(f"{PREFIX}/clock-in", json={})
    attendance_id = clock_in_resp.json()["id"]

    await _make_employee(client, db_session, "attacker2@example.com", "ATT013")
    resp = await client.post(
        f"{PREFIX}/{attendance_id}/corrections",
        json={"requested_status": "leave", "reason": "not mine"},
    )
    assert resp.status_code == 403


async def test_late_detection_with_shift_assignment(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_user = await _make_admin(client, db_session, "admin_shift@example.com")

    # Create a shift with a start time guaranteed to be in the past for "today",
    # so any clock-in right now is considered late.
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/shifts",
        json={
            "name": "Day Shift",
            "shift_type": "day",
            "start_time": "00:00:00",
            "end_time": "00:01:00",
            "grace_period_minutes": 0,
            "max_break_minutes": 0,
            "expected_working_minutes": 1,
        },
    )
    assert resp.status_code == 201
    shift_id = resp.json()["id"]

    employee_user, employee = await _make_employee(
        client, db_session, "lateworker@example.com", "ATT014"
    )

    authed_client_for(client, admin_user, "admin")
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/shifts/assignments",
        json={
            "employee_id": str(employee.id),
            "shift_id": shift_id,
            "effective_from": "2020-01-01",
        },
    )
    assert resp.status_code == 201

    authed_client_for(client, employee_user, "employee")
    resp = await client.post(f"{PREFIX}/clock-in", json={})
    assert resp.status_code == 200
    assert resp.json()["is_late"] is True

    resp = await client.post(
        f"{PREFIX}/breaks/start", json={"break_type": "lunch", "is_paid": True}
    )
    assert resp.status_code == 409


async def test_clock_in_with_manual_time_is_accepted_and_flagged(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "manualclock1@example.com", "ATT015")
    manual_time = datetime.now(UTC) - timedelta(minutes=15)
    resp = await client.post(
        f"{PREFIX}/clock-in", json={"clock_in_time": manual_time.isoformat()}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_manual_entry"] is True
    assert body["clock_in"].startswith(manual_time.isoformat()[:16])


async def test_clock_in_manual_time_in_future_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "manualclock2@example.com", "ATT016")
    future_time = datetime.now(UTC) + timedelta(hours=2)
    resp = await client.post(
        f"{PREFIX}/clock-in", json={"clock_in_time": future_time.isoformat()}
    )
    assert resp.status_code == 409


async def test_clock_in_manual_time_wrong_day_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "manualclock3@example.com", "ATT017")
    yesterday = datetime.now(UTC) - timedelta(days=1)
    resp = await client.post(
        f"{PREFIX}/clock-in", json={"clock_in_time": yesterday.isoformat()}
    )
    assert resp.status_code == 409


async def test_clock_out_with_manual_time_before_clock_in_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "manualclock4@example.com", "ATT018")
    resp = await client.post(f"{PREFIX}/clock-in", json={})
    clock_in_iso = resp.json()["clock_in"]
    clock_in_time = datetime.fromisoformat(clock_in_iso)

    earlier_time = clock_in_time - timedelta(hours=1)
    resp = await client.post(
        f"{PREFIX}/clock-out", json={"clock_out_time": earlier_time.isoformat()}
    )
    assert resp.status_code == 409


async def test_clock_out_with_valid_manual_time(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "manualclock5@example.com", "ATT019")
    resp = await client.post(f"{PREFIX}/clock-in", json={})
    clock_in_time = datetime.fromisoformat(resp.json()["clock_in"])

    out_time = clock_in_time + timedelta(minutes=30)
    if out_time > datetime.now(UTC):
        out_time = datetime.now(UTC)
    resp = await client.post(
        f"{PREFIX}/clock-out", json={"clock_out_time": out_time.isoformat()}
    )
    assert resp.status_code == 200
    assert resp.json()["is_manual_entry"] is True
