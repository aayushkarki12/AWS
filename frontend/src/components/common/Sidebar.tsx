import { NavLink } from "react-router-dom";
import {
  CalendarClock,
  CalendarDays,
  Clock,
  FileBarChart,
  Fingerprint,
  LayoutDashboard,
  Users,
} from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { cn } from "@/utils/cn";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard, roles: ["employee", "admin", "super_admin"] },
  { to: "/attendance", label: "Attendance", icon: Clock, roles: ["employee", "admin", "super_admin"] },
  { to: "/employees", label: "Employees", icon: Users, roles: ["admin", "super_admin"] },
  { to: "/shifts", label: "Shifts", icon: CalendarClock, roles: ["admin", "super_admin"] },
  { to: "/holidays", label: "Holidays", icon: CalendarDays, roles: ["employee", "admin", "super_admin"] },
  { to: "/reports", label: "Reports", icon: FileBarChart, roles: ["admin", "super_admin"] },
];

export function Sidebar() {
  const { user } = useAuth();
  const role = user?.role ?? "employee";

  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-ink-800 bg-ink-900/60 px-3 py-5 print:hidden lg:flex">
      <div className="flex items-center gap-2.5 px-2 pb-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-glow/10 border border-amber-glow/30">
          <Fingerprint className="h-4.5 w-4.5 text-amber-glow" strokeWidth={1.75} />
        </div>
        <span className="text-[14px] font-medium tracking-tight text-ink-100">Meridian</span>
      </div>

      <nav className="flex flex-col gap-0.5">
        {NAV_ITEMS.filter((item) => item.roles.includes(role)).map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13.5px] font-medium transition-colors",
                isActive
                  ? "bg-amber-glow/10 text-amber-glow"
                  : "text-ink-400 hover:bg-ink-800 hover:text-ink-100",
              )
            }
          >
            <item.icon className="h-4 w-4" strokeWidth={1.75} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
