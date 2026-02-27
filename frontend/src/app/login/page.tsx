"use client";

import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [isSignup, setIsSignup] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = isSignup ? "/api/auth/signup" : "/api/auth/login";
      const body = isSignup
        ? { name, email, password }
        : { email, password };

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Something went wrong");
        return;
      }

      const data = await res.json();
      if (!data.onboarding_completed) {
        window.location.href = "/onboarding";
      } else {
        window.location.href = "/";
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE}/api/auth/google`;
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#F7F7F4]">
      {/* Animated background orbs */}
      <div className="pointer-events-none absolute inset-0">
        <div
          className="absolute -top-32 -left-32 h-[420px] w-[420px] rounded-full opacity-[0.07]"
          style={{
            background: "radial-gradient(circle, #f97316 0%, transparent 70%)",
            animation: "orb-drift 20s ease-in-out infinite",
          }}
        />
        <div
          className="absolute -right-24 top-1/4 h-[360px] w-[360px] rounded-full opacity-[0.05]"
          style={{
            background: "radial-gradient(circle, #1a1a1a 0%, transparent 70%)",
            animation: "orb-drift 25s ease-in-out infinite reverse",
          }}
        />
        <div
          className="absolute -bottom-24 left-1/3 h-[300px] w-[300px] rounded-full opacity-[0.04]"
          style={{
            background: "radial-gradient(circle, #f97316 0%, transparent 70%)",
            animation: "orb-drift 18s ease-in-out infinite 3s",
          }}
        />
      </div>

      {/* Content */}
      <div className="relative z-10 w-full max-w-sm px-6">
        {/* Brand */}
        <div className="mb-10 text-center">
          <div
            className="mb-4 inline-flex"
            style={{ animation: "logo-pop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) both" }}
          >
            <img src="/logo.svg" alt="WINGMAN" className="h-14 w-auto" />
          </div>
          <div className="overflow-hidden">
            <h1
              className="text-3xl font-bold tracking-tight text-[#1a1a1a]"
              style={{ animation: "letter-slide 0.5s cubic-bezier(0.16, 1, 0.3, 1) 0.3s both" }}
            >
              WINGMAN
            </h1>
          </div>
          <p
            className="mt-2 text-[13px] text-gray-400"
            style={{ animation: "fade-in 0.6s ease 0.5s both" }}
          >
            Your autonomous networking agent
          </p>
        </div>

        {/* Card */}
        <div
          className="rounded-2xl border border-black/[0.04] bg-white/80 p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] backdrop-blur-xl"
          style={{ animation: "fade-in-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.4s both" }}
        >
          {/* Google button first — primary CTA */}
          <button
            onClick={handleGoogleLogin}
            className="mb-5 inline-flex w-full items-center justify-center gap-3 rounded-xl bg-white px-6 py-3.5 text-[14px] font-medium text-gray-800 shadow-[0_1px_4px_rgba(0,0,0,0.08)] transition-all duration-200 hover:shadow-[0_4px_16px_rgba(0,0,0,0.1)] hover:-translate-y-0.5 active:scale-[0.98]"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            Continue with Google
          </button>

          <div className="mb-5 flex items-center gap-3">
            <div className="h-px flex-1 bg-black/[0.06]" />
            <span className="text-[11px] text-gray-300">or</span>
            <div className="h-px flex-1 bg-black/[0.06]" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-3">
            {isSignup && (
              <input
                type="text"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full rounded-xl border border-black/[0.06] bg-[#F7F7F4]/60 px-4 py-3 text-[14px] text-gray-900 placeholder-gray-400 transition-all duration-200 focus:border-black/15 focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/[0.04]"
              />
            )}
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-black/[0.06] bg-[#F7F7F4]/60 px-4 py-3 text-[14px] text-gray-900 placeholder-gray-400 transition-all duration-200 focus:border-black/15 focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/[0.04]"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full rounded-xl border border-black/[0.06] bg-[#F7F7F4]/60 px-4 py-3 text-[14px] text-gray-900 placeholder-gray-400 transition-all duration-200 focus:border-black/15 focus:bg-white focus:outline-none focus:ring-2 focus:ring-black/[0.04]"
            />

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 animate-fade-in">
                <svg className="h-3.5 w-3.5 shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-[12px] text-red-500">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#1a1a1a] px-4 py-3 text-[14px] font-medium text-white transition-all duration-200 hover:bg-[#333] hover:shadow-[0_4px_12px_rgba(0,0,0,0.15)] active:scale-[0.98] disabled:opacity-50"
            >
              {loading ? (
                <span className="inline-flex items-center gap-2">
                  <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Loading
                </span>
              ) : isSignup ? "Create account" : "Sign in"}
            </button>
          </form>
        </div>

        {/* Toggle */}
        <p
          className="mt-6 text-center text-[12px] text-gray-400"
          style={{ animation: "fade-in 0.6s ease 0.7s both" }}
        >
          {isSignup ? "Already have an account?" : "Don\u2019t have an account?"}{" "}
          <button
            onClick={() => {
              setIsSignup(!isSignup);
              setError("");
            }}
            className="font-medium text-gray-700 transition-colors hover:text-[#1a1a1a]"
          >
            {isSignup ? "Sign in" : "Create one"}
          </button>
        </p>
      </div>
    </div>
  );
}
