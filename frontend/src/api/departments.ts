import { apiClient } from "@/api/client";
import type { DepartmentPublic } from "@/types/organization";

export async function listDepartments(): Promise<DepartmentPublic[]> {
  const { data } = await apiClient.get<DepartmentPublic[]>("/departments");
  return data;
}
