"""Dashboard analytics endpoints."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_employee
from app.db.session import get_db
from app.models.employee import Employee
from app.permissions.rbac import require_admin, require_any_role
from app.schemas.dashboard import (
    AdminDashboard,
    BreakAnalysis,
    DailyTrendPoint,
    EmployeeDashboard,
    LeaderboardEntry,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/admin", response_model=AdminDashboard, dependencies=[Depends(require_admin)])
async def admin_dashboard(
    on_date: date | None = None, db: AsyncSession = Depends(get_db)
) -> AdminDashboard:
    return await DashboardService(db).admin_dashboard(on_date)


@router.get(
    "/admin/trend",
    response_model=list[DailyTrendPoint],
    dependencies=[Depends(require_admin)],
)
async def admin_trend(
    date_from: date, date_to: date, db: AsyncSession = Depends(get_db)
) -> list[DailyTrendPoint]:
    return await DashboardService(db).daily_trend(date_from, date_to)


@router.get(
    "/admin/break-analysis",
    response_model=BreakAnalysis,
    dependencies=[Depends(require_admin)],
)
async def admin_break_analysis(
    date_from: date, date_to: date, db: AsyncSession = Depends(get_db)
) -> BreakAnalysis:
    return await DashboardService(db).break_analysis(date_from, date_to)


@router.get(
    "/admin/leaderboard",
    response_model=list[LeaderboardEntry],
    dependencies=[Depends(require_any_role)],
)
async def admin_leaderboard(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[LeaderboardEntry]:
    # Open to every role: the leaderboard only surfaces name/present-days/streak/badges,
    # nothing sensitive, and employees seeing where they rank is the point of it.
    return await DashboardService(db).leaderboard(days=days, limit=limit)


@router.get("/me", response_model=EmployeeDashboard)
async def employee_dashboard(
    employee: Employee = Depends(get_current_employee), db: AsyncSession = Depends(get_db)
) -> EmployeeDashboard:
    return await DashboardService(db).employee_dashboard(employee.id)


@router.get("/me/trend", response_model=list[DailyTrendPoint])
async def employee_trend(
    date_from: date,
    date_to: date,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
) -> list[DailyTrendPoint]:
    return await DashboardService(db).daily_trend(date_from, date_to, employee_id=employee.id)


@router.get("/me/break-analysis", response_model=BreakAnalysis)
async def employee_break_analysis(
    date_from: date,
    date_to: date,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
) -> BreakAnalysis:
    return await DashboardService(db).break_analysis(date_from, date_to, employee_id=employee.id)
