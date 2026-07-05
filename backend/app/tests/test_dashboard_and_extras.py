"""Tests for dashboards, notifications, holidays, reports, and audit log reads."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.conftest import authed_client_for, create_employee_for_user, create_user_with_role

ATT = f"{settings.API_V1_PREFIX}/attendance"


async def _make_employee(client, db_session, email, code):
    user = await create_user_with_role(db_session, email, "employee")
    employee = await create_employee_for_user(db_session, user, code, "Test", "Worker")
    authed_client_for(client, user, "employee")
    return user, employee


async def _make_admin(client, db_session, email):
    user = await create_user_with_role(db_session, email, "admin")
    authed_client_for(client, user, "admin")
    return user


async def test_admin_dashboard_reflects_clocked_in_employee(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "dashworker1@example.com", "DASH001")
    await client.post(f"{ATT}/clock-in", json={})

    admin = await _make_admin(client, db_session, "dashadmin1@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/admin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_employees"] == 1
    assert body["present_count"] == 1
    assert body["working_now_count"] == 1


async def test_employee_dashboard_shows_today_attendance(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "dashworker2@example.com", "DASH002")
    await client.post(f"{ATT}/clock-in", json={})

    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["today_attendance"] is not None
    assert body["monthly_present_days"] == 1


async def test_employee_dashboard_requires_employee_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(client, db_session, "dashadmin2@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/me")
    assert resp.status_code == 404


async def test_correction_submission_notifies_admins(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin = await _make_admin(client, db_session, "notifyadmin@example.com")

    _, employee = await _make_employee(client, db_session, "notifyworker@example.com", "NOTF001")
    clock_in_resp = await client.post(f"{ATT}/clock-in", json={})
    attendance_id = clock_in_resp.json()["id"]
    await client.post(
        f"{ATT}/{attendance_id}/corrections",
        json={"requested_status": "half_day", "reason": "Doctor visit"},
    )

    authed_client_for(client, admin, "admin")
    resp = await client.get(f"{settings.API_V1_PREFIX}/notifications")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["unread_count"] >= 1
    assert any(n["notification_type"] == "correction_submitted" for n in body["items"])


async def test_correction_decision_notifies_employee(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    employee_user, employee = await _make_employee(
        client, db_session, "notifyworker2@example.com", "NOTF002"
    )
    clock_in_resp = await client.post(f"{ATT}/clock-in", json={})
    attendance_id = clock_in_resp.json()["id"]
    correction_resp = await client.post(
        f"{ATT}/{attendance_id}/corrections",
        json={"requested_status": "leave", "reason": "Sick day"},
    )
    correction_id = correction_resp.json()["id"]

    admin = await _make_admin(client, db_session, "notifyadmin2@example.com")
    authed_client_for(client, admin, "admin")
    await client.patch(
        f"{ATT}/corrections/{correction_id}", json={"approve": True, "approval_remarks": "OK"}
    )

    authed_client_for(client, employee_user, "employee")
    resp = await client.get(f"{settings.API_V1_PREFIX}/notifications")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(n["notification_type"] == "correction_approved" for n in items)


async def test_mark_notification_read(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await _make_admin(client, db_session, "notifyadmin3@example.com")
    _, employee = await _make_employee(client, db_session, "notifyworker3@example.com", "NOTF003")
    clock_in_resp = await client.post(f"{ATT}/clock-in", json={})
    attendance_id = clock_in_resp.json()["id"]
    await client.post(
        f"{ATT}/{attendance_id}/corrections",
        json={"requested_status": "half_day", "reason": "x"},
    )

    authed_client_for(client, admin, "admin")
    notifications = (await client.get(f"{settings.API_V1_PREFIX}/notifications")).json()["items"]
    notification_id = notifications[0]["id"]

    resp = await client.post(f"{settings.API_V1_PREFIX}/notifications/{notification_id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True

    resp = await client.post(f"{settings.API_V1_PREFIX}/notifications/read-all")
    assert resp.status_code == 204


async def test_holiday_create_requires_admin_but_list_is_open(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "holidayworker@example.com", "HOL001")
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/holidays",
        json={"name": "New Year", "holiday_date": "2027-01-01"},
    )
    assert resp.status_code == 403

    resp = await client.get(f"{settings.API_V1_PREFIX}/holidays")
    assert resp.status_code == 200

    admin = await _make_admin(client, db_session, "holidayadmin@example.com")
    authed_client_for(client, admin, "admin")
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/holidays",
        json={"name": "New Year", "holiday_date": "2027-01-01"},
    )
    assert resp.status_code == 201


async def test_attendance_summary_report_and_csv_export(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "reportworker@example.com", "REP001")
    await client.post(f"{ATT}/clock-in", json={})
    await client.post(f"{ATT}/clock-out", json={})

    admin = await _make_admin(client, db_session, "reportadmin@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(
        f"{settings.API_V1_PREFIX}/reports/attendance-summary",
        params={"date_from": "2020-01-01", "date_to": "2030-01-01"},
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["employee_code"] == "REP001"
    assert rows[0]["present_days"] == 1

    resp = await client.get(
        f"{settings.API_V1_PREFIX}/reports/attendance-summary/export",
        params={"date_from": "2020-01-01", "date_to": "2030-01-01"},
    )
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "REP001" in resp.text


async def test_audit_logs_require_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    await _make_employee(client, db_session, "auditworker@example.com", "AUD001")
    resp = await client.get(f"{settings.API_V1_PREFIX}/audit-logs")
    assert resp.status_code == 403


async def test_audit_logs_admin_can_view(client: AsyncClient, db_session: AsyncSession) -> None:
    _, employee = await _make_employee(client, db_session, "auditworker2@example.com", "AUD002")
    await client.post(f"{ATT}/clock-in", json={})

    admin = await _make_admin(client, db_session, "auditadmin@example.com")
    authed_client_for(client, admin, "admin")
    resp = await client.get(f"{settings.API_V1_PREFIX}/audit-logs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(entry["action"] == "clock_in" for entry in body["items"])


async def test_admin_dashboard_includes_new_kpis(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "kpiworker1@example.com", "KPI001")
    await client.post(f"{ATT}/clock-in", json={})

    admin = await _make_admin(client, db_session, "kpiadmin1@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/admin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["attendance_rate"] == 100.0
    assert body["on_time_rate"] == 100.0
    assert body["pending_corrections_count"] == 0


async def test_leaderboard_reflects_present_days_and_badges(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, employee = await _make_employee(client, db_session, "lbworker1@example.com", "LB001")
    await client.post(f"{ATT}/clock-in", json={})
    await client.post(f"{ATT}/clock-out", json={})

    admin = await _make_admin(client, db_session, "lbadmin1@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/admin/leaderboard")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["employee_code"] == "LB001"
    assert entries[0]["present_days"] == 1
    assert entries[0]["current_streak"] == 1
    assert "Never Late" in entries[0]["badges"]


async def test_leaderboard_is_visible_to_employees(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "lbworker2@example.com", "LB002")
    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/admin/leaderboard")
    assert resp.status_code == 200


async def test_leaderboard_requires_authentication(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.API_V1_PREFIX}/dashboard/admin/leaderboard")
    assert resp.status_code == 401


async def test_employee_trend_scoped_to_self(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "trendworker1@example.com", "TRD001")
    await client.post(f"{ATT}/clock-in", json={})

    resp = await client.get(
        f"{settings.API_V1_PREFIX}/dashboard/me/trend",
        params={"date_from": "2020-01-01", "date_to": "2030-01-01"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["present_count"] == 1


async def test_employee_break_analysis_scoped_to_self(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "trendworker2@example.com", "TRD002")
    await client.post(f"{ATT}/clock-in", json={})
    resp = await client.post(f"{ATT}/breaks/start", json={"break_type": "tea", "is_paid": True})
    break_id = resp.json()["id"]
    await client.post(f"{ATT}/breaks/{break_id}/end")

    resp = await client.get(
        f"{settings.API_V1_PREFIX}/dashboard/me/break-analysis",
        params={"date_from": "2020-01-01", "date_to": "2030-01-01"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_breaks"] == 1
    assert body["by_type"][0]["break_type"] == "tea"


async def test_break_analysis_aggregates_by_type(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _make_employee(client, db_session, "breakworker1@example.com", "BRK001")
    await client.post(f"{ATT}/clock-in", json={})
    resp = await client.post(
        f"{ATT}/breaks/start", json={"break_type": "lunch", "is_paid": True}
    )
    break_id = resp.json()["id"]
    await client.post(f"{ATT}/breaks/{break_id}/end")

    admin = await _make_admin(client, db_session, "breakadmin1@example.com")
    authed_client_for(client, admin, "admin")

    resp = await client.get(
        f"{settings.API_V1_PREFIX}/dashboard/admin/break-analysis",
        params={"date_from": "2020-01-01", "date_to": "2030-01-01"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_breaks"] == 1
    assert body["by_type"][0]["break_type"] == "lunch"
    assert body["by_type"][0]["count"] == 1
