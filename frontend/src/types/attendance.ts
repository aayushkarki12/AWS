import type { AttendancePublic, BreakPublic } from "@/types/dashboard";

export type { AttendancePublic, BreakPublic };

export interface PaginatedAttendance {
  items: AttendancePublic[];
  total: number;
  page: number;
  page_size: number;
}

export type BreakType =
  | "lunch"
  | "tea"
  | "prayer"
  | "medical"
  | "meeting"
  | "emergency"
  | "personal"
  | "other";

export type CorrectionStatus = "pending" | "approved" | "rejected";

export interface CorrectionPublic {
  id: string;
  attendance_id: string;
  requested_by_id: string;
  requested_clock_in: string | null;
  requested_clock_out: string | null;
  requested_status: string | null;
  reason: string;
  status: CorrectionStatus;
  approver_id: string | null;
  approval_remarks: string | null;
  approved_at: string | null;
}
