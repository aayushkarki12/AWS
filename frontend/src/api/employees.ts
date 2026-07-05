import { apiClient } from "@/api/client";
import type {
  CreateEmployeePayload,
  EmployeePublic,
  PaginatedEmployees,
  UpdateEmployeePayload,
} from "@/types/employee";

export async function listEmployees(params: {
  page?: number;
  page_size?: number;
  search?: string;
}): Promise<PaginatedEmployees> {
  const { data } = await apiClient.get<PaginatedEmployees>("/employees", { params });
  return data;
}

export async function createEmployee(payload: CreateEmployeePayload): Promise<EmployeePublic> {
  const { data } = await apiClient.post<EmployeePublic>("/employees", payload);
  return data;
}

export async function deactivateEmployee(employeeId: string): Promise<void> {
  await apiClient.delete(`/employees/${employeeId}`);
}

export async function updateEmployee(
  employeeId: string,
  payload: UpdateEmployeePayload,
): Promise<EmployeePublic> {
  const { data } = await apiClient.patch<EmployeePublic>(`/employees/${employeeId}`, payload);
  return data;
}

export async function fetchMyProfile(): Promise<EmployeePublic> {
  const { data } = await apiClient.get<EmployeePublic>("/employees/me");
  return data;
}

export async function updateMyProfile(payload: {
  first_name?: string;
  last_name?: string;
  phone?: string;
}): Promise<EmployeePublic> {
  const { data } = await apiClient.patch<EmployeePublic>("/employees/me", payload);
  return data;
}

export async function uploadMyAvatar(file: File): Promise<EmployeePublic> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<EmployeePublic>("/employees/me/avatar", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
