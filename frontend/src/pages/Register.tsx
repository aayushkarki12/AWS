import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Fingerprint } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import { getApiErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ email, password, first_name: firstName, last_name: lastName });
      navigate("/");
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not create your account"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-950 px-6 py-12">
      <div
        className="pointer-events-none fixed left-1/2 top-0 h-[36rem] w-[36rem] -translate-x-1/2 rounded-full opacity-10 blur-3xl"
        style={{
          background: "radial-gradient(circle, var(--color-amber-glow) 0%, transparent 70%)",
        }}
      />

      <div className="relative z-10 w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-glow/10 border border-amber-glow/30">
            <Fingerprint className="h-5 w-5 text-amber-glow" strokeWidth={1.75} />
          </div>
          <span className="text-[15px] font-medium tracking-tight text-ink-100">Meridian</span>
        </div>

        <div className="rounded-xl border border-ink-700 bg-ink-900/70 p-8 shadow-panel">
          <h2 className="text-center text-2xl font-semibold tracking-tight text-ink-50">
            Create your account
          </h2>
          <p className="mt-1.5 text-center text-sm text-ink-400">
            Get started with your workforce dashboard.
          </p>

          <form className="mt-7 flex flex-col gap-5" onSubmit={handleSubmit}>
            {error && (
              <div className="flex items-start gap-2 rounded-lg border border-coral-deep/30 bg-coral-deep/10 px-3 py-2.5 text-[13px] text-coral-glow">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="firstName">First name</Label>
                <Input
                  id="firstName"
                  required
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Jane"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="lastName">Last name</Label>
                <Input
                  id="lastName"
                  required
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Doe"
                />
              </div>
            </div>

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
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 8 characters"
              />
              <p className="text-[12px] text-ink-500">
                Use upper &amp; lowercase letters, a number, and a symbol.
              </p>
            </div>

            <Button type="submit" size="lg" disabled={isSubmitting} className="mt-1">
              {isSubmitting ? "Creating account…" : "Create account"}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-ink-400">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-amber-glow hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
