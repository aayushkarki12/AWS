import { Outlet, useLocation } from "react-router-dom";

import { Navbar } from "@/components/common/Navbar";
import { Sidebar } from "@/components/common/Sidebar";
import { useAttendanceShortcuts } from "@/hooks/useAttendanceShortcuts";

const TITLES: Record<string, string> = {
  "/": "Overview",
  "/attendance": "Attendance",
  "/employees": "Employees",
  "/shifts": "Shift Management",
  "/holidays": "Holiday Calendar",
  "/reports": "Reports",
  "/profile": "My Profile",
};

export function DashboardLayout() {
  const location = useLocation();
  const title = TITLES[location.pathname] ?? "Meridian";
  useAttendanceShortcuts();

  return (
    <div className="flex h-screen bg-ink-950">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar title={title} />
        <main className="flex-1 overflow-y-auto px-6 py-6">
          <div key={location.pathname} className="animate-slide-up">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
