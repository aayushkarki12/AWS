export type ShiftType = "day" | "night" | "24_hours" | "custom" | "flexible" | "split";

export interface ShiftPublic {
  id: string;
  name: string;
  shift_type: string;
  start_time: string;
  end_time: string;
  crosses_midnight: boolean;
  grace_period_minutes: number;
  max_break_minutes: number;
  expected_working_minutes: number;
}

export interface ShiftCreatePayload {
  name: string;
  shift_type: ShiftType;
  start_time: string;
  end_time: string;
  crosses_midnight: boolean;
  grace_period_minutes: number;
  max_break_minutes: number;
  expected_working_minutes: number;
}

export interface ShiftAssignmentPublic {
  id: string;
  employee_id: string;
  employee_code: string;
  employee_name: string;
  shift_id: string;
  shift_name: string;
  effective_from: string;
  effective_to: string | null;
}

export interface ShiftAssignmentCreatePayload {
  employee_id: string;
  shift_id: string;
  effective_from: string;
  effective_to?: string;
}
