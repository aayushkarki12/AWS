import { apiClient } from "@/api/client";
import type { NotificationPublic, PaginatedNotifications } from "@/types/notification";

export async function listNotifications(page = 1, pageSize = 10): Promise<PaginatedNotifications> {
  const { data } = await apiClient.get<PaginatedNotifications>("/notifications", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function markNotificationRead(id: string): Promise<NotificationPublic> {
  const { data } = await apiClient.post<NotificationPublic>(`/notifications/${id}/read`);
  return data;
}

export async function markAllNotificationsRead(): Promise<void> {
  await apiClient.post("/notifications/read-all");
}
