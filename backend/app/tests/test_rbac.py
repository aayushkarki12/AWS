"""RBAC enforcement tests: admins manage everyone, employees only ever see themselves."""
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.tests.conftest import authed_client_for, create_employee_for_user, create_user_with_role


async def test_employee_cannot_list_employees(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "worker@example.com", "employee")
    authed_client_for(client, user, "employee")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees")
    assert resp.status_code == 403


async def test_admin_can_list_employees(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user_with_role(db_session, "boss@example.com", "admin")
    authed_client_for(client, user, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_employee_cannot_create_employee(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "worker2@example.com", "employee")
    authed_client_for(client, user, "employee")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/employees",
        json={
            "email": "new@example.com",
            "password": "Str0ng!Passw0rd",
            "employee_code": "EMP001",
            "first_name": "New",
            "last_name": "Hire",
        },
    )
    assert resp.status_code == 403


async def test_admin_can_create_employee(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user_with_role(db_session, "boss2@example.com", "admin")
    authed_client_for(client, user, "admin")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/employees",
        json={
            "email": "hired@example.com",
            "password": "Str0ng!Passw0rd",
            "employee_code": "EMP002",
            "first_name": "Hired",
            "last_name": "Person",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["employee_code"] == "EMP002"


async def test_employee_can_view_own_profile(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_user_with_role(db_session, "self@example.com", "employee")
    employee = await create_employee_for_user(db_session, user, "EMP010", "Self", "Viewer")
    authed_client_for(client, user, "employee")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees/me")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(employee.id)

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees/{employee.id}")
    assert resp.status_code == 200


async def test_employee_cannot_view_other_employee(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    victim_user = await create_user_with_role(db_session, "victim@example.com", "employee")
    victim_employee = await create_employee_for_user(
        db_session, victim_user, "EMP020", "Victim", "Person"
    )

    attacker_user = await create_user_with_role(db_session, "attacker@example.com", "employee")
    await create_employee_for_user(db_session, attacker_user, "EMP021", "Attacker", "Person")
    authed_client_for(client, attacker_user, "employee")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees/{victim_employee.id}")
    assert resp.status_code == 403


async def test_admin_can_view_any_employee(client: AsyncClient, db_session: AsyncSession) -> None:
    target_user = await create_user_with_role(db_session, "target@example.com", "employee")
    target_employee = await create_employee_for_user(
        db_session, target_user, "EMP030", "Target", "Person"
    )

    admin_user = await create_user_with_role(db_session, "admin2@example.com", "admin")
    authed_client_for(client, admin_user, "admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees/{target_employee.id}")
    assert resp.status_code == 200


async def test_employee_cannot_update_others_via_admin_endpoint(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "worker3@example.com", "employee")
    employee = await create_employee_for_user(db_session, user, "EMP040", "Worker", "Three")
    authed_client_for(client, user, "employee")

    resp = await client.patch(
        f"{settings.API_V1_PREFIX}/employees/{employee.id}", json={"job_title": "Hacker"}
    )
    assert resp.status_code == 403


async def test_unauthenticated_request_rejected(client: AsyncClient) -> None:
    resp = await client.get(f"{settings.API_V1_PREFIX}/employees")
    assert resp.status_code == 401


async def test_super_admin_bypasses_admin_only_routes(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "root@example.com", "super_admin")
    authed_client_for(client, user, "super_admin")

    resp = await client.get(f"{settings.API_V1_PREFIX}/employees")
    assert resp.status_code == 200


async def test_branch_and_department_creation_requires_admin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "worker4@example.com", "employee")
    authed_client_for(client, user, "employee")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/branches",
        json={"name": "HQ", "code": "HQ01"},
    )
    assert resp.status_code == 403


async def test_admin_can_create_branch_and_department(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "admin3@example.com", "admin")
    authed_client_for(client, user, "admin")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/branches", json={"name": "HQ", "code": "HQ02"}
    )
    assert resp.status_code == 201
    branch_id = resp.json()["id"]

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/departments",
        json={"name": "Engineering", "code": "ENG02", "branch_id": branch_id},
    )
    assert resp.status_code == 201


async def test_admin_can_assign_department_manager_and_join_date(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "admin4@example.com", "admin")
    authed_client_for(client, user, "admin")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/branches", json={"name": "HQ", "code": "HQ03"}
    )
    branch_id = resp.json()["id"]
    resp = await client.post(
        f"{settings.API_V1_PREFIX}/departments",
        json={"name": "Sales", "code": "SLS01", "branch_id": branch_id},
    )
    department_id = resp.json()["id"]

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/employees",
        json={
            "email": "manager@example.com",
            "password": "Str0ng!Passw0rd",
            "employee_code": "MGR001",
            "first_name": "Manny",
            "last_name": "Ager",
        },
    )
    manager_id = resp.json()["id"]

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/employees",
        json={
            "email": "reportee@example.com",
            "password": "Str0ng!Passw0rd",
            "employee_code": "REP100",
            "first_name": "Rep",
            "last_name": "Ortee",
        },
    )
    employee_id = resp.json()["id"]

    resp = await client.patch(
        f"{settings.API_V1_PREFIX}/employees/{employee_id}",
        json={
            "department_id": department_id,
            "manager_id": manager_id,
            "date_of_joining": "2025-01-15",
            "job_title": "Account Executive",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["department_name"] == "Sales"
    assert body["manager_name"] == "Manny Ager"
    assert body["date_of_joining"] == "2025-01-15"
    assert body["job_title"] == "Account Executive"


async def test_employee_cannot_be_own_manager(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await create_user_with_role(db_session, "admin5@example.com", "admin")
    authed_client_for(client, user, "admin")

    resp = await client.post(
        f"{settings.API_V1_PREFIX}/employees",
        json={
            "email": "selfmanage@example.com",
            "password": "Str0ng!Passw0rd",
            "employee_code": "SELF001",
            "first_name": "Self",
            "last_name": "Manage",
        },
    )
    employee_id = resp.json()["id"]

    resp = await client.patch(
        f"{settings.API_V1_PREFIX}/employees/{employee_id}",
        json={"manager_id": employee_id},
    )
    assert resp.status_code == 409
