import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Clock, Plus, UserPlus } from "lucide-react";

import * as employeesApi from "@/api/employees";
import * as shiftsApi from "@/api/shifts";
import { getApiErrorMessage } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import type { ShiftAssignmentCreatePayload, ShiftCreatePayload, ShiftType } from "@/types/shift";
import { formatDate, statusLabel } from "@/utils/format";

const SHIFT_TYPES: ShiftType[] = ["day", "night", "24_hours", "flexible", "split", "custom"];

const DEFAULT_SHIFT_FORM: ShiftCreatePayload = {
  name: "",
  shift_type: "day",
  start_time: "09:00",
  end_time: "17:00",
  crosses_midnight: false,
  grace_period_minutes: 10,
  max_break_minutes: 60,
  expected_working_minutes: 480,
};

function CreateShiftDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<ShiftCreatePayload>(DEFAULT_SHIFT_FORM);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => shiftsApi.createShift({ ...form, start_time: `${form.start_time}:00`, end_time: `${form.end_time}:00` }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shifts"] });
      setForm(DEFAULT_SHIFT_FORM);
      onClose();
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Create shift">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
        className="flex flex-col gap-4"
      >
        {error && <p className="text-[13px] text-coral-glow">{error}</p>}

        <div className="flex flex-col gap-1.5">
          <Label>Shift name</Label>
          <Input
            required
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Day Shift"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Shift type</Label>
          <Select
            value={form.shift_type}
            onChange={(e) => setForm({ ...form, shift_type: e.target.value as ShiftType })}
          >
            {SHIFT_TYPES.map((t) => (
              <option key={t} value={t}>
                {statusLabel(t)}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Start time</Label>
            <Input
              type="time"
              required
              value={form.start_time}
              onChange={(e) => setForm({ ...form, start_time: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>End time</Label>
            <Input
              type="time"
              required
              value={form.end_time}
              onChange={(e) => setForm({ ...form, end_time: e.target.value })}
            />
          </div>
        </div>

        <label className="flex items-center gap-2 text-[13px] text-ink-400">
          <input
            type="checkbox"
            checked={form.crosses_midnight}
            onChange={(e) => setForm({ ...form, crosses_midnight: e.target.checked })}
            className="h-3.5 w-3.5 rounded border-ink-600 bg-ink-900 accent-amber-glow"
          />
          Shift crosses midnight
        </label>

        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Grace (min)</Label>
            <Input
              type="number"
              min={0}
              value={form.grace_period_minutes}
              onChange={(e) =>
                setForm({ ...form, grace_period_minutes: Number(e.target.value) })
              }
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Max break (min)</Label>
            <Input
              type="number"
              min={0}
              value={form.max_break_minutes}
              onChange={(e) => setForm({ ...form, max_break_minutes: Number(e.target.value) })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Expected (min)</Label>
            <Input
              type="number"
              min={0}
              value={form.expected_working_minutes}
              onChange={(e) =>
                setForm({ ...form, expected_working_minutes: Number(e.target.value) })
              }
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Create shift
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function AssignShiftDialog({
  open,
  onClose,
  shiftId,
}: {
  open: boolean;
  onClose: () => void;
  shiftId: string | null;
}) {
  const queryClient = useQueryClient();
  const [employeeId, setEmployeeId] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState(new Date().toISOString().slice(0, 10));
  const [effectiveTo, setEffectiveTo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: employeesPage } = useQuery({
    queryKey: ["employees", "for-assignment"],
    queryFn: () => employeesApi.listEmployees({ page: 1, page_size: 100 }),
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () => {
      const payload: ShiftAssignmentCreatePayload = {
        employee_id: employeeId,
        shift_id: shiftId!,
        effective_from: effectiveFrom,
        effective_to: effectiveTo || undefined,
      };
      return shiftsApi.createShiftAssignment(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["shift-assignments"] });
      setEmployeeId("");
      setEffectiveTo("");
      onClose();
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Assign shift to employee">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
        className="flex flex-col gap-4"
      >
        {error && <p className="text-[13px] text-coral-glow">{error}</p>}

        <div className="flex flex-col gap-1.5">
          <Label>Employee</Label>
          <Select required value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}>
            <option value="" disabled>
              Select an employee…
            </option>
            {employeesPage?.items.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.first_name} {emp.last_name} ({emp.employee_code})
              </option>
            ))}
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Effective from</Label>
            <Input
              type="date"
              required
              value={effectiveFrom}
              onChange={(e) => setEffectiveFrom(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Effective to (optional)</Label>
            <Input
              type="date"
              value={effectiveTo}
              onChange={(e) => setEffectiveTo(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending || !employeeId}>
            Assign shift
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

export default function Shifts() {
  const [createShiftOpen, setCreateShiftOpen] = useState(false);
  const [assignTargetShiftId, setAssignTargetShiftId] = useState<string | null>(null);

  const { data: shifts, isLoading: shiftsLoading } = useQuery({
    queryKey: ["shifts"],
    queryFn: shiftsApi.listShifts,
  });

  const { data: assignments, isLoading: assignmentsLoading } = useQuery({
    queryKey: ["shift-assignments"],
    queryFn: shiftsApi.listShiftAssignments,
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-display text-xl text-ink-50">Shift Management</h2>
          <p className="text-[13px] text-ink-400">
            Define shifts and assign employees to them
          </p>
        </div>
        <Button onClick={() => setCreateShiftOpen(true)}>
          <Plus className="h-4 w-4" /> New shift
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {shiftsLoading ? (
          <p className="text-sm text-ink-500">Loading shifts…</p>
        ) : !shifts || shifts.length === 0 ? (
          <p className="text-sm text-ink-500">No shifts defined yet.</p>
        ) : (
          shifts.map((shift) => (
            <Card key={shift.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-ink-100">{shift.name}</CardTitle>
                  <Badge variant="neutral">{statusLabel(shift.shift_type)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div className="flex items-center gap-2 text-sm text-ink-300">
                  <Clock className="h-4 w-4 text-ink-500" />
                  {shift.start_time.slice(0, 5)} – {shift.end_time.slice(0, 5)}
                  {shift.crosses_midnight && (
                    <span className="text-[11px] text-ink-500">(next day)</span>
                  )}
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-500">
                  <span>Grace: {shift.grace_period_minutes}m</span>
                  <span>Max break: {shift.max_break_minutes}m</span>
                  <span>Expected: {(shift.expected_working_minutes / 60).toFixed(1)}h</span>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setAssignTargetShiftId(shift.id)}
                >
                  <UserPlus className="h-3.5 w-3.5" /> Assign employee
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Current Assignments</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {assignmentsLoading ? (
            <p className="p-5 text-sm text-ink-500">Loading…</p>
          ) : !assignments || assignments.length === 0 ? (
            <p className="p-5 text-sm text-ink-500">No shift assignments yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-800 text-[12px] uppercase tracking-wide text-ink-500">
                    <th className="px-5 py-3 font-medium">Employee</th>
                    <th className="px-5 py-3 font-medium">Shift</th>
                    <th className="px-5 py-3 font-medium">Effective From</th>
                    <th className="px-5 py-3 font-medium">Effective To</th>
                  </tr>
                </thead>
                <tbody>
                  {assignments.map((a) => (
                    <tr key={a.id} className="border-b border-ink-800/60 last:border-0">
                      <td className="px-5 py-3">
                        <div className="flex flex-col">
                          <span className="text-ink-100">{a.employee_name}</span>
                          <span className="text-[12px] text-ink-500">{a.employee_code}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3 text-ink-300">{a.shift_name}</td>
                      <td className="px-5 py-3 text-ink-300">{formatDate(a.effective_from)}</td>
                      <td className="px-5 py-3 text-ink-400">
                        {a.effective_to ? formatDate(a.effective_to) : "Ongoing"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <CreateShiftDialog open={createShiftOpen} onClose={() => setCreateShiftOpen(false)} />
      <AssignShiftDialog
        open={Boolean(assignTargetShiftId)}
        onClose={() => setAssignTargetShiftId(null)}
        shiftId={assignTargetShiftId}
      />
    </div>
  );
}
