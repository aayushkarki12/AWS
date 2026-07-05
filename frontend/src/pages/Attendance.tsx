import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Coffee, LogIn, LogOut, RefreshCw, Soup, Square, X } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import * as attendanceApi from "@/api/attendance";
import { getApiErrorMessage } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import type { AttendancePublic, BreakType } from "@/types/attendance";
import { formatDate, formatMinutes, formatTime, statusLabel } from "@/utils/format";

const OTHER_BREAK_TYPES: BreakType[] = ["prayer", "medical", "meeting", "emergency", "personal", "other"];

function statusVariant(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "present" || status === "wfh") return "success";
  if (status === "half_day" || status === "leave") return "warning";
  if (status === "absent") return "danger";
  return "neutral";
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function ClockControls() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [useManualTime, setUseManualTime] = useState(false);
  const [manualTime, setManualTime] = useState("");
  const [otherBreakType, setOtherBreakType] = useState<BreakType>("prayer");

  const { data: page, isFetching } = useQuery({
    queryKey: ["attendance", "mine", "today"],
    queryFn: () =>
      attendanceApi.listAttendance({
        page: 1,
        page_size: 1,
        date_from: todayIso(),
        date_to: todayIso(),
      }),
  });
  const today = page?.items[0];
  const openBreak = today?.breaks.find((b) => b.break_end === null);
  const isClockedIn = Boolean(today?.clock_in && !today?.clock_out);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["attendance"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    setManualTime("");
  }

  const manualTimeIso =
    useManualTime && manualTime ? new Date(manualTime).toISOString() : undefined;

  const clockInMutation = useMutation({
    mutationFn: () => attendanceApi.clockIn(undefined, manualTimeIso),
    onSuccess: invalidate,
    onError: (e) => setError(getApiErrorMessage(e)),
  });
  const clockOutMutation = useMutation({
    mutationFn: () => attendanceApi.clockOut(undefined, manualTimeIso),
    onSuccess: invalidate,
    onError: (e) => setError(getApiErrorMessage(e)),
  });
  const startBreakMutation = useMutation({
    mutationFn: (breakType: BreakType) => attendanceApi.startBreak(breakType),
    onSuccess: invalidate,
    onError: (e) => setError(getApiErrorMessage(e)),
  });
  const endBreakMutation = useMutation({
    mutationFn: (breakId: string) => attendanceApi.endBreak(breakId),
    onSuccess: invalidate,
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  const canClockIn = !isClockedIn && !today?.clock_out && !(useManualTime && !manualTime);
  const canClockOut = isClockedIn && !openBreak && !(useManualTime && !manualTime);
  const canStartBreak = isClockedIn && !openBreak;

  return (
    <div className="flex flex-col gap-4">
      {error && (
        <p className="rounded-lg border border-coral-deep/30 bg-coral-deep/10 px-3 py-2 text-[13px] text-coral-glow">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Today&rsquo;s Status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-display text-2xl text-ink-50">
              {isClockedIn ? "Clocked In" : today?.clock_out ? "Clocked Out" : "Not Clocked In"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Today&rsquo;s Hours</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="font-display text-2xl text-amber-glow">
              {((today?.total_working_minutes ?? 0) / 60).toFixed(2)}h
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            {today?.status ? (
              <div className="flex flex-wrap gap-1.5">
                <Badge variant={statusVariant(today.status)}>{statusLabel(today.status)}</Badge>
                {today.is_late && <Badge variant="warning">Late</Badge>}
              </div>
            ) : (
              <Badge variant="neutral">Not Set</Badge>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button className="flex-1" onClick={() => clockInMutation.mutate()} disabled={!canClockIn}>
              <LogIn className="h-4 w-4" /> Clock In
            </Button>
            <Button
              className="flex-1"
              variant="secondary"
              onClick={() => clockOutMutation.mutate()}
              disabled={!canClockOut}
            >
              <LogOut className="h-4 w-4" /> Clock Out
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1.5 text-[13px] font-medium text-ink-300">
            <Coffee className="h-4 w-4 text-ink-500" /> Break Actions:
          </span>

          <Button
            size="sm"
            variant="secondary"
            disabled={!canStartBreak || startBreakMutation.isPending}
            onClick={() => startBreakMutation.mutate("tea")}
          >
            <Coffee className="h-3.5 w-3.5" /> Start Coffee Break
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={!canStartBreak || startBreakMutation.isPending}
            onClick={() => startBreakMutation.mutate("lunch")}
          >
            <Soup className="h-3.5 w-3.5" /> Start Lunch Break
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={!openBreak || endBreakMutation.isPending}
            onClick={() => openBreak && endBreakMutation.mutate(openBreak.id)}
          >
            <Square className="h-3.5 w-3.5" /> End Break
          </Button>

          <div className="ml-auto flex items-center gap-2">
            <Select
              value={otherBreakType}
              onChange={(e) => setOtherBreakType(e.target.value as BreakType)}
              className="h-8 w-36 text-[13px]"
              disabled={!canStartBreak}
            >
              {OTHER_BREAK_TYPES.map((bt) => (
                <option key={bt} value={bt}>
                  {statusLabel(bt)}
                </option>
              ))}
            </Select>
            <Button
              size="sm"
              variant="ghost"
              disabled={!canStartBreak || startBreakMutation.isPending}
              onClick={() => startBreakMutation.mutate(otherBreakType)}
            >
              Start
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-[13px] text-ink-400">
            <input
              type="checkbox"
              checked={useManualTime}
              onChange={(e) => {
                setUseManualTime(e.target.checked);
                if (!e.target.checked) setManualTime("");
              }}
              className="h-3.5 w-3.5 rounded border-ink-600 bg-ink-900 accent-amber-glow"
            />
            Enter time manually
          </label>
          {useManualTime && (
            <Input
              type="datetime-local"
              value={manualTime}
              onChange={(e) => setManualTime(e.target.value)}
              className="max-w-56"
            />
          )}
          {isFetching && <span className="ml-auto text-[12px] text-ink-500">Refreshing…</span>}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-[12px] text-ink-500">
        <span>
          <kbd className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5 font-mono text-ink-300">
            Ctrl+Shift+I
          </kbd>{" "}
          Clock in
        </span>
        <span>
          <kbd className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5 font-mono text-ink-300">
            Ctrl+Shift+O
          </kbd>{" "}
          Clock out
        </span>
        <span>
          <kbd className="rounded border border-ink-600 bg-ink-800 px-1.5 py-0.5 font-mono text-ink-300">
            Ctrl+Shift+B
          </kbd>{" "}
          Start break
        </span>
      </div>
    </div>
  );
}

const CORRECTION_STATUSES = [
  { value: "", label: "No change" },
  { value: "present", label: "Present" },
  { value: "absent", label: "Absent" },
  { value: "half_day", label: "Half Day" },
  { value: "leave", label: "Leave" },
  { value: "holiday", label: "Holiday" },
  { value: "wfh", label: "WFH" },
  { value: "training", label: "Training" },
];

function toDatetimeLocal(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function CorrectionDialog({
  attendance,
  onClose,
}: {
  attendance: AttendancePublic | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");
  const [requestedStatus, setRequestedStatus] = useState("");
  const [requestedClockIn, setRequestedClockIn] = useState("");
  const [requestedClockOut, setRequestedClockOut] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Pre-fill the time fields with the record's current values whenever a new
  // attendance row is targeted, so they're genuinely editable (not just a
  // placeholder) — otherwise submitting without touching them silently drops
  // the time correction.
  useEffect(() => {
    if (!attendance) return;
    setRequestedClockIn(toDatetimeLocal(attendance.clock_in));
    setRequestedClockOut(toDatetimeLocal(attendance.clock_out));
  }, [attendance]);

  function resetAndClose() {
    setReason("");
    setRequestedStatus("");
    setRequestedClockIn("");
    setRequestedClockOut("");
    onClose();
  }

  const mutation = useMutation({
    mutationFn: () =>
      attendanceApi.requestCorrection(attendance!.id, {
        reason,
        requested_status: requestedStatus || undefined,
        requested_clock_in: requestedClockIn ? new Date(requestedClockIn).toISOString() : undefined,
        requested_clock_out: requestedClockOut
          ? new Date(requestedClockOut).toISOString()
          : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["corrections"] });
      resetAndClose();
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  return (
    <Dialog open={Boolean(attendance)} onClose={resetAndClose} title="Request a correction">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
        className="flex flex-col gap-4"
      >
        {error && <p className="text-[13px] text-coral-glow">{error}</p>}
        <p className="text-[13px] text-ink-400">
          {attendance && formatDate(attendance.attendance_date)} — specify what should change,
          then explain why.
        </p>

        <div className="flex flex-col gap-1.5">
          <Label>Corrected status</Label>
          <Select value={requestedStatus} onChange={(e) => setRequestedStatus(e.target.value)}>
            {CORRECTION_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Corrected clock-in</Label>
            <Input
              type="datetime-local"
              value={requestedClockIn}
              onChange={(e) => setRequestedClockIn(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Corrected clock-out</Label>
            <Input
              type="datetime-local"
              value={requestedClockOut}
              onChange={(e) => setRequestedClockOut(e.target.value)}
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Reason</Label>
          <Textarea
            required
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="e.g. Forgot to clock out, left early for an appointment…"
          />
        </div>

        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={resetAndClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Submit request
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function AttendanceHistory({ isAdmin }: { isAdmin: boolean }) {
  const [page, setPage] = useState(1);
  const [dateFrom, setDateFrom] = useState(todayIso());
  const [dateTo, setDateTo] = useState(todayIso());
  const [employeeSearch, setEmployeeSearch] = useState("");
  const [correctionTarget, setCorrectionTarget] = useState<AttendancePublic | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["attendance", "mine", "history", page, dateFrom, dateTo],
    queryFn: () =>
      attendanceApi.listAttendance({ page, page_size: 10, date_from: dateFrom, date_to: dateTo }),
  });

  const visibleItems = data
    ? data.items.filter((a) => {
        if (!isAdmin || !employeeSearch) return true;
        const q = employeeSearch.toLowerCase();
        return (
          a.employee_name.toLowerCase().includes(q) || a.employee_code.toLowerCase().includes(q)
        );
      })
    : [];

  return (
    <Card>
      <CardContent className="flex flex-wrap items-end gap-3 border-b border-ink-800 pb-4">
        <div className="flex flex-col gap-1.5">
          <Label>Start Date</Label>
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setDateFrom(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>End Date</Label>
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setDateTo(e.target.value);
              setPage(1);
            }}
          />
        </div>
        {isAdmin && (
          <div className="flex flex-col gap-1.5">
            <Label>Employee</Label>
            <Input
              value={employeeSearch}
              onChange={(e) => setEmployeeSearch(e.target.value)}
              placeholder="Search name or code…"
              className="w-48"
            />
          </div>
        )}
      </CardContent>

      <CardContent>
        {isLoading ? (
          <p className="text-sm text-ink-500">Loading…</p>
        ) : !data || visibleItems.length === 0 ? (
          <p className="text-sm text-ink-500">No attendance records in this range.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-ink-800 text-[12px] uppercase tracking-wide text-ink-500">
                  {isAdmin && <th className="pb-2 font-medium">Employee</th>}
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Clock In</th>
                  <th className="pb-2 font-medium">Clock Out</th>
                  <th className="pb-2 font-medium">Total Hours</th>
                  <th className="pb-2 font-medium">Status</th>
                  <th className="pb-2 font-medium">Breaks</th>
                  <th className="pb-2 font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {visibleItems.map((a) => (
                  <tr key={a.id} className="border-b border-ink-800/60 last:border-0">
                    {isAdmin && (
                      <td className="py-2.5">
                        <div className="flex flex-col">
                          <span className="text-ink-100">{a.employee_name}</span>
                          <span className="text-[12px] text-ink-500">{a.employee_code}</span>
                        </div>
                      </td>
                    )}
                    <td className="py-2.5 text-ink-200">{formatDate(a.attendance_date)}</td>
                    <td className="py-2.5 text-ink-300">{formatTime(a.clock_in)}</td>
                    <td className="py-2.5 text-ink-300">{formatTime(a.clock_out)}</td>
                    <td className="py-2.5 text-ink-300">{formatMinutes(a.total_working_minutes)}</td>
                    <td className="py-2.5">
                      <div className="flex gap-1.5">
                        <Badge variant={statusVariant(a.status)}>{statusLabel(a.status)}</Badge>
                        {a.is_late && <Badge variant="warning">Late</Badge>}
                      </div>
                    </td>
                    <td className="py-2.5 text-ink-400">{a.breaks.length}</td>
                    <td className="py-2.5 text-right">
                      {!isAdmin && (
                        <button
                          onClick={() => setCorrectionTarget(a)}
                          className="text-[13px] font-medium text-amber-glow hover:underline"
                        >
                          Request fix
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-4 flex items-center justify-between text-[13px] text-ink-500">
              <span>
                Page {data.page} of {Math.max(1, Math.ceil(data.total / data.page_size))}
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={page * data.page_size >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>

      <CorrectionDialog attendance={correctionTarget} onClose={() => setCorrectionTarget(null)} />
    </Card>
  );
}

function PendingCorrections() {
  const queryClient = useQueryClient();
  const [remarksById, setRemarksById] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ["corrections", "pending"],
    queryFn: attendanceApi.listPendingCorrections,
  });

  const decideMutation = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) =>
      attendanceApi.decideCorrection(id, approve, remarksById[id]),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["corrections"] });
      queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
  });

  if (isLoading || !data || data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pending Correction Requests</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="flex flex-col gap-3">
          {data.map((c) => (
            <li
              key={c.id}
              className="flex flex-col gap-2 rounded-lg border border-ink-700 bg-ink-800/40 p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm text-ink-200">{c.reason}</p>
                {c.requested_status && (
                  <p className="mt-0.5 text-[12px] text-ink-500">
                    Requested status: {statusLabel(c.requested_status)}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <input
                  placeholder="Remarks (optional)"
                  value={remarksById[c.id] ?? ""}
                  onChange={(e) =>
                    setRemarksById((prev) => ({ ...prev, [c.id]: e.target.value }))
                  }
                  className="h-8 w-40 rounded-md border border-ink-600 bg-ink-900/60 px-2 text-[13px] text-ink-100 outline-none focus:border-amber-glow/60"
                />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => decideMutation.mutate({ id: c.id, approve: true })}
                >
                  <Check className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => decideMutation.mutate({ id: c.id, approve: false })}
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

export default function Attendance() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[15px] text-ink-400">Track your daily attendance and breaks</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => queryClient.invalidateQueries({ queryKey: ["attendance"] })}
        >
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>

      {!isAdmin && <ClockControls />}
      {isAdmin && <PendingCorrections />}
      <AttendanceHistory isAdmin={isAdmin} />
    </div>
  );
}
