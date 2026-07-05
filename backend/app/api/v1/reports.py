"""Attendance summary reports with CSV/JSON export (admin only)."""
import csv
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.permissions.rbac import require_admin
from app.schemas.dashboard import EmployeeSummaryRow
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/attendance-summary",
    response_model=list[EmployeeSummaryRow],
    dependencies=[Depends(require_admin)],
)
async def attendance_summary(
    date_from: date,
    date_to: date,
    department_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[EmployeeSummaryRow]:
    return await DashboardService(db).attendance_summary(date_from, date_to, department_id)


@router.get("/attendance-summary/export", dependencies=[Depends(require_admin)])
async def export_attendance_summary(
    date_from: date,
    date_to: date,
    department_id: uuid.UUID | None = None,
    format: str = Query(default="csv", pattern="^csv$"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    rows = await DashboardService(db).attendance_summary(date_from, date_to, department_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Employee Code",
            "Full Name",
            "Present Days",
            "Absent Days",
            "Late Days",
            "Total Working Minutes",
            "Total Overtime Minutes",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.employee_code,
                row.full_name,
                row.present_days,
                row.absent_days,
                row.late_days,
                row.total_working_minutes,
                row.total_overtime_minutes,
            ]
        )
    buffer.seek(0)

    filename = f"attendance-summary-{date_from}-to-{date_to}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
