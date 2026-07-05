import { apiClient } from "@/api/client";
import type {
  AdminDashboard,
  BreakAnalysis,
  DailyTrendPoint,
  EmployeeDashboard,
  LeaderboardEntry,
} from "@/types/dashboard";

export async function fetchAdminDashboard(): Promise<AdminDashboard> {
  const { data } = await apiClient.get<AdminDashboard>("/dashboard/admin");
  return data;
}

export async function fetchEmployeeDashboard(): Promise<EmployeeDashboard> {
  const { data } = await apiClient.get<EmployeeDashboard>("/dashboard/me");
  return data;
}

export async function fetchAdminTrend(
  dateFrom: string,
  dateTo: string,
): Promise<DailyTrendPoint[]> {
  const { data } = await apiClient.get<DailyTrendPoint[]>("/dashboard/admin/trend", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchBreakAnalysis(
  dateFrom: string,
  dateTo: string,
): Promise<BreakAnalysis> {
  const { data } = await apiClient.get<BreakAnalysis>("/dashboard/admin/break-analysis", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchLeaderboard(days = 30, limit = 10): Promise<LeaderboardEntry[]> {
  const { data } = await apiClient.get<LeaderboardEntry[]>("/dashboard/admin/leaderboard", {
    params: { days, limit },
  });
  return data;
}

export async function fetchMyTrend(dateFrom: string, dateTo: string): Promise<DailyTrendPoint[]> {
  const { data } = await apiClient.get<DailyTrendPoint[]>("/dashboard/me/trend", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}

export async function fetchMyBreakAnalysis(
  dateFrom: string,
  dateTo: string,
): Promise<BreakAnalysis> {
  const { data } = await apiClient.get<BreakAnalysis>("/dashboard/me/break-analysis", {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
}
