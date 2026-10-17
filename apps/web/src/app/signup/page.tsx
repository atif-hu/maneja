"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { BotanicalArt } from "@/components/BotanicalArt";
import { createClient } from "@/lib/supabase/client";
import "../auth.css";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!agreed) {
      setError("Please agree to the Terms and Privacy Policy.");
      return;
    }
    setLoading(true);
    setError(null);
    const supabase = createClient();
    const { error: err } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName } },
    });
    setLoading(false);
    if (err) {
      setError(err.message);
      return;
    }
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
        <section className="auth-panel auth-panel--signup">
          <Link href="/login" className="auth-mark">
            <Image src="/logo.png" alt="Maneja" width={34} height={34} className="rounded-lg" />
            <span className="bg-gradient-to-r from-[#E8798F] to-[#A855A0] bg-clip-text text-xl font-bold tracking-tight text-transparent">
              Maneja
            </span>
          </Link>

          <div className="auth-form-wrap">
            <form className="auth-form auth-form--signup" onSubmit={onSubmit}>
              <div className="auth-heading auth-heading--center">
                <h1>Create your Maneja account</h1>
                <p>A more considered way to create.</p>
              </div>

              <button type="button" className="auth-btn auth-btn--google" onClick={onGoogle}>
                <span className="g-mark">G</span>
                Continue with Google
              </button>

              <div className="auth-divider">
                <span>or sign up with email</span>
              </div>

              <div className="auth-fields">
                <div className="auth-field">
                  <label htmlFor="full-name">Full name</label>
                  <input
                    id="full-name"
                    type="text"
                    required
                    placeholder="Your name"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    autoComplete="name"
                  />
                </div>

                <div className="auth-field">
                  <label htmlFor="email">Work email</label>
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
                    minLength={6}
                    placeholder="Create a password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="new-password"
                  />
                </div>
              </div>

              <label className="auth-check auth-check--terms">
                <input
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                />
                <span>I agree to the Terms and Privacy Policy</span>
              </label>

              {error ? <p className="auth-error">{error}</p> : null}

              <button className="auth-btn auth-btn--primary" type="submit" disabled={loading}>
                {loading ? "Creating…" : "Create account"}
              </button>

              <p className="auth-footer">
                Already have an account?
                <Link href="/login">Sign in</Link>
              </p>
            </form>
          </div>
        </section>

        <section className="auth-aside">
          <div className="auth-aside__lines">
            <BotanicalArt variant="signup" />
          </div>
          <div className="auth-aside__center">
            <span className="brand">Maneja</span>
            <span className="tag">create with intention</span>
          </div>
        </section>
      </div>
    </div>
  );
}
