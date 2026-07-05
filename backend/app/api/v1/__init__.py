"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1.attendance import router as attendance_router
from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.branches import router as branches_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.departments import router as departments_router
from app.api.v1.employees import router as employees_router
from app.api.v1.health import router as health_router
from app.api.v1.holidays import router as holidays_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.reports import router as reports_router
from app.api.v1.shifts import router as shifts_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(employees_router, prefix="/employees", tags=["employees"])
api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
api_router.include_router(branches_router, prefix="/branches", tags=["branches"])
api_router.include_router(shifts_router, prefix="/shifts", tags=["shifts"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
api_router.include_router(holidays_router, prefix="/holidays", tags=["holidays"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["audit-logs"])
