import { apiClient } from "@/api/client";
import type {
  ShiftAssignmentCreatePayload,
  ShiftAssignmentPublic,
  ShiftCreatePayload,
  ShiftPublic,
} from "@/types/shift";

export async function listShifts(): Promise<ShiftPublic[]> {
  const { data } = await apiClient.get<ShiftPublic[]>("/shifts");
  return data;
}

export async function createShift(payload: ShiftCreatePayload): Promise<ShiftPublic> {
  const { data } = await apiClient.post<ShiftPublic>("/shifts", payload);
  return data;
}

export async function listShiftAssignments(): Promise<ShiftAssignmentPublic[]> {
  const { data } = await apiClient.get<ShiftAssignmentPublic[]>("/shifts/assignments");
  return data;
}

export async function createShiftAssignment(
  payload: ShiftAssignmentCreatePayload,
): Promise<ShiftAssignmentPublic> {
  const { data } = await apiClient.post<ShiftAssignmentPublic>("/shifts/assignments", payload);
  return data;
}
