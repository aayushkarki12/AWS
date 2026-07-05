import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, ArrowRight, Fingerprint } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { getApiErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password, remember_me: rememberMe });
      navigate("/");
    } catch (err) {
      setError(getApiErrorMessage(err, "Invalid email or password"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-ink-950">
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden p-12 lg:flex">
        <div
          className="pointer-events-none absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full opacity-20 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, var(--color-amber-glow) 0%, transparent 70%)",
          }}
        />
        <div
          className="pointer-events-none absolute bottom-[-10rem] right-[-6rem] h-[28rem] w-[28rem] rounded-full opacity-10 blur-3xl"
          style={{
            background: "radial-gradient(circle, var(--color-teal-glow) 0%, transparent 70%)",
          }}
        />

        <div className="relative z-10 flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-glow/10 border border-amber-glow/30">
            <Fingerprint className="h-5 w-5 text-amber-glow" strokeWidth={1.75} />
          </div>
          <span className="text-[15px] font-medium tracking-tight text-ink-100">Meridian</span>
        </div>

        <div className="relative z-10 max-w-md">
          <h1 className="font-display text-[2.75rem] leading-[1.1] text-ink-50">
            Attendance, without the guesswork.
          </h1>
          <p className="mt-5 text-[15px] leading-relaxed text-ink-300">
            Shift-aware clock-ins, correction workflows, and live workforce
            analytics — built for teams that take operations seriously.
          </p>
        </div>

        <p className="relative z-10 text-[13px] text-ink-500">
          © {new Date().getFullYear()} Meridian Workforce
        </p>
      </div>

      <div className="flex w-full flex-col justify-center px-8 sm:px-16 lg:w-1/2 lg:px-20">
        <div className="mx-auto w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-glow/10 border border-amber-glow/30">
                <Fingerprint className="h-5 w-5 text-amber-glow" strokeWidth={1.75} />
              </div>
              <span className="text-[15px] font-medium tracking-tight text-ink-100">
                Meridian
              </span>
            </div>
          </div>

          <h2 className="text-2xl font-semibold tracking-tight text-ink-50">Welcome back</h2>
          <p className="mt-1.5 text-sm text-ink-400">Sign in to your workspace to continue.</p>

          <form className="mt-8 flex flex-col gap-5" onSubmit={handleSubmit}>
            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-coral-deep/30 bg-coral-deep/10 px-3 py-2.5 text-[13px] text-coral-glow">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  to="/forgot-password"
                  className="text-[13px] text-ink-400 hover:text-amber-glow transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>

            <label className="flex items-center gap-2 text-[13px] text-ink-400">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-3.5 w-3.5 rounded border-ink-600 bg-ink-900 accent-amber-glow"
              />
              Remember me for 30 days
            </label>

            <Button type="submit" size="lg" disabled={isSubmitting} className="mt-1 group">
              {isSubmitting ? "Signing in…" : "Sign in"}
              {!isSubmitting && (
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              )}
            </Button>
          </form>

          <p className="mt-8 text-center text-sm text-ink-400">
            Don&apos;t have an account?{" "}
            <Link to="/register" className="font-medium text-amber-glow hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
