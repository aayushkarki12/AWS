import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, LogOut, Menu, Moon, Sun, User as UserIcon } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { useTheme } from "@/auth/ThemeContext";
import * as employeesApi from "@/api/employees";
import { resolveUploadUrl } from "@/api/client";
import { LiveClock } from "@/components/common/LiveClock";
import { NotificationsMenu } from "@/components/common/NotificationsMenu";
import { cn } from "@/utils/cn";

const ROLE_LABELS: Record<string, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  employee: "Employee",
};

export function Navbar({ title, onMenuClick }: { title: string; onMenuClick?: () => void }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const { data: profile } = useQuery({
    queryKey: ["employees", "me"],
    queryFn: employeesApi.fetchMyProfile,
    retry: false,
  });

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  const initials = user?.email?.slice(0, 2).toUpperCase() ?? "??";
  const avatarUrl = resolveUploadUrl(profile?.profile_picture_url);

  return (
    <header className="relative z-30 flex h-16 shrink-0 items-center justify-between border-b border-ink-800 bg-ink-950/80 px-6 backdrop-blur-sm print:hidden">
      <div className="flex items-center gap-2 sm:gap-4">
        <button
          type="button"
          onClick={onMenuClick}
          aria-label="Open menu"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-ink-400 hover:bg-ink-800 hover:text-ink-100 lg:hidden"
        >
          <Menu className="h-[18px] w-[18px]" strokeWidth={1.75} />
        </button>
        <h1 className="text-[15px] font-medium tracking-tight text-ink-100">{title}</h1>
        <LiveClock className="hidden items-baseline text-[13px] sm:flex" />
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle color theme"
          className="relative flex h-9 w-9 items-center justify-center rounded-lg text-ink-400 transition-colors hover:bg-ink-800 hover:text-ink-100"
        >
          {theme === "dark" ? (
            <Sun className="h-[18px] w-[18px]" strokeWidth={1.75} />
          ) : (
            <Moon className="h-[18px] w-[18px]" strokeWidth={1.75} />
          )}
        </button>

        <NotificationsMenu />

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2 rounded-lg py-1.5 pl-1.5 pr-2 text-left transition-colors hover:bg-ink-800"
          >
            <div className="flex h-7 w-7 items-center justify-center overflow-hidden rounded-full bg-amber-glow/15 text-[11px] font-semibold text-amber-glow">
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                initials
              )}
            </div>
            <div className="hidden flex-col sm:flex">
              <span className="text-[13px] leading-tight text-ink-100">{user?.email}</span>
              <span className="text-[11px] leading-tight text-ink-500">
                {user ? ROLE_LABELS[user.role] : ""}
              </span>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-ink-500" />
          </button>

          {menuOpen && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
              <div
                className={cn(
                  "absolute right-0 top-full z-20 mt-2 w-44 rounded-lg border border-ink-700",
                  "bg-ink-900 py-1 shadow-panel",
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    navigate("/profile");
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-ink-300 hover:bg-ink-800 hover:text-ink-100"
                >
                  <UserIcon className="h-3.5 w-3.5" />
                  My Profile
                </button>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-[13px] text-ink-300 hover:bg-ink-800 hover:text-coral-glow"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
