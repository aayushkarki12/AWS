export interface AdminDashboard {
  total_employees: number;
  present_count: number;
  absent_count: number;
  late_count: number;
  on_leave_count: number;
  working_now_count: number;
  on_break_count: number;
  total_overtime_minutes: number;
  average_working_minutes: number;
  attendance_rate: number;
  on_time_rate: number;
  pending_corrections_count: number;
}

export interface DailyTrendPoint {
  attendance_date: string;
  present_count: number;
  absent_count: number;
  late_count: number;
}

export interface BreakTypeBreakdown {
  break_type: string;
  count: number;
  total_minutes: number;
  average_minutes: number;
}

export interface BreakAnalysis {
  total_breaks: number;
  total_minutes: number;
  average_minutes: number;
  by_type: BreakTypeBreakdown[];
}

export interface LeaderboardEntry {
  employee_id: string;
  employee_code: string;
  employee_name: string;
  present_days: number;
  current_streak: number;
  badges: string[];
}

export interface BreakPublic {
  id: string;
  break_type: string;
  break_start: string;
  break_end: string | null;
  duration_minutes: number | null;
  reason: string | null;
  is_paid: boolean;
}

export interface AttendancePublic {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  shift_id: string | null;
  attendance_date: string;
  clock_in: string | null;
  clock_out: string | null;
  status: string;
  remarks: string | null;
  is_late: boolean;
  is_early_leave: boolean;
  is_missing_punch: boolean;
  is_manual_entry: boolean;
  total_working_minutes: number | null;
  overtime_minutes: number;
  breaks: BreakPublic[];
}

export interface HolidayPublic {
  id: string;
  name: string;
  holiday_date: string;
  is_optional: boolean;
  branch_id: string | null;
}

export interface EmployeeDashboard {
  today_attendance: AttendancePublic | null;
  monthly_present_days: number;
  monthly_absent_days: number;
  monthly_total_working_minutes: number;
  upcoming_holidays: HolidayPublic[];
  recent_attendance: AttendancePublic[];
}
