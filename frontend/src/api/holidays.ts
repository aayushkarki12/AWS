import { apiClient } from "@/api/client";
import type { HolidayPublic } from "@/types/dashboard";

export async function listHolidays(): Promise<HolidayPublic[]> {
  const { data } = await apiClient.get<HolidayPublic[]>("/holidays");
  return data;
}

export async function createHoliday(payload: {
  name: string;
  holiday_date: string;
  is_optional?: boolean;
}): Promise<HolidayPublic> {
  const { data } = await apiClient.post<HolidayPublic>("/holidays", payload);
  return data;
}
