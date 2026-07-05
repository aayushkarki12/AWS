"""Shift definition and shift assignment endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.shift import Shift, ShiftAssignment
from app.permissions.rbac import require_admin, require_any_role
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.shift_repository import ShiftRepository
from app.schemas.shift import (
    ShiftAssignmentCreate,
    ShiftAssignmentPublic,
    ShiftCreate,
    ShiftPublic,
)

router = APIRouter()


@router.get("", response_model=list[ShiftPublic], dependencies=[Depends(require_any_role)])
async def list_shifts(db: AsyncSession = Depends(get_db)) -> list[ShiftPublic]:
    shifts = await ShiftRepository(db).list_all()
    return [ShiftPublic.model_validate(s) for s in shifts]


@router.post(
    "",
    response_model=ShiftPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_shift(payload: ShiftCreate, db: AsyncSession = Depends(get_db)) -> ShiftPublic:
    shift = Shift(
        name=payload.name,
        shift_type=payload.shift_type,
        start_time=payload.start_time,
        end_time=payload.end_time,
        crosses_midnight=payload.crosses_midnight,
        grace_period_minutes=payload.grace_period_minutes,
        max_break_minutes=payload.max_break_minutes,
        expected_working_minutes=payload.expected_working_minutes,
    )
    shift = await ShiftRepository(db).create(shift)
    await db.commit()
    return ShiftPublic.model_validate(shift)


@router.get(
    "/assignments",
    response_model=list[ShiftAssignmentPublic],
    dependencies=[Depends(require_admin)],
)
async def list_shift_assignments(
    db: AsyncSession = Depends(get_db),
) -> list[ShiftAssignmentPublic]:
    assignments = await ShiftRepository(db).list_assignments()
    return [ShiftAssignmentPublic.model_validate(a) for a in assignments]


@router.post(
    "/assignments",
    response_model=ShiftAssignmentPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def assign_shift(
    payload: ShiftAssignmentCreate, db: AsyncSession = Depends(get_db)
) -> ShiftAssignmentPublic:
    repo = ShiftRepository(db)
    shift = await repo.get_by_id(payload.shift_id)
    if shift is None:
        raise NotFoundError("Shift not found")

    employee = await EmployeeRepository(db).get_by_id(payload.employee_id)
    if employee is None:
        raise NotFoundError("Employee not found")

    assignment = ShiftAssignment(
        employee_id=payload.employee_id,
        shift_id=payload.shift_id,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
    )
    # Populate in memory so the serializer doesn't trigger an async lazy-load.
    assignment.shift = shift
    assignment.employee = employee
    assignment = await repo.create_assignment(assignment)
    await db.commit()
    return ShiftAssignmentPublic.model_validate(assignment)
