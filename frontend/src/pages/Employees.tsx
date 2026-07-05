import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search, UserMinus } from "lucide-react";

import * as departmentsApi from "@/api/departments";
import * as employeesApi from "@/api/employees";
import { getApiErrorMessage } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/toast";
import type { CreateEmployeePayload, EmployeePublic, UpdateEmployeePayload } from "@/types/employee";

const EMPLOYMENT_STATUSES = ["active", "on_leave", "suspended", "terminated"];

function CreateEmployeeDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [form, setForm] = useState<CreateEmployeePayload>({
    email: "",
    password: "",
    employee_code: "",
    first_name: "",
    last_name: "",
    role: "employee",
  });
  const [error, setError] = useState<string | null>(null);

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.listDepartments,
    enabled: open,
  });

  const mutation = useMutation({
    mutationFn: () => employeesApi.createEmployee(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees"] });
      showToast({ variant: "success", title: "Employee created" });
      onClose();
      setForm({
        email: "",
        password: "",
        employee_code: "",
        first_name: "",
        last_name: "",
        role: "employee",
      });
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Add employee">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
        className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto pr-1"
      >
        {error && <p className="text-[13px] text-coral-glow">{error}</p>}

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>First name</Label>
            <Input
              required
              value={form.first_name}
              onChange={(e) => setForm({ ...form, first_name: e.target.value })}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Last name</Label>
            <Input
              required
              value={form.last_name}
              onChange={(e) => setForm({ ...form, last_name: e.target.value })}
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Employee code</Label>
          <Input
            required
            value={form.employee_code}
            onChange={(e) => setForm({ ...form, employee_code: e.target.value })}
            placeholder="EMP001"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Email</Label>
          <Input
            type="email"
            required
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Temporary password</Label>
          <Input
            type="password"
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>Job title</Label>
            <Input
              value={form.job_title ?? ""}
              onChange={(e) => setForm({ ...form, job_title: e.target.value })}
              placeholder="e.g. Software Engineer"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Date of joining</Label>
            <Input
              type="date"
              value={form.date_of_joining ?? ""}
              onChange={(e) => setForm({ ...form, date_of_joining: e.target.value })}
            />
          </div>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Department</Label>
          <Select
            value={form.department_id ?? ""}
            onChange={(e) => setForm({ ...form, department_id: e.target.value || undefined })}
          >
            <option value="">No department</option>
            {departments?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Role</Label>
          <Select
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value as "employee" | "admin" })}
          >
            <option value="employee">Employee</option>
            <option value="admin">Admin</option>
          </Select>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Create employee
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

function EditEmployeeDialog({
  employee,
  allEmployees,
  onClose,
}: {
  employee: EmployeePublic | null;
  allEmployees: EmployeePublic[];
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [form, setForm] = useState<UpdateEmployeePayload>({});
  const [error, setError] = useState<string | null>(null);

  const { data: departments } = useQuery({
    queryKey: ["departments"],
    queryFn: departmentsApi.listDepartments,
    enabled: Boolean(employee),
  });

  useEffect(() => {
    if (!employee) return;
    setForm({
      job_title: employee.job_title ?? undefined,
      date_of_joining: employee.date_of_joining ?? undefined,
      department_id: employee.department_id ?? undefined,
      manager_id: employee.manager_id ?? undefined,
      employment_status: employee.employment_status,
    });
  }, [employee]);

  const mutation = useMutation({
    mutationFn: () => employeesApi.updateEmployee(employee!.id, form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees"] });
      showToast({ variant: "success", title: "Employee updated" });
      onClose();
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  const managerOptions = allEmployees.filter((e) => e.id !== employee?.id);

  return (
    <Dialog
      open={Boolean(employee)}
      onClose={onClose}
      title={employee ? `Edit ${employee.first_name} ${employee.last_name}` : "Edit employee"}
    >
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
          <Label>Job title</Label>
          <Input
            value={form.job_title ?? ""}
            onChange={(e) => setForm({ ...form, job_title: e.target.value })}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Date of joining</Label>
          <Input
            type="date"
            value={form.date_of_joining ?? ""}
            onChange={(e) => setForm({ ...form, date_of_joining: e.target.value })}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Department</Label>
          <Select
            value={form.department_id ?? ""}
            onChange={(e) => setForm({ ...form, department_id: e.target.value || undefined })}
          >
            <option value="">No department</option>
            {departments?.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Manager</Label>
          <Select
            value={form.manager_id ?? ""}
            onChange={(e) => setForm({ ...form, manager_id: e.target.value || undefined })}
          >
            <option value="">No manager</option>
            {managerOptions.map((m) => (
              <option key={m.id} value={m.id}>
                {m.first_name} {m.last_name} ({m.employee_code})
              </option>
            ))}
          </Select>
        </div>

        <div className="flex flex-col gap-1.5">
          <Label>Employment status</Label>
          <Select
            value={form.employment_status ?? "active"}
            onChange={(e) => setForm({ ...form, employment_status: e.target.value })}
          >
            {EMPLOYMENT_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </Select>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Save changes
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

export default function Employees() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<EmployeePublic | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["employees", page, search],
    queryFn: () => employeesApi.listEmployees({ page, page_size: 10, search: search || undefined }),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => employeesApi.deactivateEmployee(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["employees"] }),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-500" />
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search by name or code…"
            className="pl-9"
          />
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4" /> Add employee
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-5 text-sm text-ink-500">Loading…</p>
          ) : !data || data.items.length === 0 ? (
            <p className="p-5 text-sm text-ink-500">No employees found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-800 text-[12px] uppercase tracking-wide text-ink-500">
                    <th className="px-5 py-3 font-medium">Employee</th>
                    <th className="px-5 py-3 font-medium">Contact</th>
                    <th className="px-5 py-3 font-medium">Role</th>
                    <th className="px-5 py-3 font-medium">Department</th>
                    <th className="px-5 py-3 font-medium">Manager</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((emp) => (
                    <tr key={emp.id} className="border-b border-ink-800/60 last:border-0">
                      <td className="px-5 py-3">
                        <div className="flex flex-col">
                          <span className="text-ink-100">
                            {emp.first_name} {emp.last_name}
                          </span>
                          <span className="text-[12px] text-ink-500">
                            {emp.employee_code}
                            {emp.job_title ? ` · ${emp.job_title}` : ""}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex flex-col">
                          <span className="text-ink-300">{emp.email}</span>
                          {emp.phone && <span className="text-[12px] text-ink-500">{emp.phone}</span>}
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        <Badge variant={emp.role_name === "employee" ? "neutral" : "warning"}>
                          {emp.role_name.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-5 py-3 text-ink-300">
                        {emp.department_name ? (
                          <div className="flex flex-col">
                            <span>{emp.department_name}</span>
                            {emp.branch_name && (
                              <span className="text-[12px] text-ink-500">{emp.branch_name}</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-ink-500">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-ink-400">{emp.manager_name ?? "—"}</td>
                      <td className="px-5 py-3">
                        <div className="flex flex-col gap-1">
                          <Badge variant={emp.employment_status === "active" ? "success" : "neutral"}>
                            {emp.employment_status.replace("_", " ")}
                          </Badge>
                          {!emp.is_active && <Badge variant="danger">Login disabled</Badge>}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <div className="flex items-center justify-end gap-3">
                          <button
                            onClick={() => setEditTarget(emp)}
                            className="inline-flex items-center gap-1 text-[13px] text-amber-glow hover:underline"
                          >
                            <Pencil className="h-3.5 w-3.5" /> Edit
                          </button>
                          <button
                            onClick={() => deactivateMutation.mutate(emp.id)}
                            className="inline-flex items-center gap-1 text-[13px] text-ink-500 hover:text-coral-glow"
                          >
                            <UserMinus className="h-3.5 w-3.5" /> Deactivate
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex items-center justify-between px-5 py-3 text-[13px] text-ink-500">
                <span>
                  Page {data.page} of {Math.max(1, Math.ceil(data.total / data.page_size))} ·{" "}
                  {data.total} total
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
      </Card>

      <CreateEmployeeDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
      <EditEmployeeDialog
        employee={editTarget}
        allEmployees={data?.items ?? []}
        onClose={() => setEditTarget(null)}
      />
    </div>
  );
}
