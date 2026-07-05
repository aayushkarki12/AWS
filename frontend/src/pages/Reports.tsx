import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, Printer } from "lucide-react";

import * as reportsApi from "@/api/reports";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatMinutes } from "@/utils/format";

function firstOfMonthIso(): string {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1).toISOString().slice(0, 10);
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function Reports() {
  const [dateFrom, setDateFrom] = useState(firstOfMonthIso());
  const [dateTo, setDateTo] = useState(todayIso());

  const { data, isLoading } = useQuery({
    queryKey: ["reports", "attendance-summary", dateFrom, dateTo],
    queryFn: () => reportsApi.fetchAttendanceSummary(dateFrom, dateTo),
    enabled: Boolean(dateFrom && dateTo),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="hidden print:block">
        <h1 className="font-display text-xl text-ink-950">Attendance Summary Report</h1>
        <p className="text-sm text-ink-500">
          {dateFrom} to {dateTo}
        </p>
      </div>

      <Card className="print:hidden">
        <CardContent className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1.5">
            <Label>From</Label>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>To</Label>
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div className="ml-auto flex gap-2">
            <Button variant="secondary" onClick={() => window.print()}>
              <Printer className="h-4 w-4" /> Print / Export PDF
            </Button>
            <a href={reportsApi.attendanceSummaryExportUrl(dateFrom, dateTo)}>
              <Button variant="secondary">
                <Download className="h-4 w-4" /> Export CSV
              </Button>
            </a>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-5 text-sm text-ink-500">Loading…</p>
          ) : !data || data.length === 0 ? (
            <p className="p-5 text-sm text-ink-500">No attendance in this range.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-800 text-[12px] uppercase tracking-wide text-ink-500">
                    <th className="px-5 py-3 font-medium">Employee</th>
                    <th className="px-5 py-3 font-medium">Present</th>
                    <th className="px-5 py-3 font-medium">Absent</th>
                    <th className="px-5 py-3 font-medium">Late</th>
                    <th className="px-5 py-3 font-medium">Worked</th>
                    <th className="px-5 py-3 font-medium">Overtime</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((row) => (
                    <tr key={row.employee_id} className="border-b border-ink-800/60 last:border-0">
                      <td className="px-5 py-3 text-ink-100">
                        {row.full_name}
                        <span className="ml-2 text-[12px] text-ink-500">{row.employee_code}</span>
                      </td>
                      <td className="px-5 py-3 text-ink-300">{row.present_days}</td>
                      <td className="px-5 py-3 text-ink-300">{row.absent_days}</td>
                      <td className="px-5 py-3 text-ink-300">{row.late_days}</td>
                      <td className="px-5 py-3 text-ink-300">
                        {formatMinutes(row.total_working_minutes)}
                      </td>
                      <td className="px-5 py-3 text-ink-300">
                        {formatMinutes(row.total_overtime_minutes)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
