import { apiClient } from "@/api/client";

export interface EmployeeSummaryRow {
  employee_id: string;
  employee_code: string;
  full_name: string;
  present_days: number;
  absent_days: number;
  late_days: number;
  total_working_minutes: number;
  total_overtime_minutes: number;
}

export async function fetchAttendanceSummary(
  dateFrom: string,
  dateTo: string,
): Promise<EmployeeSummaryRow[]> {
  const { data } = await apiClient.get<EmployeeSummaryRow[]>("/reports/attendance-summary", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export function attendanceSummaryExportUrl(dateFrom: string, dateTo: string): string {
  const base = apiClient.defaults.baseURL;
  return `${base}/reports/attendance-summary/export?date_from=${dateFrom}&date_to=${dateTo}`;
}
