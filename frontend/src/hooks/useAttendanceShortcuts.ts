import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/auth/AuthContext";
import * as attendanceApi from "@/api/attendance";
import { getApiErrorMessage } from "@/api/client";
import { useToast } from "@/components/ui/toast";

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

/**
 * Global keyboard shortcuts for employees:
 *   Ctrl+Shift+I -> Clock In
 *   Ctrl+Shift+O -> Clock Out
 *   Ctrl+Shift+B -> Start a quick break
 *
 * Note: Ctrl+Shift+I is DevTools in most browsers; we call preventDefault()
 * but browsers may still intercept it before page JS runs.
 */
export function useAttendanceShortcuts() {
  const { user } = useAuth();
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const isEmployee = user?.role === "employee";

  const { data: page } = useQuery({
    queryKey: ["attendance", "mine", "today"],
    queryFn: () =>
      attendanceApi.listAttendance({
        page: 1,
        page_size: 1,
        date_from: todayIso(),
        date_to: todayIso(),
      }),
    enabled: isEmployee,
  });
  const today = page?.items[0];
  const openBreak = today?.breaks.find((b) => b.break_end === null);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["attendance"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }

  const clockInMutation = useMutation({
    mutationFn: () => attendanceApi.clockIn(),
    onSuccess: () => {
      invalidate();
      showToast({ variant: "success", title: "Clocked in", description: "Have a great shift!" });
    },
    onError: (e) =>
      showToast({ variant: "error", title: "Couldn't clock in", description: getApiErrorMessage(e) }),
  });

  const clockOutMutation = useMutation({
    mutationFn: () => attendanceApi.clockOut(),
    onSuccess: () => {
      invalidate();
      showToast({ variant: "success", title: "Clocked out", description: "See you tomorrow!" });
    },
    onError: (e) =>
      showToast({
        variant: "error",
        title: "Couldn't clock out",
        description: getApiErrorMessage(e),
      }),
  });

  const startBreakMutation = useMutation({
    mutationFn: () => attendanceApi.startBreak("tea"),
    onSuccess: () => {
      invalidate();
      showToast({ variant: "info", title: "Break started", description: "Enjoy your break." });
    },
    onError: (e) =>
      showToast({
        variant: "error",
        title: "Couldn't start break",
        description: getApiErrorMessage(e),
      }),
  });

  // Keep the latest mutations/state in a ref so the keydown listener can be
  // attached once instead of being torn down and rebuilt on every query refetch.
  const latest = useRef({ today, openBreak, clockInMutation, clockOutMutation, startBreakMutation });
  latest.current = { today, openBreak, clockInMutation, clockOutMutation, startBreakMutation };

  useEffect(() => {
    if (!isEmployee) return;

    function onKeyDown(e: KeyboardEvent) {
      if (!e.ctrlKey || !e.shiftKey) return;
      const { today, openBreak, clockInMutation, clockOutMutation, startBreakMutation } =
        latest.current;

      const key = e.key.toLowerCase();
      if (key === "i") {
        e.preventDefault();
        if (!today?.clock_in) clockInMutation.mutate();
      } else if (key === "o") {
        e.preventDefault();
        if (today?.clock_in && !today?.clock_out && !openBreak) clockOutMutation.mutate();
      } else if (key === "b") {
        e.preventDefault();
        if (today?.clock_in && !today?.clock_out && !openBreak) startBreakMutation.mutate();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isEmployee]);
}
