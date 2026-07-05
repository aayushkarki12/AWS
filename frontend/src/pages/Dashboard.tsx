import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlarmClockOff,
  Building2,
  CheckCircle2,
  Clock3,
  Coffee,
  FileWarning,
  Percent,
  TrendingUp,
  UserCheck,
  UserX,
  Users,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import {
  fetchAdminDashboard,
  fetchAdminTrend,
  fetchBreakAnalysis,
  fetchEmployeeDashboard,
  fetchLeaderboard,
  fetchMyBreakAnalysis,
  fetchMyTrend,
} from "@/api/dashboard";
import { listEmployees } from "@/api/employees";
import { Card, CardContent, CardHeader, CardTitle, CardValue } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatMinutes, statusLabel } from "@/utils/format";
import type { AdminDashboard } from "@/types/dashboard";

function StatCard({
  label,
  value,
  icon: Icon,
  accent = "amber",
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
  accent?: "amber" | "teal" | "coral" | "neutral";
}) {
  const accentClasses = {
    amber: "text-amber-glow bg-amber-glow/10 border-amber-glow/20",
    teal: "text-teal-glow bg-teal-deep/10 border-teal-deep/20",
    coral: "text-coral-glow bg-coral-deep/10 border-coral-deep/20",
    neutral: "text-ink-300 bg-ink-800 border-ink-600",
  }[accent];

  return (
    <Card>
      <div className="flex items-start justify-between p-5">
        <div className="flex flex-col gap-2">
          <CardTitle>{label}</CardTitle>
          <CardValue>{value}</CardValue>
        </div>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg border ${accentClasses}`}>
          <Icon className="h-4.5 w-4.5" strokeWidth={1.75} />
        </div>
      </div>
    </Card>
  );
}

function last14DaysRange(): { dateFrom: string; dateTo: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - 13);
  return { dateFrom: from.toISOString().slice(0, 10), dateTo: to.toISOString().slice(0, 10) };
}

function AttendanceTrendChart({ scope = "admin" }: { scope?: "admin" | "me" }) {
  const { dateFrom, dateTo } = last14DaysRange();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", scope, "trend", dateFrom, dateTo],
    queryFn: () => (scope === "me" ? fetchMyTrend(dateFrom, dateTo) : fetchAdminTrend(dateFrom, dateTo)),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {scope === "me" ? "My Attendance (Last 14 Days)" : "Attendance Trend (Last 14 Days)"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || !data || data.length === 0 ? (
          <p className="text-sm text-ink-500">Not enough data yet.</p>
        ) : (
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="presentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-amber-glow)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--color-amber-glow)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-ink-800)" />
                <XAxis
                  dataKey="attendance_date"
                  tick={{ fill: "var(--color-ink-500)", fontSize: 11 }}
                  tickFormatter={(v: string) => v.slice(5)}
                  axisLine={{ stroke: "var(--color-ink-700)" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "var(--color-ink-500)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-ink-900)",
                    border: "1px solid var(--color-ink-700)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: "var(--color-ink-200)" }}
                />
                <Area
                  type="monotone"
                  dataKey="present_count"
                  name="Present"
                  stroke="var(--color-amber-glow)"
                  fill="url(#presentGradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function BreakAnalysisCard({ scope = "admin" }: { scope?: "admin" | "me" }) {
  const { dateFrom, dateTo } = last14DaysRange();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", scope, "break-analysis", dateFrom, dateTo],
    queryFn: () =>
      scope === "me" ? fetchMyBreakAnalysis(dateFrom, dateTo) : fetchBreakAnalysis(dateFrom, dateTo),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {scope === "me" ? "My Breaks (Last 14 Days)" : "Break Analysis (Last 14 Days)"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || !data || data.by_type.length === 0 ? (
          <p className="text-sm text-ink-500">No breaks recorded in this period.</p>
        ) : (
          <div className="flex flex-col gap-3">
            <div className="flex gap-6 text-[13px] text-ink-400">
              <span>
                Total: <span className="text-ink-100">{data.total_breaks}</span>
              </span>
              <span>
                Avg duration: <span className="text-ink-100">{data.average_minutes}m</span>
              </span>
            </div>
            <div className="flex flex-col gap-2.5">
              {data.by_type.map((b) => {
                const pct = data.total_breaks ? Math.round((b.count / data.total_breaks) * 100) : 0;
                return (
                  <div key={b.break_type} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-[13px]">
                      <span className="text-ink-200">{statusLabel(b.break_type)}</span>
                      <span className="text-ink-500">
                        {b.count} · avg {b.average_minutes}m
                      </span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-800">
                      <div
                        className="h-full rounded-full bg-amber-glow transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

const MEDALS = ["🥇", "🥈", "🥉"];
const BADGE_ICON: Record<string, string> = {
  "Never Late": "⭐",
  "Perfect Week": "💪",
  "Early Bird": "🌅",
};

function LeaderboardCard() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "admin", "leaderboard"],
    queryFn: () => fetchLeaderboard(30, 5),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>🏆 Attendance Leaderboard</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || !data || data.length === 0 ? (
          <p className="text-sm text-ink-500">Not enough attendance history yet.</p>
        ) : (
          <ul className="flex flex-col gap-2.5">
            {data.map((entry, i) => (
              <li
                key={entry.employee_id}
                className="flex items-center justify-between gap-3 rounded-lg border border-ink-800 bg-ink-800/30 px-3 py-2.5"
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <span className="text-lg leading-none">{MEDALS[i] ?? `#${i + 1}`}</span>
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-medium text-ink-100">
                      {entry.employee_name}
                    </p>
                    <p className="text-[11px] text-ink-500">
                      {entry.present_days} days present
                      {entry.current_streak > 1 && ` · 🔥 ${entry.current_streak}x streak`}
                    </p>
                  </div>
                </div>
                {entry.badges.length > 0 && (
                  <div className="flex shrink-0 gap-1">
                    {entry.badges.map((b) => (
                      <span key={b} title={b} className="text-sm">
                        {BADGE_ICON[b] ?? "🎖️"}
                      </span>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-[11px] text-ink-600">
          🎖️ Badges: Early Bird, Perfect Week, Never Late — based on the last 30 days.
        </p>
      </CardContent>
    </Card>
  );
}

const DONUT_COLORS = [
  "var(--color-teal-glow)",
  "var(--color-coral-glow)",
  "var(--color-amber-glow)",
  "var(--color-ink-500)",
];

function AttendanceStatusDonut({ data }: { data: AdminDashboard }) {
  const segments = [
    { name: "Present", value: data.present_count },
    { name: "Absent", value: data.absent_count },
    { name: "On Leave", value: data.on_leave_count },
    { name: "Late", value: data.late_count },
  ].filter((s) => s.value > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Today's Attendance Status</CardTitle>
      </CardHeader>
      <CardContent>
        {segments.length === 0 ? (
          <p className="text-sm text-ink-500">No attendance recorded yet today.</p>
        ) : (
          <div className="flex items-center gap-6">
            <div className="h-44 w-44 shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={segments}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={50}
                    outerRadius={78}
                    paddingAngle={2}
                    strokeWidth={0}
                  >
                    {segments.map((s, i) => (
                      <Cell key={s.name} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--color-ink-900)",
                      border: "1px solid var(--color-ink-700)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <ul className="flex flex-col gap-2 text-[13px]">
              {segments.map((s, i) => (
                <li key={s.name} className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ background: DONUT_COLORS[i % DONUT_COLORS.length] }}
                  />
                  <span className="text-ink-300">{s.name}</span>
                  <span className="ml-auto font-medium text-ink-100">{s.value}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function EmployeesByDepartmentChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["employees", "by-department"],
    queryFn: () => listEmployees({ page: 1, page_size: 100 }),
  });

  const counts = new Map<string, number>();
  for (const emp of data?.items ?? []) {
    const key = emp.department_name ?? "Unassigned";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const chartData = Array.from(counts.entries())
    .map(([department, count]) => ({ department, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Employees by Department</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || chartData.length === 0 ? (
          <p className="text-sm text-ink-500">No department data yet.</p>
        ) : (
          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-ink-800)" horizontal={false} />
                <XAxis
                  type="number"
                  allowDecimals={false}
                  tick={{ fill: "var(--color-ink-500)", fontSize: 11 }}
                  axisLine={{ stroke: "var(--color-ink-700)" }}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="department"
                  width={90}
                  tick={{ fill: "var(--color-ink-300)", fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  cursor={{ fill: "var(--color-ink-800)" }}
                  contentStyle={{
                    background: "var(--color-ink-900)",
                    border: "1px solid var(--color-ink-700)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" fill="var(--color-amber-glow)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function AdminOverview() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "admin"],
    queryFn: fetchAdminDashboard,
  });

  if (isLoading || !data) {
    return <DashboardSkeleton />;
  }

  const avgHours = (data.average_working_minutes / 60).toFixed(1);

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
        <StatCard label="Total Employees" value={data.total_employees} icon={Users} accent="neutral" />
        <StatCard label="Present Today" value={data.present_count} icon={UserCheck} accent="teal" />
        <StatCard label="Absent Today" value={data.absent_count} icon={UserX} accent="coral" />
        <StatCard label="Late Arrivals" value={data.late_count} icon={AlarmClockOff} accent="amber" />
        <StatCard label="On Leave" value={data.on_leave_count} icon={Building2} accent="neutral" />
        <StatCard label="Working Now" value={data.working_now_count} icon={Clock3} accent="teal" />
        <StatCard label="On Break" value={data.on_break_count} icon={Coffee} accent="amber" />
        <StatCard label="Avg. Hours / Day" value={`${avgHours}h`} icon={TrendingUp} accent="neutral" />
        <StatCard
          label="Attendance Rate"
          value={`${data.attendance_rate}%`}
          icon={Percent}
          accent="teal"
        />
        <StatCard
          label="On-Time Rate"
          value={`${data.on_time_rate}%`}
          icon={CheckCircle2}
          accent="teal"
        />
        <StatCard
          label="Pending Corrections"
          value={data.pending_corrections_count}
          icon={FileWarning}
          accent={data.pending_corrections_count > 0 ? "amber" : "neutral"}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AttendanceStatusDonut data={data} />
        <EmployeesByDepartmentChart />
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AttendanceTrendChart />
        <BreakAnalysisCard />
      </div>

      <LeaderboardCard />
    </div>
  );
}

function EmployeeOverview() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "me"],
    queryFn: fetchEmployeeDashboard,
  });

  if (isLoading || !data) {
    return <DashboardSkeleton />;
  }

  const today = data.today_attendance;
  const workedHours = today?.total_working_minutes
    ? (today.total_working_minutes / 60).toFixed(1)
    : "—";

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Today's Status</CardTitle>
          </CardHeader>
          <CardContent>
            {today ? (
              <div className="flex items-center gap-3">
                <Badge variant={today.status === "present" ? "success" : "neutral"}>
                  {today.status.replace("_", " ")}
                </Badge>
                {today.is_late && <Badge variant="warning">Late</Badge>}
              </div>
            ) : (
              <p className="text-sm text-ink-500">Not clocked in yet</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Hours Worked Today</CardTitle>
          </CardHeader>
          <CardContent>
            <CardValue>{workedHours}h</CardValue>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Present Days (This Month)</CardTitle>
          </CardHeader>
          <CardContent>
            <CardValue>{data.monthly_present_days}</CardValue>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Monthly Working Hours</CardTitle>
        </CardHeader>
        <CardContent>
          <CardValue>{formatMinutes(data.monthly_total_working_minutes)}</CardValue>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <AttendanceTrendChart scope="me" />
        <BreakAnalysisCard scope="me" />
      </div>

      <LeaderboardCard />

      <Card>
        <CardHeader>
          <CardTitle>Upcoming Holidays</CardTitle>
        </CardHeader>
        <CardContent>
          {data.upcoming_holidays.length === 0 ? (
            <p className="text-sm text-ink-500">No upcoming holidays scheduled.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {data.upcoming_holidays.map((h) => (
                <li key={h.id} className="flex items-center justify-between text-sm">
                  <span className="text-ink-200">{h.name}</span>
                  <span className="text-ink-500">{h.holiday_date}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-24 animate-pulse rounded-xl border border-ink-700 bg-ink-900/50" />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  return (
    <div>
      <p className="mb-6 text-sm text-ink-400">
        Welcome back{user ? `, ${user.email.split("@")[0]}` : ""} — here's what's happening.
      </p>
      {isAdmin ? <AdminOverview /> : <EmployeeOverview />}
    </div>
  );
}
