"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Sparkles } from "lucide-react";
import { BotanicalArt } from "@/components/BotanicalArt";
import { createClient } from "@/lib/supabase/client";
import "../auth.css";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { error: err } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (err) {
      setError(err.message);
      return;
    }
    void remember;
    router.push("/dashboard");
    router.refresh();
  }

  async function onGoogle() {
    setError(null);
    const supabase = createClient();
    const { error: err } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (err) setError(err.message);
  }

  return (
    <div className="auth-root">
      <div className="auth-layout">
        <section className="auth-panel">
          <Link href="/login" className="auth-mark">
            <Sparkles className="auth-mark__icon" />
            <span className="auth-mark__name">Maneja</span>
          </Link>

          <div className="auth-form-wrap">
            <form className="auth-form" onSubmit={onSubmit}>
              <div className="auth-heading">
                <h1>Welcome back to Maneja</h1>
                <p>Your content, considered.</p>
              </div>

              <button type="button" className="auth-btn auth-btn--google" onClick={onGoogle}>
                <span className="g-mark">G</span>
                Continue with Google
              </button>

              <div className="auth-divider">
                <span>or continue with email</span>
              </div>

              <div className="auth-fields">
                <div className="auth-field">
                  <label htmlFor="email">Email</label>
                  <input
                    id="email"
                    type="email"
                    required
                    placeholder="you@yourbrand.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="password">Password</label>
                  <input
                    id="password"
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                  />
                </div>

                <div className="auth-row">
                  <label className="auth-check">
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                    />
                    Remember me
                  </label>
                  <a href="#forgot-password" className="auth-link">
                    Forgot password?
                  </a>
                </div>

                {error ? <p className="auth-error">{error}</p> : null}

                <button className="auth-btn auth-btn--primary" type="submit" disabled={loading}>
                  {loading ? "Signing in…" : "Sign in"}
                </button>
              </div>
            </form>
          </div>

          <p className="auth-footer">
            New to Maneja?
            <Link href="/signup">Create an account</Link>
          </p>
        </section>

        <aside className="auth-aside">
          <div className="auth-aside__veil" />
          <div className="auth-aside__art">
            <BotanicalArt variant="login" />
          </div>
          <div className="auth-aside__caption">
            <span>A softer way forward.</span>
            <Sparkles className="auth-mark__icon" />
          </div>
        </aside>
      </div>
    </div>
  );
}
