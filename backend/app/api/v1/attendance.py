"""Attendance, break, and correction endpoints.

Employees may only ever clock in/out, manage breaks, and request corrections
for their own attendance. Admins can view/manage attendance for anyone and
decide correction requests.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_current_employee
from app.core.exceptions import ForbiddenError
from app.db.session import get_db
from app.models.employee import Employee
from app.models.user import RoleName, User
from app.permissions.rbac import require_admin
from app.schemas.attendance import (
    AttendancePublic,
    BreakPublic,
    BreakStartRequest,
    ClockInRequest,
    ClockOutRequest,
    CorrectionDecision,
    CorrectionPublic,
    CorrectionRequestCreate,
    ManualAttendanceCreate,
    PaginatedAttendance,
)
from app.services.attendance_service import AttendanceService

router = APIRouter()


@router.post("/clock-in", response_model=AttendancePublic)
async def clock_in(
    payload: ClockInRequest,
    employee: Employee = Depends(get_current_employee),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AttendancePublic:
    attendance = await AttendanceService(db).clock_in(
        employee.id, payload.remarks, user.id, clock_in_time=payload.clock_in_time
    )
    return AttendancePublic.model_validate(attendance)


@router.post("/clock-out", response_model=AttendancePublic)
async def clock_out(
    payload: ClockOutRequest,
    employee: Employee = Depends(get_current_employee),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AttendancePublic:
    attendance = await AttendanceService(db).clock_out(
        employee.id, payload.remarks, user.id, clock_out_time=payload.clock_out_time
    )
    return AttendancePublic.model_validate(attendance)


@router.post("/breaks/start", response_model=BreakPublic)
async def start_break(
    payload: BreakStartRequest,
    employee: Employee = Depends(get_current_employee),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BreakPublic:
    attendance_break = await AttendanceService(db).start_break(
        employee.id, payload.break_type, payload.reason, payload.is_paid, user.id
    )
    return BreakPublic.model_validate(attendance_break)


@router.post("/breaks/{break_id}/end", response_model=BreakPublic)
async def end_break(
    break_id: uuid.UUID,
    employee: Employee = Depends(get_current_employee),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> BreakPublic:
    attendance_break = await AttendanceService(db).end_break(employee.id, break_id, user.id)
    return BreakPublic.model_validate(attendance_break)


@router.post(
    "/manual",
    response_model=AttendancePublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_manual_attendance(
    payload: ManualAttendanceCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AttendancePublic:
    attendance = await AttendanceService(db).create_manual_attendance(
        employee_id=payload.employee_id,
        attendance_date=payload.attendance_date,
        clock_in=payload.clock_in,
        clock_out=payload.clock_out,
        status=payload.status,
        remarks=payload.remarks,
        actor_id=user.id,
    )
    return AttendancePublic.model_validate(attendance)


@router.get("", response_model=PaginatedAttendance)
async def list_attendance(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    employee_id: uuid.UUID | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedAttendance:
    if user.role.name == RoleName.EMPLOYEE:
        own_employee = await get_current_employee(user, db)
        employee_id = own_employee.id

    items, total = await AttendanceService(db).list_attendance(
        page, page_size, employee_id, status, date_from, date_to
    )
    return PaginatedAttendance(
        items=[AttendancePublic.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/corrections/pending", response_model=list[CorrectionPublic])
async def list_pending_corrections(
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)
) -> list[CorrectionPublic]:
    corrections = await AttendanceService(db).list_pending_corrections()
    return [CorrectionPublic.model_validate(c) for c in corrections]


@router.get("/corrections/mine", response_model=list[CorrectionPublic])
async def list_my_corrections(
    employee: Employee = Depends(get_current_employee), db: AsyncSession = Depends(get_db)
) -> list[CorrectionPublic]:
    corrections = await AttendanceService(db).list_my_corrections(employee.id)
    return [CorrectionPublic.model_validate(c) for c in corrections]


@router.patch("/corrections/{correction_id}", response_model=CorrectionPublic)
async def decide_correction(
    correction_id: uuid.UUID,
    payload: CorrectionDecision,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> CorrectionPublic:
    correction = await AttendanceService(db).decide_correction(
        correction_id, payload.approve, payload.approval_remarks, user.id
    )
    return CorrectionPublic.model_validate(correction)


@router.get("/{attendance_id}", response_model=AttendancePublic)
async def get_attendance(
    attendance_id: uuid.UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AttendancePublic:
    service = AttendanceService(db)
    attendance = await service.get_attendance_or_404(attendance_id)

    if user.role.name == RoleName.EMPLOYEE:
        own_employee = await get_current_employee(user, db)
        if attendance.employee_id != own_employee.id:
            raise ForbiddenError("You may only view your own attendance records")

    return AttendancePublic.model_validate(attendance)


@router.post("/{attendance_id}/corrections", response_model=CorrectionPublic)
async def request_correction(
    attendance_id: uuid.UUID,
    payload: CorrectionRequestCreate,
    employee: Employee = Depends(get_current_employee),
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CorrectionPublic:
    correction = await AttendanceService(db).request_correction(
        attendance_id=attendance_id,
        requested_by_id=employee.id,
        requested_clock_in=payload.requested_clock_in,
        requested_clock_out=payload.requested_clock_out,
        requested_status=payload.requested_status,
        reason=payload.reason,
        actor_user_id=user.id,
    )
    return CorrectionPublic.model_validate(correction)
