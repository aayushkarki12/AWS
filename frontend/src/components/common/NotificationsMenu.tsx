import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck } from "lucide-react";

import * as notificationsApi from "@/api/notifications";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/utils/cn";

function timeAgo(iso: string): string {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function NotificationsMenu() {
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const previousUnread = useRef<number | null>(null);

  const { data } = useQuery({
    queryKey: ["notifications", "bell"],
    queryFn: () => notificationsApi.listNotifications(1, 8),
    refetchInterval: 15000,
  });

  useEffect(() => {
    if (!data) return;
    if (previousUnread.current !== null && data.unread_count > previousUnread.current) {
      const latest = data.items[0];
      if (latest) {
        showToast({ variant: "info", title: latest.title, description: latest.message });
      }
    }
    previousUnread.current = data.unread_count;
  }, [data, showToast]);

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const markAllReadMutation = useMutation({
    mutationFn: notificationsApi.markAllNotificationsRead,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const unreadCount = data?.unread_count ?? 0;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label="Notifications"
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-ink-400 transition-colors hover:bg-ink-800 hover:text-ink-100"
      >
        <Bell className="h-[18px] w-[18px]" strokeWidth={1.75} />
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-4 animate-pop items-center justify-center rounded-full bg-coral-deep px-1 text-[10px] font-semibold text-ink-fixed-inverse">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-20 mt-2 w-80 animate-slide-up rounded-lg border border-ink-700 bg-ink-900 shadow-panel">
            <div className="flex items-center justify-between border-b border-ink-800 px-4 py-3">
              <span className="text-[13px] font-medium text-ink-100">Notifications</span>
              {unreadCount > 0 && (
                <button
                  onClick={() => markAllReadMutation.mutate()}
                  className="flex items-center gap-1 text-[12px] text-amber-glow hover:underline"
                >
                  <CheckCheck className="h-3 w-3" /> Mark all read
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto">
              {!data || data.items.length === 0 ? (
                <p className="p-4 text-[13px] text-ink-500">You&rsquo;re all caught up.</p>
              ) : (
                data.items.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => !n.is_read && markReadMutation.mutate(n.id)}
                    className={cn(
                      "flex w-full flex-col gap-0.5 border-b border-ink-800/60 px-4 py-3 text-left last:border-0 hover:bg-ink-800/50",
                      !n.is_read && "bg-amber-glow/5",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      {!n.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-glow" />}
                      <span className="text-[13px] font-medium text-ink-100">{n.title}</span>
                    </div>
                    <p className="text-[12px] text-ink-400">{n.message}</p>
                    <span className="text-[11px] text-ink-600">{timeAgo(n.created_at)}</span>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
