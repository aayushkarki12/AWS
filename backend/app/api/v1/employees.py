"""Employee management endpoints.

Admins and super admins may manage every employee. Employees may only ever
view or update their own profile — this is enforced per-record, not just by
route, since the employee role has no notion of "list everyone".
"""
import uuid

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_request_context
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.uploads import save_avatar
from app.db.session import get_db
from app.models.user import RoleName, User
from app.permissions.rbac import require_admin
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.employee import (
    EmployeeCreate,
    EmployeePublic,
    EmployeeSelfUpdate,
    EmployeeUpdate,
    PaginatedEmployees,
)
from app.services.employee_service import EmployeeService

router = APIRouter()


async def _get_own_employee_or_404(db: AsyncSession, user: User):
    employee = await EmployeeRepository(db).get_by_user_id(user.id)
    if employee is None:
        raise NotFoundError("No employee profile is associated with this account")
    return employee


@router.post(
    "",
    response_model=EmployeePublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_employee(
    payload: EmployeeCreate,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeePublic:
    ctx = get_request_context(request)
    employee = await EmployeeService(db).create_employee(
        email=payload.email,
        password=payload.password,
        employee_code=payload.employee_code,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_name=payload.role,
        phone=payload.phone,
        job_title=payload.job_title,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
        actor_id=user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return EmployeePublic.model_validate(employee)


@router.get("", response_model=PaginatedEmployees, dependencies=[Depends(require_admin)])
async def list_employees(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    department_id: uuid.UUID | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> PaginatedEmployees:
    items, total = await EmployeeService(db).list_employees(
        page, page_size, department_id, search
    )
    return PaginatedEmployees(
        items=[EmployeePublic.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=EmployeePublic)
async def get_my_profile(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> EmployeePublic:
    employee = await _get_own_employee_or_404(db, user)
    return EmployeePublic.model_validate(employee)


@router.patch("/me", response_model=EmployeePublic)
async def update_my_profile(
    payload: EmployeeSelfUpdate,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeePublic:
    employee = await _get_own_employee_or_404(db, user)
    ctx = get_request_context(request)
    updated = await EmployeeService(db).update_employee(
        employee.id,
        payload.model_dump(exclude_unset=True),
        actor_id=user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return EmployeePublic.model_validate(updated)


@router.post("/me/avatar", response_model=EmployeePublic)
async def upload_my_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeePublic:
    employee = await _get_own_employee_or_404(db, user)
    url = await save_avatar(employee.id, file)
    ctx = get_request_context(request)
    updated = await EmployeeService(db).update_employee(
        employee.id,
        {"profile_picture_url": url},
        actor_id=user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return EmployeePublic.model_validate(updated)


@router.get("/{employee_id}", response_model=EmployeePublic)
async def get_employee(
    employee_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeePublic:
    service = EmployeeService(db)
    employee = await service.get_employee_or_404(employee_id)

    if user.role.name == RoleName.EMPLOYEE and employee.user_id != user.id:
        raise ForbiddenError("You may only view your own employee record")

    return EmployeePublic.model_validate(employee)


@router.patch(
    "/{employee_id}", response_model=EmployeePublic, dependencies=[Depends(require_admin)]
)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmployeePublic:
    ctx = get_request_context(request)
    employee = await EmployeeService(db).update_employee(
        employee_id,
        payload.model_dump(exclude_unset=True),
        actor_id=user.id,
        ip_address=ctx.ip_address,
        user_agent=ctx.user_agent,
    )
    return EmployeePublic.model_validate(employee)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def deactivate_employee(
    employee_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    ctx = get_request_context(request)
    await EmployeeService(db).deactivate_employee(
        employee_id, actor_id=user.id, ip_address=ctx.ip_address, user_agent=ctx.user_agent
    )
