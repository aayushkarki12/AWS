"""Pydantic schemas for dashboard analytics."""
import uuid
from datetime import date

from pydantic import BaseModel

from app.schemas.attendance import AttendancePublic
from app.schemas.holiday import HolidayPublic


class AdminDashboard(BaseModel):
    total_employees: int
    present_count: int
    absent_count: int
    late_count: int
    on_leave_count: int
    working_now_count: int
    on_break_count: int
    total_overtime_minutes: int
    average_working_minutes: float
    attendance_rate: float
    on_time_rate: float
    pending_corrections_count: int


class BreakTypeBreakdown(BaseModel):
    break_type: str
    count: int
    total_minutes: int
    average_minutes: float


class BreakAnalysis(BaseModel):
    total_breaks: int
    total_minutes: int
    average_minutes: float
    by_type: list[BreakTypeBreakdown]


class LeaderboardEntry(BaseModel):
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    present_days: int
    current_streak: int
    badges: list[str]


class EmployeeDashboard(BaseModel):
    today_attendance: AttendancePublic | None
    monthly_present_days: int
    monthly_absent_days: int
    monthly_total_working_minutes: int
    upcoming_holidays: list[HolidayPublic]
    recent_attendance: list[AttendancePublic]


class DailyTrendPoint(BaseModel):
    attendance_date: date
    present_count: int
    absent_count: int
    late_count: int


class EmployeeSummaryRow(BaseModel):
    employee_id: uuid.UUID
    employee_code: str
    full_name: str
    present_days: int
    absent_days: int
    late_days: int
    total_working_minutes: int
    total_overtime_minutes: int
