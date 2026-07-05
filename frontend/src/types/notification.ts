export interface NotificationPublic {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedNotifications {
  items: NotificationPublic[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}
