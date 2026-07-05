import { apiClient } from "@/api/client";
import type {
  AttendancePublic,
  BreakPublic,
  BreakType,
  CorrectionPublic,
  PaginatedAttendance,
} from "@/types/attendance";

export async function clockIn(remarks?: string, clockInTime?: string): Promise<AttendancePublic> {
  const { data } = await apiClient.post<AttendancePublic>("/attendance/clock-in", {
    remarks,
    clock_in_time: clockInTime,
  });
  return data;
}

export async function clockOut(
  remarks?: string,
  clockOutTime?: string,
): Promise<AttendancePublic> {
  const { data } = await apiClient.post<AttendancePublic>("/attendance/clock-out", {
    remarks,
    clock_out_time: clockOutTime,
  });
  return data;
}

export async function startBreak(
  break_type: BreakType,
  reason?: string,
  is_paid = true,
): Promise<BreakPublic> {
  const { data } = await apiClient.post<BreakPublic>("/attendance/breaks/start", {
    break_type,
    reason,
    is_paid,
  });
  return data;
}

export async function endBreak(breakId: string): Promise<BreakPublic> {
  const { data } = await apiClient.post<BreakPublic>(`/attendance/breaks/${breakId}/end`);
  return data;
}

export interface ListAttendanceParams {
  page?: number;
  page_size?: number;
  employee_id?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
}

export async function listAttendance(
  params: ListAttendanceParams = {},
): Promise<PaginatedAttendance> {
  const { data } = await apiClient.get<PaginatedAttendance>("/attendance", { params });
  return data;
}

export async function requestCorrection(
  attendanceId: string,
  payload: {
    requested_clock_in?: string;
    requested_clock_out?: string;
    requested_status?: string;
    reason: string;
  },
): Promise<CorrectionPublic> {
  const { data } = await apiClient.post<CorrectionPublic>(
    `/attendance/${attendanceId}/corrections`,
    payload,
  );
  return data;
}

export async function listMyCorrections(): Promise<CorrectionPublic[]> {
  const { data } = await apiClient.get<CorrectionPublic[]>("/attendance/corrections/mine");
  return data;
}

export async function listPendingCorrections(): Promise<CorrectionPublic[]> {
  const { data } = await apiClient.get<CorrectionPublic[]>("/attendance/corrections/pending");
  return data;
}

export async function decideCorrection(
  correctionId: string,
  approve: boolean,
  approval_remarks?: string,
): Promise<CorrectionPublic> {
  const { data } = await apiClient.patch<CorrectionPublic>(
    `/attendance/corrections/${correctionId}`,
    { approve, approval_remarks },
  );
  return data;
}
